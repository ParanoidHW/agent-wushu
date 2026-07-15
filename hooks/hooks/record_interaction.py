#!/usr/bin/env python3
"""Record user/agent interaction history in the project Markdown spec.

The script is designed for hook usage:

1. Pipe a JSON event into stdin. The script extracts topic-relevant user and
   assistant messages, ignores tool/system/developer content, and appends new
   complete QA turns.
2. Or call the `append` subcommand with explicit --user/--agent values.

It writes Markdown compatible with interaction-record-spec.md and the static
viewer in interaction-viewer.html.
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
from typing import Any, Iterable

SPEC_NAME = "agent-interaction-record"
SPEC_VERSION = "1.0"
DEFAULT_OUTPUT = "interaction-history.md"
DEFAULT_STATE = ".interaction-recorder-state.json"
IGNORED_ROLES = {"system", "developer", "tool", "function"}
USER_ROLES = {"user", "human"}
AGENT_ROLES = {"assistant", "agent", "ai"}
TOOL_HOOK_EVENTS = {"pretooluse", "posttooluse", "tooluse", "toolcall", "tool_call", "mcp_tool_call"}
TOOL_PROMPT_KEYS = {
    "prompt",
    "user_prompt",
    "input_prompt",
    "positive_prompt",
    "negative_prompt",
    "system_prompt",
    "instructions",
    "instruction",
    "query",
    "search_query",
    "question",
    "request",
    "task",
}
SECONDARY_TOOL_PROMPT_KEYS = {"description", "text", "message", "input"}
NOISE_PATTERNS = [
    re.compile(r"^\s*<environment_context>[\s\S]*?</environment_context>\s*$", re.I),
    re.compile(r"^\s*<codex_internal_context\b[\s\S]*?</codex_internal_context>\s*$", re.I),
    re.compile(r"^\s*<tool_call\b[\s\S]*?</tool_call>\s*$", re.I),
    re.compile(r"^\s*<tool_result\b[\s\S]*?</tool_result>\s*$", re.I),
]
HEADING_PATTERN = re.compile(r"^##\s+Turn\s+(\d+)(?::\s*(.*))?\s*$", re.M | re.I)


class RecorderError(Exception):
    """Raised when the input cannot be turned into an interaction record."""


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "append":
            turns = [
                Turn(
                    user=args.user.strip(),
                    agent=args.agent.strip(),
                    title=args.turn_title.strip() if args.turn_title else "",
                    notes=args.notes.strip() if args.notes else "",
                    tags=args.tags.strip() if args.tags else "",
                )
            ]
        else:
            raw = sys.stdin.read()
            if not raw.strip():
                raise RecorderError("stdin is empty; pass hook JSON or use the append subcommand")
            turns = turns_from_payload(
                load_json(raw),
                include_partial=args.include_partial,
                include_process=args.include_process,
            )

        if not turns:
            if not args.quiet:
                print("No complete topic-relevant QA turns found; nothing written.", file=sys.stderr)
            return 0

        written = record_turns(
            turns=turns,
            output=Path(args.output),
            state_file=Path(args.state_file) if args.state_file else None,
            title=args.title,
            topic=args.topic,
            user_name=args.user_name,
            agent_name=args.agent_name,
            source=args.source,
            dry_run=args.dry_run,
        )

        if not args.quiet:
            action = "Would append" if args.dry_run else "Appended"
            print(f"{action} {written} turn(s) to {args.output}.")
        return 0
    except RecorderError as error:
        if not getattr(args, "quiet", False):
            print(f"record_interaction.py: {error}", file=sys.stderr)
        return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Append user/agent QA turns to a Markdown interaction record."
    )
    parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Markdown record path. Default: {DEFAULT_OUTPUT}",
    )
    parser.add_argument(
        "--state-file",
        default=DEFAULT_STATE,
        help=f"JSON state file used to avoid duplicate hook appends. Default: {DEFAULT_STATE}",
    )
    parser.add_argument("--title", default="Agent Interaction History", help="Record title for new files.")
    parser.add_argument("--topic", default="", help="Topic description for new files.")
    parser.add_argument("--user-name", default="User", help="User display name for new files.")
    parser.add_argument("--agent-name", default="Agent", help="Agent display name for new files.")
    parser.add_argument("--source", default="hook", help="Source field for new files.")
    parser.add_argument("--dry-run", action="store_true", help="Parse and report without writing files.")
    parser.add_argument("--quiet", action="store_true", help="Suppress stdout/stderr status messages for hooks.")
    parser.add_argument(
        "--include-partial",
        action="store_true",
        help="Record a trailing user message without an agent response as an empty-agent turn.",
    )
    parser.add_argument(
        "--include-process",
        action="store_true",
        help="Include public process summaries from Codex transcripts in the Notes section.",
    )

    subparsers = parser.add_subparsers(dest="command")
    append = subparsers.add_parser("append", help="Append one explicit QA turn.")
    append.add_argument("--user", required=True, help="User message Markdown.")
    append.add_argument("--agent", required=True, help="Agent response Markdown.")
    append.add_argument("--turn-title", default="", help="Optional turn title.")
    append.add_argument("--notes", default="", help="Optional Notes section.")
    append.add_argument("--tags", default="", help="Optional comma-separated Tags section.")
    return parser


class Turn:
    def __init__(
        self,
        user: str,
        agent: str,
        title: str = "",
        notes: str = "",
        tags: str = "",
    ) -> None:
        self.user = strip_noise(user)
        self.agent = strip_noise(agent)
        self.title = clean_heading_text(title)
        self.notes = strip_noise(notes)
        self.tags = strip_noise(tags)

    def is_complete(self) -> bool:
        return bool(self.user.strip()) and bool(self.agent.strip())

    def fingerprint(self) -> str:
        payload = json.dumps(
            {
                "user": normalize_for_hash(self.user),
                "agent": normalize_for_hash(self.agent),
                "notes": normalize_for_hash(self.notes),
                "tags": normalize_for_hash(self.tags),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_json(raw: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as error:
        raise RecorderError(f"stdin is not valid JSON: {error}") from error


def turns_from_payload(
    payload: Any,
    include_partial: bool = False,
    include_process: bool = False,
) -> list[Turn]:
    if isinstance(payload, dict):
        event_name = hook_event_name(payload)
        if event_name == "subagentstop":
            return turns_from_subagent_stop_payload(payload)
        if event_name in {"precompact", "postcompact"}:
            return turns_from_compact_hook_payload(payload, include_process=include_process)

    if isinstance(payload, dict) and is_tool_hook_payload(payload):
        return turns_from_tool_hook_payload(payload)

    try:
        turns = turns_from_hook_payload(payload, include_partial=include_partial)
    except RecorderError:
        turns = []

    if turns:
        return turns

    if isinstance(payload, dict):
        return turns_from_codex_payload(payload, include_process=include_process)

    return []


def hook_event_name(payload: dict[str, Any]) -> str:
    event_name = normalize_role(
        extract_first_text(payload, "hook_event_name", "hookEventName", "event_name", "eventName")
    )
    if event_name:
        return event_name

    nested = payload.get("event")
    if isinstance(nested, dict):
        return hook_event_name(nested)
    return ""


def turns_from_subagent_stop_payload(payload: dict[str, Any]) -> list[Turn]:
    agent_id = extract_first_text(payload, "agent_id", "agentId") or "unknown"
    agent_type = extract_first_text(payload, "agent_type", "agentType") or "subagent"
    task = extract_first_text(
        payload,
        "prompt",
        "user_prompt",
        "userPrompt",
        "task",
        "description",
        "instruction",
    )
    summary = extract_first_text(
        payload,
        "last_assistant_message",
        "lastAssistantMessage",
        "last_agent_message",
        "lastAgentMessage",
        "summary",
        "result",
        "response",
        "output",
    )
    if not summary:
        summary = "Subagent stopped without a public completion summary."

    user = f"Subagent `{agent_type}` (`{agent_id}`) completed."
    if task:
        user = f"{user}\n\nAssigned task:\n{compact_process_text(task)}"

    notes = [part for part in [codex_note(payload)] if part]
    notes.extend([f"agent_id: {agent_id}", f"agent_type: {agent_type}"])
    return [
        Turn(
            user=user,
            agent=summary,
            title=f"Subagent {agent_type} completed",
            notes="\n".join(notes),
            tags="codex, subagent, hook",
        )
    ]


def turns_from_compact_hook_payload(payload: dict[str, Any], include_process: bool) -> list[Turn]:
    event_name = hook_event_name(payload) or "precompact"
    trigger = extract_first_text(payload, "trigger", "compact_trigger", "compactTrigger", "reason", "source")
    trigger = trigger or "unknown"
    context_turn = latest_transcript_turn_from_payload(payload, include_process=include_process)
    agent = extract_first_text(
        payload,
        "last_assistant_message",
        "lastAssistantMessage",
        "last_agent_message",
        "lastAgentMessage",
        "summary",
    )
    if not agent and context_turn:
        agent = context_turn.agent
    if not agent:
        agent = "Context compaction snapshot recorded."

    notes = [part for part in [codex_note(payload)] if part]
    notes.append(f"compact_trigger: {trigger}")
    if context_turn:
        notes.append(f"Last user request:\n{compact_process_text(context_turn.user)}")
        process = key_process_from_notes(context_turn.notes)
        if process:
            notes.append(process)

    return [
        Turn(
            user=f"Context compaction requested ({trigger}).",
            agent=agent,
            title=f"Context compact ({trigger})",
            notes="\n\n".join(notes),
            tags="codex, compact, hook",
        )
    ]


def latest_transcript_turn_from_payload(payload: dict[str, Any], include_process: bool) -> Turn | None:
    has_transcript_reference = any(
        key in payload
        for key in (
            "transcript_path",
            "transcriptPath",
            "agent_transcript_path",
            "agentTranscriptPath",
            "rollout_path",
            "rolloutPath",
            "session_id",
            "sessionId",
        )
    )
    if not has_transcript_reference:
        return None

    transcript = transcript_path_from_payload(payload)
    if not transcript:
        return None
    turns = turns_from_codex_transcript(transcript, include_process=include_process)
    return turns[-1] if turns else None


def key_process_from_notes(notes: str) -> str:
    marker = "Key process:"
    index = notes.find(marker)
    if index == -1:
        return ""
    process = strip_noise(notes[index:]).strip()
    if len(process) <= 1200:
        return process
    return process[:1197].rstrip() + "..."


def is_tool_hook_payload(payload: dict[str, Any]) -> bool:
    event_name = normalize_role(
        extract_first_text(payload, "hook_event_name", "hookEventName", "event_name", "eventName")
    )
    if event_name in TOOL_HOOK_EVENTS:
        return True

    nested = payload.get("event")
    if isinstance(nested, dict) and is_tool_hook_payload(nested):
        return True

    return any(
        key in payload
        for key in (
            "tool_name",
            "toolName",
            "tool_input",
            "toolInput",
            "tool_call",
            "toolCall",
            "mcp_tool",
            "mcpTool",
        )
    )


def turns_from_tool_hook_payload(payload: dict[str, Any]) -> list[Turn]:
    nested = payload.get("event")
    if isinstance(nested, dict) and not any(
        key in payload for key in ("tool_name", "toolName", "tool_input", "toolInput")
    ):
        payload = nested

    tool_name = extract_first_text(
        payload,
        "tool_name",
        "toolName",
        "name",
        "tool",
        "mcp_tool",
        "mcpTool",
    ) or "unknown-tool"
    tool_input = first_present_value(
        payload,
        "tool_input",
        "toolInput",
        "arguments",
        "args",
        "parameters",
        "params",
        "input",
    )
    if tool_input is None:
        tool_input = payload

    prompt_entries = tool_prompt_entries(tool_input, tool_name)
    if not prompt_entries and tool_input is not payload:
        prompt_entries = tool_prompt_entries(payload, tool_name)
    if not prompt_entries:
        return []

    prompt_text = format_tool_prompt_entries(prompt_entries)
    tags = ["codex", "tool-prompt", "hook"]
    if is_mcp_tool(tool_name):
        tags.append("mcp")

    return [
        Turn(
            user=prompt_text,
            agent=f"Tool call: `{tool_name}`",
            title=infer_title(f"{tool_name}: {prompt_text}"),
            notes=tool_note(payload, tool_name),
            tags=", ".join(tags),
        )
    ]


def first_present_value(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in payload:
            return payload.get(key)
    return None


def tool_prompt_entries(tool_input: Any, tool_name: str) -> list[tuple[str, str]]:
    entries = collect_prompt_entries(tool_input, TOOL_PROMPT_KEYS)
    if entries:
        return dedupe_prompt_entries(entries)

    if allow_secondary_tool_prompt(tool_name, tool_input):
        return dedupe_prompt_entries(collect_prompt_entries(tool_input, SECONDARY_TOOL_PROMPT_KEYS))

    return []


def collect_prompt_entries(value: Any, key_names: set[str], path: str = "") -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_path = f"{path}.{key}" if path else str(key)
            if normalize_field_name(key) in key_names:
                text = prompt_value_to_text(child)
                if text:
                    entries.append((key_path, text))
                continue
            if isinstance(child, (dict, list)):
                entries.extend(collect_prompt_entries(child, key_names, key_path))
        return entries

    if isinstance(value, list):
        for index, child in enumerate(value):
            if isinstance(child, (dict, list)):
                entries.extend(collect_prompt_entries(child, key_names, f"{path}[{index}]"))

    return entries


def dedupe_prompt_entries(entries: list[tuple[str, str]]) -> list[tuple[str, str]]:
    seen: set[tuple[str, str]] = set()
    unique: list[tuple[str, str]] = []
    for label, text in entries:
        fingerprint = (label, normalize_for_hash(text))
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        unique.append((label, text))
    return unique


def allow_secondary_tool_prompt(tool_name: str, tool_input: Any) -> bool:
    lower_tool = tool_name.lower()
    if is_mcp_tool(tool_name) or "agent" in lower_tool or "image" in lower_tool:
        return True
    if isinstance(tool_input, dict):
        command_keys = {"command", "cmd", "script", "path", "file_path", "filename"}
        input_keys = {normalize_field_name(key) for key in tool_input}
        return not bool(input_keys & command_keys)
    return False


def prompt_value_to_text(value: Any) -> str:
    text = extract_text(value)
    if text:
        return text
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True).strip()
    return str(value).strip() if value is not None else ""


def format_tool_prompt_entries(entries: list[tuple[str, str]]) -> str:
    if len(entries) == 1:
        return entries[0][1]

    parts: list[str] = []
    for label, text in entries:
        parts.extend([f"#### {label}", "", text.strip(), ""])
    return "\n".join(parts).strip()


def tool_note(payload: dict[str, Any], tool_name: str) -> str:
    parts = [part for part in [codex_note(payload)] if part]
    parts.append(f"tool_name: {tool_name}")

    tool_call_id = extract_first_text(
        payload,
        "tool_call_id",
        "toolCallId",
        "tool_use_id",
        "toolUseId",
        "call_id",
        "callId",
    )
    cwd = extract_first_text(payload, "cwd", "working_directory", "workingDirectory")
    if tool_call_id:
        parts.append(f"tool_call_id: {tool_call_id}")
    if cwd:
        parts.append(f"cwd: {cwd}")
    return "\n".join(parts)


def is_mcp_tool(tool_name: str) -> bool:
    lower = tool_name.lower()
    return lower.startswith("mcp__") or lower.startswith("mcp.") or lower.startswith("mcp-")


def normalize_field_name(value: Any) -> str:
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", str(value or ""))
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def turns_from_codex_payload(payload: dict[str, Any], include_process: bool = False) -> list[Turn]:
    """Extract a QA turn from native Codex hook payloads.

    Stop hooks normally include fields such as transcript_path, session_id,
    turn_id, and last_assistant_message. Depending on the Codex surface, prompt
    may or may not be included, so transcript parsing is the reliable fallback.
    """
    user_text = extract_first_text(
        payload,
        "prompt",
        "user_prompt",
        "userPrompt",
        "input",
        "input_text",
        "inputText",
    )
    agent_text = extract_first_text(
        payload,
        "last_assistant_message",
        "lastAssistantMessage",
        "last_agent_message",
        "lastAgentMessage",
        "response",
        "assistant_response",
        "assistantResponse",
        "answer",
    )

    if user_text and agent_text:
        return [
            Turn(
                user=user_text,
                agent=agent_text,
                title=infer_title(user_text),
                notes=codex_note(payload),
                tags="codex, hook",
            )
        ]

    transcript = transcript_path_from_payload(payload)
    if transcript:
        turns = turns_from_codex_transcript(transcript, include_process=include_process)
        if turns:
            latest = turns[-1]
            if agent_text and not latest.agent:
                latest.agent = agent_text
            if latest.is_complete():
                return [latest]

    if agent_text:
        latest_user = latest_user_prompt_from_history(payload)
        if latest_user:
            return [
                Turn(
                    user=latest_user,
                    agent=agent_text,
                    title=infer_title(latest_user),
                    notes=codex_note(payload),
                    tags="codex, hook",
                )
            ]

    return []


def turns_from_hook_payload(payload: Any, include_partial: bool = False) -> list[Turn]:
    messages = extract_messages(payload)
    turns: list[Turn] = []
    pending_user: str | None = None

    for message in messages:
        role = normalize_role(message.get("role"))
        if role in IGNORED_ROLES:
            continue

        content = extract_text(message.get("content"))
        if not content or is_noise(content):
            continue

        if role in USER_ROLES:
            pending_user = content
            continue

        if role in AGENT_ROLES and pending_user:
            turn = Turn(
                user=pending_user,
                agent=content,
                title=message.get("title", "") or infer_title(pending_user),
                notes=message.get("notes", ""),
                tags=coerce_tags(message.get("tags", "")),
            )
            if turn.is_complete():
                turns.append(turn)
            pending_user = None

    if include_partial and pending_user:
        turns.append(Turn(user=pending_user, agent="", title=infer_title(pending_user)))

    return turns


def extract_messages(payload: Any) -> list[dict[str, Any]]:
    """Find message-like dictionaries in common hook payload shapes."""
    if isinstance(payload, list):
        return [item for item in payload if is_message(item)]

    if not isinstance(payload, dict):
        raise RecorderError("hook JSON must be an object or an array of messages")

    for key in ("messages", "conversation", "turns", "transcript", "history"):
        value = payload.get(key)
        if isinstance(value, list):
            return normalize_message_list(value)

    direct = direct_messages_from_event(payload)
    if direct:
        return direct

    nested = payload.get("event")
    if isinstance(nested, dict):
        return extract_messages(nested)

    raise RecorderError(
        "could not find messages; expected messages/conversation/turns/transcript/history or role/content"
    )


def normalize_message_list(items: Iterable[Any]) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    for item in items:
        if is_message(item):
            messages.append(item)
            continue

        if isinstance(item, dict) and ("user" in item or "agent" in item or "assistant" in item):
            if item.get("user"):
                messages.append({"role": "user", "content": item.get("user")})
            agent = item.get("agent", item.get("assistant"))
            if agent:
                messages.append({"role": "assistant", "content": agent})
            continue

        if isinstance(item, dict) and ("question" in item or "answer" in item):
            if item.get("question"):
                messages.append({"role": "user", "content": item.get("question")})
            if item.get("answer"):
                messages.append({"role": "assistant", "content": item.get("answer")})

    return messages


def direct_messages_from_event(payload: dict[str, Any]) -> list[dict[str, Any]]:
    role = payload.get("role") or payload.get("speaker") or payload.get("author")
    content = payload.get("content") or payload.get("message") or payload.get("text")
    if role and content is not None:
        return [{"role": role, "content": content}]

    if payload.get("prompt") and payload.get("response"):
        return [
            {"role": "user", "content": payload.get("prompt")},
            {
                "role": "assistant",
                "content": payload.get("response"),
                "title": payload.get("title", infer_title(extract_text(payload.get("prompt")))),
                "notes": payload.get("notes", ""),
                "tags": payload.get("tags", ""),
            },
        ]

    assistant = extract_first_text(
        payload,
        "last_assistant_message",
        "lastAssistantMessage",
        "last_agent_message",
        "lastAgentMessage",
    )
    if payload.get("prompt") and assistant:
        return [
            {"role": "user", "content": payload.get("prompt")},
            {
                "role": "assistant",
                "content": assistant,
                "title": infer_title(extract_text(payload.get("prompt"))),
                "notes": payload.get("notes", "") or codex_note(payload),
                "tags": payload.get("tags", "") or "codex, hook",
            },
        ]

    return []


def extract_first_text(payload: dict[str, Any], *keys: str) -> str:
    for key in keys:
        if key in payload:
            text = extract_text(payload.get(key))
            if text:
                return text
    return ""


def codex_note(payload: dict[str, Any]) -> str:
    parts = []
    event_name = extract_first_text(payload, "hook_event_name", "hookEventName", "event_name", "eventName")
    session_id = extract_first_text(payload, "session_id", "sessionId")
    turn_id = extract_first_text(payload, "turn_id", "turnId")
    if event_name:
        parts.append(f"hook_event_name: {event_name}")
    if session_id:
        parts.append(f"session_id: {session_id}")
    if turn_id:
        parts.append(f"turn_id: {turn_id}")
    return "\n".join(parts)


def transcript_path_from_payload(payload: dict[str, Any]) -> Path | None:
    raw_path = extract_first_text(
        payload,
        "transcript_path",
        "transcriptPath",
        "agent_transcript_path",
        "agentTranscriptPath",
        "rollout_path",
        "rolloutPath",
    )
    if raw_path:
        path = expand_path(raw_path)
        if path.exists():
            return path

    session_id = extract_first_text(payload, "session_id", "sessionId", "conversation_id", "conversationId")
    if session_id:
        found = find_transcript_by_session_id(session_id)
        if found:
            return found

    return latest_codex_transcript()


def expand_path(value: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(value)))


def codex_home() -> Path:
    return expand_path(os.environ.get("CODEX_HOME", "~/.codex"))


def find_transcript_by_session_id(session_id: str) -> Path | None:
    sessions_dir = codex_home() / "sessions"
    if not sessions_dir.exists():
        return None
    matches = sorted(sessions_dir.rglob(f"*{session_id}*.jsonl"), key=lambda item: item.stat().st_mtime)
    return matches[-1] if matches else None


def latest_codex_transcript() -> Path | None:
    sessions_dir = codex_home() / "sessions"
    if not sessions_dir.exists():
        return None
    latest: Path | None = None
    latest_mtime = -1.0
    for path in sessions_dir.rglob("*.jsonl"):
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        if mtime > latest_mtime:
            latest = path
            latest_mtime = mtime
    return latest


def turns_from_codex_transcript(path: Path, include_process: bool = False) -> list[Turn]:
    turns: list[Turn] = []
    pending_user = ""
    last_assistant = ""
    last_turn_id = ""
    session_id = ""
    process_entries: list[tuple[str, str]] = []
    process_seen: set[str] = set()

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []

    for line in lines:
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue

        payload = item.get("payload")
        if not isinstance(payload, dict):
            continue

        if item.get("type") == "session_meta":
            session_id = extract_first_text(payload, "session_id", "id")
            continue

        payload_type = payload.get("type")
        if item.get("type") == "event_msg" and payload_type == "user_message":
            pending_user = extract_text(payload.get("message"))
            last_assistant = ""
            last_turn_id = ""
            process_entries = []
            process_seen = set()
            continue

        if item.get("type") == "event_msg" and payload_type == "task_started":
            last_turn_id = extract_first_text(payload, "turn_id", "turnId")
            continue

        if include_process and pending_user:
            collect_public_process_entry(payload, process_entries, process_seen)

        if item.get("type") == "event_msg" and payload_type == "task_complete":
            last_assistant = extract_text(payload.get("last_agent_message"))
            if pending_user and last_assistant:
                notes = codex_note(
                    {
                        "hook_event_name": "transcript",
                        "session_id": session_id,
                        "turn_id": payload.get("turn_id") or last_turn_id,
                    }
                )
                turns.append(
                    Turn(
                        user=pending_user,
                        agent=last_assistant,
                        title=infer_title(pending_user),
                        notes=append_process_notes(notes, process_entries),
                        tags="codex, transcript",
                    )
                )
                pending_user = ""
                last_assistant = ""
                process_entries = []
                process_seen = set()
            continue

        if item.get("type") == "response_item" and payload_type == "message":
            role = normalize_role(payload.get("role"))
            phase = normalize_role(payload.get("phase"))
            if role == "assistant" and phase in {"final", "final_answer"}:
                last_assistant = extract_text(payload.get("content"))

    if pending_user and last_assistant:
        notes = codex_note(
            {
                "hook_event_name": "transcript",
                "session_id": session_id,
                "turn_id": last_turn_id,
            }
        )
        turns.append(
            Turn(
                user=pending_user,
                agent=last_assistant,
                title=infer_title(pending_user),
                notes=append_process_notes(notes, process_entries),
                tags="codex, transcript",
            )
        )

    return turns


def collect_public_process_entry(
    payload: dict[str, Any],
    entries: list[tuple[str, str]],
    seen: set[str],
) -> None:
    """Collect public process signals only; never inspect encrypted reasoning."""
    payload_type = payload.get("type")

    if payload_type == "agent_message" and normalize_role(payload.get("phase")) == "commentary":
        append_process_entry(entries, seen, "Update", extract_text(payload.get("message")))
        return

    if payload_type == "message":
        role = normalize_role(payload.get("role"))
        phase = normalize_role(payload.get("phase"))
        if role == "assistant" and phase == "commentary":
            append_process_entry(entries, seen, "Update", extract_text(payload.get("content")))
        return

    if payload_type == "reasoning":
        summary = extract_text(payload.get("summary"))
        if summary:
            append_process_entry(entries, seen, "Reasoning summary", summary)


def append_process_entry(
    entries: list[tuple[str, str]],
    seen: set[str],
    label: str,
    text: str,
) -> None:
    cleaned = compact_process_text(text)
    if not cleaned:
        return
    fingerprint = normalize_for_hash(cleaned)
    if fingerprint in seen:
        return
    seen.add(fingerprint)
    entries.append((label, cleaned))


def compact_process_text(text: str, max_chars: int = 1200) -> str:
    cleaned = re.sub(r"\s+", " ", strip_noise(text)).strip()
    if not cleaned:
        return ""
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max_chars - 3].rstrip() + "..."


def append_process_notes(notes: str, entries: list[tuple[str, str]], max_entries: int = 12) -> str:
    if not entries:
        return notes

    lines = ["Key process:"]
    for index, (label, text) in enumerate(entries[:max_entries], start=1):
        lines.append(f"{index}. {label}: {text}")
    if len(entries) > max_entries:
        lines.append(f"... {len(entries) - max_entries} more process update(s) omitted.")

    process_block = "\n".join(lines)
    return f"{notes.rstrip()}\n\n{process_block}".strip()


def latest_user_prompt_from_history(payload: dict[str, Any]) -> str:
    session_id = extract_first_text(payload, "session_id", "sessionId", "conversation_id", "conversationId")
    history_path = codex_home() / "history.jsonl"
    if not history_path.exists():
        return ""

    latest = ""
    try:
        lines = history_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ""

    for line in lines:
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if session_id and item.get("session_id") != session_id:
            continue
        text = extract_text(item.get("text"))
        if text:
            latest = text
    return latest


def is_message(value: Any) -> bool:
    return isinstance(value, dict) and (
        ("role" in value and "content" in value)
        or ("speaker" in value and "content" in value)
        or ("author" in value and "content" in value)
    )


def normalize_role(role: Any) -> str:
    return str(role or "").strip().lower()


def extract_text(content: Any) -> str:
    if content is None:
        return ""

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            text = extract_content_part(item)
            if text:
                parts.append(text)
        return "\n\n".join(parts).strip()

    if isinstance(content, dict):
        return extract_content_part(content).strip()

    return str(content).strip()


def extract_content_part(item: Any) -> str:
    if isinstance(item, str):
        return item.strip()

    if not isinstance(item, dict):
        return ""

    part_type = str(item.get("type", "")).lower()
    if part_type in {"tool_use", "tool_result", "function_call", "function_result"}:
        return ""

    for key in ("text", "content", "message", "value"):
        value = item.get(key)
        if isinstance(value, str):
            return value.strip()

    return ""


def strip_noise(value: str) -> str:
    text = value.replace("\r\n", "\n").replace("\r", "\n").strip()
    for pattern in NOISE_PATTERNS:
        text = pattern.sub("", text).strip()
    return text


def is_noise(value: str) -> bool:
    text = value.strip()
    if not text:
        return True
    return any(pattern.match(text) for pattern in NOISE_PATTERNS)


def coerce_tags(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item).strip() for item in value if str(item).strip())
    return extract_text(value)


def infer_title(user_text: str, max_chars: int = 36) -> str:
    text = re.sub(r"\s+", " ", user_text).strip()
    text = clean_heading_text(text)
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "..."


def clean_heading_text(value: str) -> str:
    return re.sub(r"[\r\n#]+", " ", value).strip()


def normalize_for_hash(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def record_turns(
    turns: list[Turn],
    output: Path,
    state_file: Path | None,
    title: str,
    topic: str,
    user_name: str,
    agent_name: str,
    source: str,
    dry_run: bool = False,
) -> int:
    existing_hashes = read_existing_hashes(output)
    state = load_state(state_file)
    known_hashes = set(existing_hashes) | set(state.get("turn_hashes", []))
    new_turns = [turn for turn in turns if turn.fingerprint() not in known_hashes]

    if dry_run:
        return len(new_turns)

    if not new_turns:
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)
    if not output.exists():
        output.write_text(
            build_header(
                title=title,
                topic=topic,
                user_name=user_name,
                agent_name=agent_name,
                source=source,
            ),
            encoding="utf-8",
        )

    current = output.read_text(encoding="utf-8")
    next_number = next_turn_number(current)
    chunks = []

    for offset, turn in enumerate(new_turns):
        chunks.append(format_turn(next_number + offset, turn))

    with output.open("a", encoding="utf-8", newline="\n") as handle:
        if current and not current.endswith("\n"):
            handle.write("\n")
        handle.write("\n".join(chunks))
        handle.write("\n")

    state["turn_hashes"] = sorted(known_hashes | {turn.fingerprint() for turn in new_turns})
    state["updated"] = dt.date.today().isoformat()
    save_state(state_file, state)
    return len(new_turns)


def build_header(
    title: str,
    topic: str,
    user_name: str,
    agent_name: str,
    source: str,
) -> str:
    today = dt.date.today().isoformat()
    return (
        "---\n"
        f"spec: {SPEC_NAME}\n"
        f"version: {SPEC_VERSION}\n"
        f"title: {yaml_scalar(title)}\n"
        f"created: {today}\n"
        f"updated: {today}\n"
        "participants:\n"
        f"  user: {yaml_scalar(user_name)}\n"
        f"  agent: {yaml_scalar(agent_name)}\n"
        f"topic: {yaml_scalar(topic)}\n"
        f"source: {yaml_scalar(source)}\n"
        "---\n\n"
        f"# {title.strip() or 'Agent Interaction History'}\n"
    )


def yaml_scalar(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return '""'
    if re.fullmatch(r"[A-Za-z0-9_.:/ -]+", text):
        return text
    return json.dumps(text, ensure_ascii=False)


def next_turn_number(markdown: str) -> int:
    numbers = [int(match.group(1)) for match in HEADING_PATTERN.finditer(markdown)]
    return max(numbers, default=0) + 1


def format_turn(number: int, turn: Turn) -> str:
    title = f": {turn.title}" if turn.title else ""
    sections = [
        f"## Turn {number}{title}",
        "",
        "### User",
        "",
        protect_reserved_headings(turn.user),
        "",
        "### Agent",
        "",
        protect_reserved_headings(turn.agent),
    ]

    if turn.notes:
        sections.extend(["", "### Notes", "", protect_reserved_headings(turn.notes)])

    if turn.tags:
        sections.extend(["", "### Tags", "", turn.tags])

    return "\n".join(sections).rstrip() + "\n"


def protect_reserved_headings(markdown: str) -> str:
    """Fence content that would otherwise be parsed as record section markers."""
    reserved = re.compile(r"^(##\s+Turn\b|###\s+(User|Agent|Notes|Tags)\s*$)", re.M | re.I)
    if not reserved.search(markdown):
        return markdown.strip()
    return "```markdown\n" + markdown.strip() + "\n```"


def read_existing_hashes(output: Path) -> set[str]:
    if not output.exists():
        return set()

    text = output.read_text(encoding="utf-8")
    turns = parse_existing_turns(text)
    return {turn.fingerprint() for turn in turns}


def parse_existing_turns(markdown: str) -> list[Turn]:
    lines = markdown.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    turns: list[Turn] = []
    current: dict[str, Any] | None = None
    active_section: str | None = None
    active_lines: list[str] = []

    def finish_section() -> None:
        nonlocal active_section, active_lines
        if current is not None and active_section:
            current["sections"][active_section] = "\n".join(active_lines).strip()
        active_section = None
        active_lines = []

    def finish_turn() -> None:
        nonlocal current
        finish_section()
        if current is None:
            return
        sections = current["sections"]
        turns.append(
            Turn(
                user=sections.get("user", ""),
                agent=sections.get("agent", ""),
                title=current.get("title", ""),
                notes=sections.get("notes", ""),
                tags=sections.get("tags", ""),
            )
        )
        current = None

    for line in lines:
        turn_match = re.match(r"^##\s+Turn\s+(\d+)(?::\s*(.*))?\s*$", line, re.I)
        if turn_match:
            finish_turn()
            current = {"title": turn_match.group(2) or "", "sections": {}}
            continue

        if current is None:
            continue

        section_match = re.match(r"^###\s+(User|Agent|Notes|Tags)\s*$", line, re.I)
        if section_match:
            finish_section()
            active_section = section_match.group(1).lower()
            continue

        if active_section:
            active_lines.append(line)

    finish_turn()
    return turns


def load_state(state_file: Path | None) -> dict[str, Any]:
    if not state_file or not state_file.exists():
        return {"turn_hashes": []}
    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"turn_hashes": []}
    if not isinstance(data, dict):
        return {"turn_hashes": []}
    hashes = data.get("turn_hashes", [])
    if not isinstance(hashes, list):
        data["turn_hashes"] = []
    return data


def save_state(state_file: Path | None, state: dict[str, Any]) -> None:
    if not state_file:
        return
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
