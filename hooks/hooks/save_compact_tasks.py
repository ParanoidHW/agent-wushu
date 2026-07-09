#!/usr/bin/env python3
"""Persist unresolved task and planning context before Codex compaction.

The hook is intentionally conservative: it records likely carry-forward items
from the hook payload or transcript, then appends a Markdown snapshot in the
current working directory. It does not claim perfect task completion analysis.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

DEFAULT_OUTPUT = "compact-task-state.md"
DEFAULT_STATE = ".compact-task-state.json"
MAX_TEXT_CHARS = 30000
MAX_ITEMS = 80
MAX_SECTION_LINES = 36

IGNORED_ROLES = {"system", "developer", "tool", "function"}
TEXT_KEYS = (
    "text",
    "content",
    "message",
    "markdown",
    "last_assistant_message",
    "lastAssistantMessage",
    "last_agent_message",
    "lastAgentMessage",
    "prompt",
    "user_prompt",
    "userPrompt",
    "input",
    "input_text",
    "inputText",
)
TRANSCRIPT_KEYS = (
    "transcript_path",
    "transcriptPath",
    "conversation_path",
    "conversationPath",
    "thread_path",
    "threadPath",
    "session_path",
    "sessionPath",
)
EVENT_KEYS = ("hook_event_name", "hookEventName", "event_name", "eventName", "event", "type")
TRIGGER_KEYS = ("trigger", "compact_trigger", "compactTrigger", "reason", "source")

OPEN_CHECKBOX_RE = re.compile(r"^\s*[-*+]\s+\[\s\]\s+(.+)")
STATUS_RE = re.compile(
    r"\b(pending|in[_ -]?progress|blocked|todo|fixme|next steps?|remaining|unresolved|open item)\b",
    re.I,
)
CN_STATUS_RE = re.compile(r"(待办|未完成|未落实|未解决|待验证|待确认|后续|下一步|还需|需要继续|阻塞|规划|计划|设计|目标)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
PLAN_HEADING_RE = re.compile(
    r"(plan|planning|design|architecture|goal|objective|todo|next steps?|open questions?|"
    r"计划|规划|设计|目标|待办|后续|下一步|未完成|未落实|问题|方案)",
    re.I,
)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    now = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    cwd = Path.cwd()
    raw = sys.stdin.read()

    payload, payload_note = load_payload(raw)
    event = first_text(payload, EVENT_KEYS) or "PreCompact"
    trigger = first_text(payload, TRIGGER_KEYS) or "unknown"
    transcript_path = find_transcript_path(payload, cwd)

    sources: list[TextSource] = []
    sources.extend(text_sources_from_payload(payload, "hook-payload"))
    if transcript_path:
        sources.extend(read_transcript_sources(transcript_path))
    elif isinstance(payload, str) and payload.strip():
        sources.append(TextSource("hook-stdin", "unknown", payload))

    extraction = extract_carry_forward_items(sources, max_items=args.max_items)
    snapshot = build_snapshot(
        now=now,
        cwd=cwd,
        event=event,
        trigger=trigger,
        payload_note=payload_note,
        transcript_path=transcript_path,
        extraction=extraction,
    )

    fingerprint = stable_hash(
        {
            "event": event,
            "trigger": trigger,
            "transcript_path": str(transcript_path) if transcript_path else "",
            "open_items": extraction.open_items,
            "plan_sections": extraction.plan_sections,
            "limitations": extraction.limitations,
        }
    )
    state_path = Path(args.state_file)
    state = load_state(state_path)
    if fingerprint in state.get("seen", []):
        if not args.quiet:
            print("compact task snapshot already recorded; nothing written.", file=sys.stderr)
        return 0

    if not args.dry_run:
        append_snapshot(Path(args.output), snapshot)
        update_state(state_path, state, fingerprint, now)

    if not args.quiet:
        action = "Would append" if args.dry_run else "Appended"
        print(f"{action} compact task snapshot to {args.output}.", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-o", "--output", default=DEFAULT_OUTPUT, help=f"Markdown output. Default: {DEFAULT_OUTPUT}")
    parser.add_argument(
        "--state-file",
        default=DEFAULT_STATE,
        help=f"JSON state file used to avoid duplicate snapshots. Default: {DEFAULT_STATE}",
    )
    parser.add_argument("--max-items", type=int, default=MAX_ITEMS, help=f"Maximum extracted items. Default: {MAX_ITEMS}")
    parser.add_argument("--dry-run", action="store_true", help="Parse and report without writing files.")
    parser.add_argument("--quiet", action="store_true", help="Suppress hook status output.")
    return parser


class TextSource:
    def __init__(self, label: str, role: str, text: str) -> None:
        self.label = label
        self.role = normalize_role(role)
        self.text = text.strip()[:MAX_TEXT_CHARS]


class Extraction:
    def __init__(self) -> None:
        self.open_items: list[str] = []
        self.plan_sections: list[tuple[str, str]] = []
        self.limitations: list[str] = []


def load_payload(raw: str) -> tuple[Any, str]:
    if not raw.strip():
        return {}, "hook stdin was empty"
    try:
        return json.loads(raw), "hook stdin parsed as JSON"
    except json.JSONDecodeError:
        return raw, "hook stdin was not JSON; treated as plain text"


def first_text(payload: Any, keys: tuple[str, ...]) -> str:
    if isinstance(payload, dict):
        for key in keys:
            value = payload.get(key)
            text = coerce_text(value)
            if text:
                return text[:200]
        nested = payload.get("event")
        if isinstance(nested, dict):
            return first_text(nested, keys)
    return ""


def find_transcript_path(payload: Any, cwd: Path) -> Path | None:
    path_text = first_text(payload, TRANSCRIPT_KEYS)
    if not path_text:
        return None
    expanded = Path(os.path.expandvars(os.path.expanduser(path_text)))
    if not expanded.is_absolute():
        expanded = cwd / expanded
    return expanded if expanded.exists() else None


def text_sources_from_payload(payload: Any, label: str) -> list[TextSource]:
    sources: list[TextSource] = []
    seen: set[int] = set()

    def walk(value: Any, source_label: str, inherited_role: str = "") -> None:
        obj_id = id(value)
        if obj_id in seen:
            return
        seen.add(obj_id)

        if isinstance(value, dict):
            role = normalize_role(coerce_text(value.get("role")) or inherited_role)
            if role in IGNORED_ROLES:
                return

            text = first_available_text(value)
            if text:
                sources.append(TextSource(source_label, role or "unknown", text))

            for key, child in value.items():
                if key in TEXT_KEYS:
                    continue
                walk(child, f"{source_label}.{key}", role)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{source_label}[{index}]", inherited_role)
        elif isinstance(value, str) and len(value) > 40:
            sources.append(TextSource(source_label, inherited_role or "unknown", value))

    walk(payload, label)
    return dedupe_sources(sources)


def read_transcript_sources(path: Path) -> list[TextSource]:
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError as error:
        return [TextSource("transcript-read-error", "unknown", f"Could not read transcript {path}: {error}")]

    stripped = raw.strip()
    if not stripped:
        return []

    try:
        parsed = json.loads(stripped)
        return text_sources_from_payload(parsed, f"transcript:{path}")
    except json.JSONDecodeError:
        pass

    jsonl_sources: list[TextSource] = []
    for line_no, line in enumerate(stripped.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            parsed_line = json.loads(line)
        except json.JSONDecodeError:
            jsonl_sources = []
            break
        jsonl_sources.extend(text_sources_from_payload(parsed_line, f"transcript:{path}:{line_no}"))
    if jsonl_sources:
        return dedupe_sources(jsonl_sources)

    return [TextSource(f"transcript:{path}", "unknown", stripped)]


def first_available_text(value: dict[str, Any]) -> str:
    for key in TEXT_KEYS:
        text = coerce_text(value.get(key))
        if text:
            return text
    return ""


def coerce_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        parts = [coerce_text(item) for item in value]
        return "\n".join(part for part in parts if part).strip()
    if isinstance(value, dict):
        if "text" in value:
            return coerce_text(value.get("text"))
        if "content" in value:
            return coerce_text(value.get("content"))
        if "value" in value:
            return coerce_text(value.get("value"))
    return ""


def normalize_role(role: str) -> str:
    return role.strip().lower().replace("-", "_") if role else ""


def dedupe_sources(sources: list[TextSource]) -> list[TextSource]:
    result: list[TextSource] = []
    seen: set[str] = set()
    for source in sources:
        key = stable_hash({"role": source.role, "text": source.text})
        if key in seen or not source.text:
            continue
        seen.add(key)
        result.append(source)
    return result


def extract_carry_forward_items(sources: list[TextSource], max_items: int) -> Extraction:
    extraction = Extraction()
    if not sources:
        extraction.limitations.append("No transcript or message text was available in the compact hook payload.")
        return extraction

    seen_items: set[str] = set()
    seen_sections: set[str] = set()

    for source in sources:
        if source.role in IGNORED_ROLES:
            continue
        lines = source.text.splitlines()

        for line in lines:
            item = extract_open_item_line(line)
            if item and item not in seen_items:
                extraction.open_items.append(item)
                seen_items.add(item)
                if len(extraction.open_items) >= max_items:
                    break
        if len(extraction.open_items) >= max_items:
            break

        for section in extract_plan_sections(lines):
            key = stable_hash(section)
            if key in seen_sections:
                continue
            seen_sections.add(key)
            extraction.plan_sections.append((source.label, section))
            if len(extraction.plan_sections) >= max_items:
                break
        if len(extraction.plan_sections) >= max_items:
            break

    if not extraction.open_items and not extraction.plan_sections:
        extraction.limitations.append(
            "No obvious open checklist item, pending status, plan, goal, or design section was found."
        )
    return extraction


def extract_open_item_line(line: str) -> str:
    stripped = line.strip()
    if not stripped:
        return ""
    checkbox = OPEN_CHECKBOX_RE.match(stripped)
    if checkbox:
        return f"- [ ] {checkbox.group(1).strip()}"
    if STATUS_RE.search(stripped) or CN_STATUS_RE.search(stripped):
        if len(stripped) > 260:
            stripped = stripped[:257].rstrip() + "..."
        if stripped.startswith(("- ", "* ", "+ ")):
            return stripped
        return f"- [ ] {stripped}"
    return ""


def extract_plan_sections(lines: list[str]) -> list[str]:
    sections: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        heading = HEADING_RE.match(line.strip())
        if not heading or not PLAN_HEADING_RE.search(heading.group(2)):
            index += 1
            continue

        heading_level = len(heading.group(1))
        captured = [line.rstrip()]
        index += 1
        while index < len(lines) and len(captured) < MAX_SECTION_LINES:
            next_line = lines[index]
            next_heading = HEADING_RE.match(next_line.strip())
            if next_heading and len(next_heading.group(1)) <= heading_level:
                break
            if next_line.strip():
                captured.append(next_line.rstrip())
            index += 1
        section = "\n".join(captured).strip()
        if len(section) > 40:
            sections.append(section)
    return sections


def build_snapshot(
    now: str,
    cwd: Path,
    event: str,
    trigger: str,
    payload_note: str,
    transcript_path: Path | None,
    extraction: Extraction,
) -> str:
    lines = [
        f"## Snapshot {now}",
        "",
        f"- Event: `{event}`",
        f"- Compact trigger: `{trigger}`",
        f"- CWD: `{cwd}`",
        f"- Hook payload: {payload_note}",
        f"- Transcript: `{transcript_path}`" if transcript_path else "- Transcript: unavailable",
        "",
        "### Unresolved Task Candidates",
        "",
    ]

    if extraction.open_items:
        lines.extend(extraction.open_items)
    else:
        lines.append("- None detected by heuristic extraction.")

    lines.extend(["", "### Plan / Design Context Candidates", ""])
    if extraction.plan_sections:
        for label, section in extraction.plan_sections:
            lines.append(f"Source: `{label}`")
            lines.append("")
            lines.append(fence(section))
            lines.append("")
    else:
        lines.append("- None detected by heuristic extraction.")

    if extraction.limitations:
        lines.extend(["", "### Extraction Limitations", ""])
        for limitation in extraction.limitations:
            lines.append(f"- {limitation}")

    lines.append("")
    return "\n".join(lines)


def fence(text: str) -> str:
    ticks = "```"
    while ticks in text:
        ticks += "`"
    return f"{ticks}md\n{text}\n{ticks}"


def append_snapshot(output: Path, snapshot: str) -> None:
    if output.exists():
        with output.open("a", encoding="utf-8") as handle:
            handle.write("\n")
            handle.write(snapshot)
        return

    header = "\n".join(
        [
            "# Compact Task State",
            "",
            "This file is generated by `hooks/hooks/save_compact_tasks.py` before Codex compact events.",
            "It records likely unresolved goals, plans, and design context so work can resume after context compression.",
            "Treat extracted items as carry-forward candidates and verify them against source artifacts when needed.",
            "",
        ]
    )
    output.write_text(header + snapshot, encoding="utf-8")


def load_state(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"seen": []}


def update_state(path: Path, state: dict[str, Any], fingerprint: str, now: str) -> None:
    seen = list(state.get("seen", []))
    seen.append(fingerprint)
    state["seen"] = seen[-200:]
    state["updated_at"] = now
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
