import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

import wushu


class WushuTests(unittest.TestCase):
    def test_status_uses_target_path_for_existing_submodule_layout(self):
        registry = yaml.safe_load((wushu.REPO_ROOT / "registry.yaml").read_text(encoding="utf-8"))
        module = next(m for m in registry["modules"] if m["name"] == "anthropics-pptx-skill")

        self.assertEqual(
            wushu.get_module_path(module, registry),
            wushu.REPO_ROOT / "skills/anthropics-pptx",
        )
        self.assertTrue(wushu.is_git_checkout(wushu.get_module_path(module, registry)))

    def test_clone_sparse_supports_file_patterns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source = root / "source"
            target = root / "clone"
            source.mkdir()

            subprocess.run(["git", "init", "-b", "main"], cwd=source, check=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=source, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=source, check=True)
            (source / "README.md").write_text("hello\n", encoding="utf-8")
            (source / "docs").mkdir()
            (source / "docs" / "guide.md").write_text("guide\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=source, check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=source, check=True)

            registry = {
                "categories": {"skills": {"path": "skills"}},
                "modules": [],
            }
            module = {
                "name": "local-demo",
                "repo": str(source),
                "category": "skills",
                "branch": "main",
                "target_path": str(target),
                "sparse_checkout": ["README.md"],
            }

            wushu.clone_module(module, registry, shallow=True)

            self.assertTrue((target / "README.md").exists())
            self.assertFalse((target / "docs" / "guide.md").exists())
            self.assertTrue(wushu.is_git_checkout(target))


if __name__ == "__main__":
    unittest.main()
