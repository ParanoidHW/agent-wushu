---
name: openrouter-icu-image
description: Generate or edit images synchronously through OpenRouter ICU's OpenAI-compatible image API. Use when the user asks Codex to create an image, produce visual assets, transform or edit local/reference images, upload non-image documents such as Markdown/PDF/text as image-generation context, use OpenRouter ICU, call https://openrouter.icu/v1/images/generations, call https://openrouter.icu/v1/images/edits, call https://openrouter.icu/v1/responses with input_file plus image_generation, parse streaming image responses, or save generated image files from OpenRouter ICU. Always run foreground/blocking and wait for final image files before continuing or replying.
---

# OpenRouter ICU Image

## Core Workflow

1. Check `OPENROUTER_ICU_API_KEY` before making network requests. If it is missing, ask the user for the key and do not call the API.
2. Keep API controls out of the image prompt. The prompt should describe only the visual goal: subject, scene, composition, materials, lighting, style, and explicit visual constraints.
3. Choose the endpoint:
   - Text-to-image: `/v1/images/generations`.
   - Local image editing or multi-image visual references: `/v1/images/edits`. Inputs must be image MIME types.
   - Non-image document inputs such as Markdown, plain text, CSV, or PDFs: `/v1/responses` with an `input_file` content part and an `image_generation` tool. This is the verified file-input path for "use this document as input" requests.
   - Do not rely on `/v1/files` for image-generation document inputs on OpenRouter ICU unless it is re-verified in the current session; it has returned `404` in practice. Do not send Markdown/text to `/v1/images/edits` as `image[]`; it is rejected as unsupported non-image MIME.
4. Set explicit request parameters. Defaults are `model=gpt-image-2`, `size=1024x1024`, `quality=high`, `output_format=png`, `stream=true`, and `partial_images=2`.
5. Run image generation synchronously. Do not background the command, detach the process, start a separate hidden terminal, or use fire-and-forget automation.
6. Wait until the CLI process exits and the final image file is written before continuing with dependent work or sending a final response. If a terminal tool returns a live session ID, poll that session until it exits; do not start unrelated work while image generation is still running.
7. Save outputs under a user-requested path when provided; otherwise use a clear local output path such as `output/openrouter-icu/<slug>.png`.
8. After generation, verify the file exists and render or show it when useful.

## Document Inputs

When the user explicitly wants a Markdown/PDF/text document uploaded as the image-generation input, use `/v1/responses`, not `/v1/images/edits` and not `/v1/files`.

Use this request shape:

- `input[].content[]` includes a concise visual instruction as `{"type":"input_text","text":"..."}`.
- The local document is base64 encoded into a data URL and passed as `{"type":"input_file","filename":"source.md","file_data":"data:text/markdown;base64,..."}`.
- `tools` includes `{"type":"image_generation","size":"1024x1024","quality":"high","output_format":"png"}`.
- Set `stream: true`, read SSE until `response.completed`, then decode the final image from `response.output[*].result` or an `image_generation_call` completed item. Partial images can appear as `partial_image_b64`.

Keep the prompt focused on the visual output. Do not paste the document contents into the prompt when the user asked for file upload; the document belongs in `input_file`.

Minimal Python pattern:

```python
file_data = "data:text/markdown;base64," + base64.b64encode(path.read_bytes()).decode("ascii")
payload = {
    "model": "gpt-5.4-mini",
    "input": [{
        "role": "user",
        "content": [
            {"type": "input_text", "text": "Create a clean technical infographic from the uploaded document."},
            {"type": "input_file", "filename": path.name, "file_data": file_data},
        ],
    }],
    "tools": [{"type": "image_generation", "size": "1024x1024", "quality": "high", "output_format": "png"}],
    "stream": True,
    "store": False,
}
```

If a high-resolution Responses request stalls, retry at `1024x1024` first. Streaming keepalive events are normal; keep polling until `response.completed` or an error/failed event.

## Preferred CLI

Use `scripts/openrouter_icu_image.py` for most tasks. It uses only the Python 3 standard library, handles streaming SSE, validates core parameters, avoids accidental requests without an API key, and writes decoded images only after image payload fields are present.

The CLI is synchronous by default: it does not exit until the HTTP response has completed, SSE events have been parsed, and final image files have been decoded and written. Treat a nonzero exit code as a failed generation and do not claim success.

Run the script from the skill directory or pass the script path appropriate for the installed location. Use a Python 3 launcher:

- macOS/Linux: `python3 scripts/openrouter_icu_image.py`
- Windows PowerShell/CMD: `py -3 scripts\openrouter_icu_image.py`
- Windows without the Python launcher: `python scripts\openrouter_icu_image.py` when `python` points to Python 3

Examples:

```bash
python3 scripts/openrouter_icu_image.py generate \
  --prompt "A clean product photo of a white ceramic coffee mug on a wooden desk, soft natural light" \
  --output output/openrouter-icu/mug.png
```

Windows equivalent:

```powershell
py -3 scripts\openrouter_icu_image.py generate `
  --prompt "A clean product photo of a white ceramic coffee mug on a wooden desk, soft natural light" `
  --output output\openrouter-icu\mug.png
```

```bash
python3 scripts/openrouter_icu_image.py edit \
  --image input.png \
  --prompt "Change the background to a clean modern office while preserving the subject, clothing, pose, and facial features" \
  --output output/openrouter-icu/office.png
```

```bash
python3 scripts/openrouter_icu_image.py edit \
  --image product.png \
  --image background-reference.png \
  --prompt "Create a premium product photo using the product from the first image and the environment style from the second image" \
  --size 1536x1024 \
  --quality high \
  --output output/openrouter-icu/product.png
```

```bash
python3 scripts/openrouter_icu_image.py edit \
  --image-url https://example.com/input.png \
  --prompt "Create a clean product photo using this reference image" \
  --output output/openrouter-icu/from-url.png
```

Only after re-verifying that `/v1/files` is available for the current OpenRouter ICU account, reusable server-side image references may use:

```bash
python3 scripts/openrouter_icu_image.py upload input.png --purpose vision

python3 scripts/openrouter_icu_image.py edit \
  --file-id file_abc123 \
  --prompt "Change the background while preserving the subject" \
  --output output/openrouter-icu/from-file-id.png
```

Use `--dry-run` to inspect the request shape without contacting the API.

For image inputs, prefer the simplest accepted form:

- Use `edit --image path.png` for local image files. This sends multipart `image[]` directly to `/v1/images/edits`; no separate upload is needed.
- Use `edit --image-url https://...` for remote images that the API can fetch.
- Use `upload path.png --purpose vision` only for reusable image references after `/v1/files` has been re-verified as available. It is not the path for Markdown/PDF/text document inputs.
- Do not put local file paths or URLs inside the image prompt. Put them in `--image`, `--image-url`, or `--file-id`.

CLI flags use hyphenated names while the API payload uses snake_case. The script also accepts the snake_case aliases for API-shaped options:

| CLI flag | API payload field |
|---|---|
| `upload FILE --purpose vision` | `POST /v1/files` multipart `file` + `purpose`; re-verify availability first |
| `--output-format` / `--output_format` | `output_format` |
| `--output-compression` / `--output_compression` | `output_compression` |
| `--stream`, `--stream true`, `--stream false` | `stream` |
| `--no-stream` / `--no_stream` | `stream=false` |
| `--partial-images` / `--partial_images` | `partial_images` |
| `--image` / `--image-file` | multipart `image[]` |
| `--file-id` / `--file_id` | `images[].file_id` |
| `--image-url` / `--image_url` | `images[].image_url` |
| `--base-url` / `--base_url` | request base; accepts `https://openrouter.icu` or `https://openrouter.icu/v1` |

## Parameter Rules

- Always set `size`, `quality`, and `output_format` explicitly.
- Use `quality=high` unless the user specifies otherwise.
- Use `output_format=png` unless the user asks for `jpeg` or `webp`.
- Use `stream=true` and `partial_images=2` by default for visible progress and robust final-event handling.
- When using `--stream false`, `--no-stream`, or `--no_stream`, omit `partial_images` from the API payload.
- For custom sizes, require `WIDTHxHEIGHT`, dimensions divisible by 16, aspect ratio between `1:3` and `3:1`, and no more pixels than `3840x2160`.
- Avoid sizes above `2560x1440` unless the user needs high-resolution output.

## Error Handling

- `400`: print full error JSON, fix parameters, and do not retry unchanged.
- `401`: check `OPENROUTER_ICU_API_KEY`; if absent or invalid, ask the user for a valid key.
- `403` / `404`: print full error JSON and check model, file IDs, image URLs, and permissions.
- `408` / `409` / `429` / `5xx`: retry with bounded exponential backoff when appropriate.
- Preserve debugging context: HTTP status, `x-request-id`, model, size, quality, output format, streaming mode, and last SSE event type.

## References

Read `references/api.md` when you need complete endpoint parameters, curl examples, SDK examples, SSE parsing details, or troubleshooting tables.
