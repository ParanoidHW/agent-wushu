import tempfile
import unittest
from pathlib import Path

from tools.skill_converter import convert_single_skill, detect_platform, parse_skill_file


class SkillConverterTests(unittest.TestCase):
    def test_detects_multiword_claude_title(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "SKILL.md"
            skill_path.write_text(
                "---\n"
                "name: ppt-generator-pro\n"
                "description: Use this skill when building decks.\n"
                "---\n\n"
                "# PPT Generator Pro - Claude Code Skill\n\n"
                "Body\n",
                encoding="utf-8",
            )

            skill_data = parse_skill_file(skill_path)
            self.assertEqual(detect_platform(skill_data), "claude")

    def test_creates_missing_output_directory_for_single_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            skill_path = root / "SKILL.md"
            output_path = root / "nested" / "output" / "SKILL.md"
            skill_path.write_text(
                "---\n"
                "name: excalidraw-diagram\n"
                "description: Use this skill when creating diagrams.\n"
                "---\n\n"
                "# Excalidraw Diagram Creator\n\n"
                "Body\n",
                encoding="utf-8",
            )

            target_path, was_converted = convert_single_skill(skill_path, "codex", output_path)

            self.assertTrue(was_converted)
            self.assertEqual(target_path, output_path)
            self.assertTrue(output_path.exists())

    def test_generic_skill_is_not_misdetected_as_cursor(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "SKILL.md"
            skill_path.write_text(
                "---\n"
                "name: excalidraw-diagram\n"
                "description: Create diagrams.\n"
                "---\n\n"
                "# Excalidraw Diagram Creator\n\n"
                "Body\n",
                encoding="utf-8",
            )

            skill_data = parse_skill_file(skill_path)
            self.assertIsNone(detect_platform(skill_data))

    def test_cursor_description_strips_prefix_without_lstrip_corruption(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            skill_path = root / "SKILL.md"
            output_path = root / "cursor" / "SKILL.md"
            skill_path.write_text(
                "---\n"
                "name: demo\n"
                "description: Use when rendering UI previews.\n"
                "---\n\n"
                "# Demo Skill\n\n"
                "Body\n",
                encoding="utf-8",
            )

            convert_single_skill(skill_path, "cursor", output_path)
            converted = output_path.read_text(encoding="utf-8")

            self.assertIn("description: A Cursor AI skill for rendering UI previews.", converted)


if __name__ == "__main__":
    unittest.main()
