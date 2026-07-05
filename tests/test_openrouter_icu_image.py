import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "skills/openrouter-icu-image/scripts/openrouter_icu_image.py"


def load_module():
    spec = importlib.util.spec_from_file_location("openrouter_icu_image", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class OpenRouterIcuImageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def parse_args(self, *args):
        return self.module.build_parser().parse_args(list(args))

    def test_edit_local_image_uses_multipart_image_field(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image = Path(tmpdir) / "input.png"
            image.write_bytes(b"fake image")

            args = self.parse_args(
                "edit",
                "--image",
                str(image),
                "--prompt",
                "test prompt",
                "--output",
                str(Path(tmpdir) / "out.png"),
            )
            url, body, headers = self.module.build_request(args, "test-key")

        self.assertEqual(url, "https://openrouter.icu/v1/images/edits")
        self.assertTrue(headers["Content-Type"].startswith("multipart/form-data; boundary="))
        self.assertIn(b'name="image[]"', body)
        self.assertIn(b'filename="input.png"', body)
        self.assertIn(b"name=\"prompt\"", body)

    def test_edit_image_url_uses_json_images_array(self):
        args = self.parse_args(
            "edit",
            "--image-url",
            "https://example.com/input.png",
            "--prompt",
            "test prompt",
            "--output",
            "out.png",
        )
        url, body, headers = self.module.build_request(args, "test-key")
        payload = json.loads(body.decode("utf-8"))

        self.assertEqual(url, "https://openrouter.icu/v1/images/edits")
        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertEqual(payload["images"], [{"image_url": "https://example.com/input.png"}])

    def test_edit_file_id_uses_json_images_array(self):
        args = self.parse_args(
            "edit",
            "--file-id",
            "file_abc123",
            "--prompt",
            "test prompt",
            "--output",
            "out.png",
        )
        _, body, headers = self.module.build_request(args, "test-key")
        payload = json.loads(body.decode("utf-8"))

        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertEqual(payload["images"], [{"file_id": "file_abc123"}])

    def test_default_quality_is_high(self):
        args = self.parse_args(
            "generate",
            "--prompt",
            "test prompt",
            "--output",
            "out.png",
        )
        _, body, _ = self.module.build_request(args, "test-key")
        payload = json.loads(body.decode("utf-8"))

        self.assertEqual(payload["quality"], "high")

    def test_upload_uses_files_endpoint_and_multipart_file_field(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image = Path(tmpdir) / "input.png"
            image.write_bytes(b"fake image")

            args = self.parse_args("upload", str(image))
            url, body, headers = self.module.build_upload_request(args, "test-key")

        self.assertEqual(url, "https://openrouter.icu/v1/files")
        self.assertTrue(headers["Content-Type"].startswith("multipart/form-data; boundary="))
        self.assertIn(b'name="file"', body)
        self.assertIn(b'filename="input.png"', body)
        self.assertIn(b'name="purpose"', body)
        self.assertIn(b"vision", body)

    def test_no_stream_omits_partial_images(self):
        args = self.parse_args(
            "edit",
            "--image-url",
            "https://example.com/input.png",
            "--prompt",
            "test prompt",
            "--output",
            "out.png",
            "--no-stream",
        )
        _, body, _ = self.module.build_request(args, "test-key")
        payload = json.loads(body.decode("utf-8"))

        self.assertFalse(payload["stream"])
        self.assertNotIn("partial_images", payload)

    def test_upload_response_normalizes_id_to_file_id(self):
        result = self.module.parse_upload_response(b'{"id":"file_abc123","object":"file"}')

        self.assertEqual(result["id"], "file_abc123")
        self.assertEqual(result["file_id"], "file_abc123")

    def test_upload_response_keeps_existing_file_id(self):
        result = self.module.parse_upload_response(b'{"file_id":"file_abc123"}')

        self.assertEqual(result["file_id"], "file_abc123")

    def test_responses_doc_uses_input_file_and_image_generation_tool(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            document = Path(tmpdir) / "input.md"
            document.write_text("# Input\n", encoding="utf-8")

            args = self.parse_args(
                "responses-doc",
                "--input-file",
                str(document),
                "--prompt",
                "test prompt",
                "--n",
                "3",
                "--output",
                str(Path(tmpdir) / "out.png"),
            )
            url, body, headers = self.module.build_responses_doc_request(args, "test-key")
            payload = json.loads(body.decode("utf-8"))

        self.assertEqual(url, "https://openrouter.icu/v1/responses")
        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertEqual(headers["Accept"], "text/event-stream")
        self.assertEqual(payload["model"], "gpt-5.5-medium")
        self.assertEqual(payload["tools"], [{
            "type": "image_generation",
            "size": "1024x1024",
            "quality": "high",
            "output_format": "png",
            "n": 3,
        }])
        self.assertEqual(payload["input"][0]["content"][0], {"type": "input_text", "text": "test prompt"})
        file_part = payload["input"][0]["content"][1]
        self.assertEqual(file_part["type"], "input_file")
        self.assertEqual(file_part["filename"], "input.md")
        self.assertTrue(file_part["file_data"].startswith("data:text/markdown;base64,"))


if __name__ == "__main__":
    unittest.main()
