import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RECORDER_PATH = REPO_ROOT / "hooks" / "hooks" / "record_interaction.py"


spec = importlib.util.spec_from_file_location("record_interaction", RECORDER_PATH)
record_interaction = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(record_interaction)


class RecordInteractionTests(unittest.TestCase):
    def test_pre_tool_use_records_task_prompt(self):
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Task",
            "tool_input": {
                "description": "Inspect hooks",
                "prompt": "Find missing MCP prompt recording.",
            },
            "session_id": "session-1",
            "tool_call_id": "call-1",
        }

        turns = record_interaction.turns_from_payload(payload)

        self.assertEqual(len(turns), 1)
        self.assertEqual(turns[0].user, "Find missing MCP prompt recording.")
        self.assertEqual(turns[0].agent, "Tool call: `Task`")
        self.assertIn("tool-prompt", turns[0].tags)

    def test_pre_tool_use_records_mcp_query(self):
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "mcp__search__papers",
            "tool_input": {"query": "diffusion draft model"},
        }

        turns = record_interaction.turns_from_payload(payload)

        self.assertEqual(len(turns), 1)
        self.assertEqual(turns[0].user, "diffusion draft model")
        self.assertIn("mcp", turns[0].tags)

    def test_pre_tool_use_ignores_command_without_prompt(self):
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "functions.exec_command",
            "tool_input": {"cmd": "rg prompt hooks"},
        }

        self.assertEqual(record_interaction.turns_from_payload(payload), [])

    def test_tool_prompt_records_are_written_once_for_same_payload(self):
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "mcp__image__generate",
            "tool_input": {"prompt": "A clean diagram of the hook flow"},
            "tool_call_id": "call-1",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output = root / "history.md"
            state = root / "state.json"
            turns = record_interaction.turns_from_payload(payload)

            first = record_interaction.record_turns(
                turns=turns,
                output=output,
                state_file=state,
                title="Test",
                topic="",
                user_name="User",
                agent_name="Agent",
                source="hook",
            )
            second = record_interaction.record_turns(
                turns=turns,
                output=output,
                state_file=state,
                title="Test",
                topic="",
                user_name="User",
                agent_name="Agent",
                source="hook",
            )

            self.assertEqual(first, 1)
            self.assertEqual(second, 0)
            self.assertEqual(output.read_text(encoding="utf-8").count("## Turn"), 1)
            saved_state = json.loads(state.read_text(encoding="utf-8"))
            self.assertEqual(len(saved_state["turn_hashes"]), 1)

    def test_include_process_adds_public_transcript_updates_to_notes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            transcript = Path(tmpdir) / "session.jsonl"
            lines = [
                {"type": "session_meta", "payload": {"session_id": "session-1"}},
                {
                    "type": "event_msg",
                    "payload": {"type": "user_message", "message": "Please fix the hook."},
                },
                {
                    "type": "event_msg",
                    "payload": {
                        "type": "agent_message",
                        "phase": "commentary",
                        "message": "I will inspect the recorder and hook config.",
                    },
                },
                {
                    "type": "response_item",
                    "payload": {
                        "type": "reasoning",
                        "summary": [
                            {"type": "summary_text", "text": "Need to preserve public summaries only."}
                        ],
                        "encrypted_content": "do-not-record",
                    },
                },
                {
                    "type": "response_item",
                    "payload": {
                        "type": "message",
                        "role": "assistant",
                        "phase": "final",
                        "content": [{"type": "output_text", "text": "Fixed."}],
                    },
                },
            ]
            transcript.write_text(
                "\n".join(json.dumps(line, ensure_ascii=False) for line in lines) + "\n",
                encoding="utf-8",
            )

            turns = record_interaction.turns_from_codex_transcript(transcript, include_process=True)

            self.assertEqual(len(turns), 1)
            self.assertEqual(turns[0].agent, "Fixed.")
            self.assertIn("Key process:", turns[0].notes)
            self.assertIn("I will inspect the recorder and hook config.", turns[0].notes)
            self.assertIn("Need to preserve public summaries only.", turns[0].notes)
            self.assertNotIn("do-not-record", turns[0].notes)

    def test_process_notes_are_omitted_by_default(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            transcript = Path(tmpdir) / "session.jsonl"
            lines = [
                {"type": "session_meta", "payload": {"session_id": "session-1"}},
                {
                    "type": "event_msg",
                    "payload": {"type": "user_message", "message": "Please fix the hook."},
                },
                {
                    "type": "event_msg",
                    "payload": {
                        "type": "agent_message",
                        "phase": "commentary",
                        "message": "I will inspect the recorder and hook config.",
                    },
                },
                {
                    "type": "response_item",
                    "payload": {
                        "type": "message",
                        "role": "assistant",
                        "phase": "final",
                        "content": [{"type": "output_text", "text": "Fixed."}],
                    },
                },
            ]
            transcript.write_text(
                "\n".join(json.dumps(line, ensure_ascii=False) for line in lines) + "\n",
                encoding="utf-8",
            )

            turns = record_interaction.turns_from_codex_transcript(transcript)

            self.assertEqual(len(turns), 1)
            self.assertNotIn("Key process:", turns[0].notes)

    def test_process_notes_deduplicate_and_cap_public_updates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            transcript = Path(tmpdir) / "session.jsonl"
            lines = [
                {"type": "session_meta", "payload": {"session_id": "session-1"}},
                {
                    "type": "event_msg",
                    "payload": {"type": "user_message", "message": "Track milestones."},
                },
            ]
            lines.extend(
                {
                    "type": "event_msg",
                    "payload": {
                        "type": "agent_message",
                        "phase": "commentary",
                        "message": f"Checkpoint {index}",
                    },
                }
                for index in range(12)
            )
            lines.extend(
                [
                    {
                        "type": "event_msg",
                        "payload": {
                            "type": "agent_message",
                            "phase": "commentary",
                            "message": "Checkpoint 0",
                        },
                    },
                    {
                        "type": "event_msg",
                        "payload": {
                            "type": "agent_message",
                            "phase": "commentary",
                            "message": "Checkpoint overflow",
                        },
                    },
                    {
                        "type": "response_item",
                        "payload": {
                            "type": "function_call",
                            "arguments": "sensitive tool output",
                        },
                    },
                    {
                        "type": "response_item",
                        "payload": {
                            "type": "message",
                            "role": "assistant",
                            "phase": "final",
                            "content": [{"type": "output_text", "text": "Done."}],
                        },
                    },
                ]
            )
            transcript.write_text(
                "\n".join(json.dumps(line, ensure_ascii=False) for line in lines) + "\n",
                encoding="utf-8",
            )

            turns = record_interaction.turns_from_codex_transcript(transcript, include_process=True)

            self.assertEqual(len(turns), 1)
            self.assertEqual(turns[0].notes.count("Checkpoint 0"), 1)
            self.assertIn("12. Update: Checkpoint 11", turns[0].notes)
            self.assertNotIn("Checkpoint overflow", turns[0].notes)
            self.assertIn("... 1 more process update(s) omitted.", turns[0].notes)
            self.assertNotIn("sensitive tool output", turns[0].notes)

    def test_process_entry_text_is_capped(self):
        text = record_interaction.compact_process_text("x" * 1201)

        self.assertEqual(len(text), 1200)
        self.assertTrue(text.endswith("..."))

    def test_subagent_stop_records_public_result(self):
        payload = {
            "hook_event_name": "SubagentStop",
            "agent_id": "agent-42",
            "agent_type": "reviewer",
            "task": "Review the recorder edge cases.",
            "last_assistant_message": "Found and documented the edge cases.",
            "session_id": "parent-session",
            "turn_id": "turn-3",
        }

        turns = record_interaction.turns_from_payload(payload, include_process=True)

        self.assertEqual(len(turns), 1)
        self.assertEqual(turns[0].title, "Subagent reviewer completed")
        self.assertIn("Review the recorder edge cases.", turns[0].user)
        self.assertEqual(turns[0].agent, "Found and documented the edge cases.")
        self.assertIn("agent_id: agent-42", turns[0].notes)
        self.assertIn("subagent", turns[0].tags)

    def test_pre_compact_records_latest_public_context(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            transcript = Path(tmpdir) / "session.jsonl"
            lines = [
                {"type": "session_meta", "payload": {"session_id": "session-1"}},
                {
                    "type": "event_msg",
                    "payload": {"type": "user_message", "message": "Continue the recorder work."},
                },
                {
                    "type": "event_msg",
                    "payload": {
                        "type": "agent_message",
                        "phase": "commentary",
                        "message": "I have synchronized the hook configuration.",
                    },
                },
                {
                    "type": "response_item",
                    "payload": {
                        "type": "message",
                        "role": "assistant",
                        "phase": "final",
                        "content": [{"type": "output_text", "text": "Synchronization complete."}],
                    },
                },
            ]
            transcript.write_text(
                "\n".join(json.dumps(line, ensure_ascii=False) for line in lines) + "\n",
                encoding="utf-8",
            )
            payload = {
                "hook_event_name": "PreCompact",
                "trigger": "auto",
                "transcript_path": str(transcript),
                "session_id": "session-1",
            }

            turns = record_interaction.turns_from_payload(payload, include_process=True)

            self.assertEqual(len(turns), 1)
            self.assertEqual(turns[0].title, "Context compact (auto)")
            self.assertEqual(turns[0].agent, "Synchronization complete.")
            self.assertIn("Last user request:", turns[0].notes)
            self.assertIn("Continue the recorder work.", turns[0].notes)
            self.assertIn("Key process:\n1. Update:", turns[0].notes)
            self.assertIn("compact", turns[0].tags)


if __name__ == "__main__":
    unittest.main()
