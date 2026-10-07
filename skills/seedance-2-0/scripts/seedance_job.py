"""Offline request builder plus explicit submit/status/download commands.

No API call occurs unless the operator passes --submit, --status, or
--download. The request ID is saved before any later status operation.
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

BASE_URL = "https://argolink.io/v1"
USER_AGENT = "seedance-2-0-skill-codex/1.0"
MODELS = {"seedance-2.0-mini", "seedance-2.0-fast", "seedance-2.0"}
RATIOS = {"adaptive", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16"}
MODEL_LIMITS = {
    "seedance-2.0-mini": {"resolutions": {"480p", "720p"}, "images": 9, "videos": 3, "audios": 3, "assets": 15},
    "seedance-2.0-fast": {"resolutions": {"480p", "720p"}, "images": 9, "videos": 3, "audios": 3, "assets": 15},
    "seedance-2.0": {"resolutions": {"480p", "720p", "1080p", "4k"}, "images": 9, "videos": 3, "audios": 3, "assets": 15},
}
STATUSES = {"pending", "done", "failed", "expired"}


class SeedanceError(RuntimeError):
    pass


def https(value: str, field: str) -> str:
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"{field} must be an https URL")
    return value


def urls(values: Iterable[str], field: str) -> List[Dict[str, str]]:
    return [{"url": https(value, f"{field}[{index}]")} for index, value in enumerate(values)]


def build(
    model: str,
    prompt: str,
    duration: int = 5,
    resolution: str = "720p",
    aspect_ratio: str = "16:9",
    *,
    mode: str = "text",
    generate_audio: bool = True,
    start_image: Optional[str] = None,
    end_image: Optional[str] = None,
    reference_images: Optional[List[str]] = None,
    reference_videos: Optional[List[str]] = None,
    reference_audios: Optional[List[str]] = None,
) -> Dict[str, Any]:
    if model not in MODELS:
        raise ValueError(f"unknown Seedance 2.0 variant: {model}")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt is required")
    if isinstance(duration, bool) or not isinstance(duration, int) or not 4 <= duration <= 15:
        raise ValueError("duration must be an integer from 4 through 15")
    limits = MODEL_LIMITS[model]
    if resolution not in limits["resolutions"]:
        raise ValueError(f"{model} supports {', '.join(sorted(limits['resolutions']))}")
    if aspect_ratio not in RATIOS:
        raise ValueError("aspect_ratio must be adaptive or one of the six fixed ratios")
    if mode not in {"text", "start_image", "first_last_frames", "multimodal_reference"}:
        raise ValueError("mode must be text, start_image, first_last_frames, or multimodal_reference")
    images = reference_images or []
    videos = reference_videos or []
    audios = reference_audios or []
    if len(images) > limits["images"] or len(videos) > limits["videos"] or len(audios) > limits["audios"]:
        raise ValueError("reference limits are 9 images, 3 videos, and 3 audio clips")
    if len(images) + len(videos) + len(audios) > limits["assets"]:
        raise ValueError("at most 15 reference assets are allowed")
    if mode == "text":
        if start_image or end_image or any((images, videos, audios)):
            raise ValueError("text mode cannot include media")
        if aspect_ratio == "adaptive":
            raise ValueError("text mode needs a fixed aspect ratio")
    elif mode == "start_image":
        if not start_image or end_image or any((images, videos, audios)):
            raise ValueError("start_image mode needs exactly one start_image")
    elif mode == "first_last_frames":
        if not start_image or not end_image or any((images, videos, audios)):
            raise ValueError("first_last_frames needs start_image and end_image only")
    else:
        if start_image or end_image or not any((images, videos, audios)):
            raise ValueError("multimodal_reference needs reference lists only")
        if aspect_ratio == "adaptive":
            raise ValueError("reference mode uses a fixed ratio for Seedance 2.0")
    body: Dict[str, Any] = {
        "model": model, "prompt": prompt, "duration": duration,
        "resolution": resolution, "aspect_ratio": aspect_ratio,
        "generate_audio": bool(generate_audio),
    }
    if start_image:
        body["start_image"] = {"url": https(start_image, "start_image")}
    if end_image:
        body["end_image"] = {"url": https(end_image, "end_image")}
    for name, values in (("reference_images", images), ("reference_videos", videos), ("reference_audios", audios)):
        if values:
            body[name] = urls(values, name)
    return body


class API:
    def __init__(self, key: Optional[str] = None, base: Optional[str] = None, timeout: float = 90.0):
        self.key = key or os.environ.get("SEEDANCE_API_KEY")
        self.base = (base or os.environ.get("SEEDANCE_BASE_URL") or BASE_URL).rstrip("/")
        self.timeout = timeout

    def call(self, method: str, path: str, body: Optional[Dict[str, Any]] = None) -> Any:
        if not self.key:
            raise SeedanceError("set SEEDANCE_API_KEY in the host environment")
        data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
        headers = {"Authorization": f"Bearer {self.key}", "User-Agent": USER_AGENT}
        if data is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(self.base + path, data=data, method=method, headers=headers)
        try:
            response = urllib.request.urlopen(request, timeout=self.timeout)
            raw = response.read()
            response.close()
        except urllib.error.HTTPError as error:
            detail = error.read(4096).decode("utf-8", errors="replace")
            raise SeedanceError(f"{method} {path} HTTP {error.code}: {detail[:300]}") from None
        if path.endswith("/content"):
            return raw
        try:
            result = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise SeedanceError(f"{method} {path} returned invalid JSON") from error
        if not isinstance(result, dict):
            raise SeedanceError(f"{method} {path} returned a non-object")
        return result

    def submit(self, body: Dict[str, Any]) -> str:
        result = self.call("POST", "/videos/generations", body)
        request_id = result.get("request_id")
        if not isinstance(request_id, str) or not request_id:
            raise SeedanceError("response did not contain request_id")
        return request_id

    def status(self, request_id: str) -> Dict[str, Any]:
        result = self.call("GET", f"/videos/{request_id}")
        if result.get("status") not in STATUSES:
            raise SeedanceError(f"unknown status {result.get('status')!r}")
        return result

    def download(self, request_id: str, output: Path) -> None:
        if output.exists():
            raise FileExistsError(str(output))
        output.parent.mkdir(parents=True, exist_ok=True)
        raw = self.call("GET", f"/videos/{request_id}/content")
        with tempfile.NamedTemporaryFile(dir=output.parent, prefix=".partial-", delete=False) as handle:
            temp = Path(handle.name)
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temp, output)
        except FileExistsError:
            raise
        finally:
            temp.unlink(missing_ok=True)


def save(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, prefix=".state-", delete=False) as handle:
        temp = Path(handle.name)
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(temp, path)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Seedance 2.0 Codex skill helper")
    parser.add_argument("--model", default="seedance-2.0-mini")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--duration", type=int, default=5)
    parser.add_argument("--resolution", default="720p")
    parser.add_argument("--aspect-ratio", default="16:9")
    parser.add_argument("--mode", default="text")
    parser.add_argument("--start-image")
    parser.add_argument("--end-image")
    parser.add_argument("--reference-image", action="append", default=[])
    parser.add_argument("--reference-video", action="append", default=[])
    parser.add_argument("--reference-audio", action="append", default=[])
    parser.add_argument("--state", type=Path, default=Path("seedance-job.json"))
    parser.add_argument("--output", type=Path, default=Path("output.mp4"))
    parser.add_argument("--print-json", action="store_true")
    parser.add_argument("--submit", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args(argv)
    body = build(
        args.model, args.prompt, args.duration, args.resolution, args.aspect_ratio,
        mode=args.mode, start_image=args.start_image, end_image=args.end_image,
        reference_images=args.reference_image, reference_videos=args.reference_video,
        reference_audios=args.reference_audio,
    )
    if args.print_json or not (args.submit or args.status or args.download):
        print(json.dumps(body, ensure_ascii=False, indent=2))
        return 0
    api = API()
    state = json.loads(args.state.read_text()) if args.state.exists() else {"body": body}
    if args.submit:
        if state.get("request_id"):
            raise SeedanceError("state already has request_id; use --status instead of submitting again")
        state["request_id"] = api.submit(body)
        state["status"] = "pending"
        state["body"] = body
        save(args.state, state)
        print(json.dumps(state, ensure_ascii=False))
        return 0
    if not state.get("request_id"):
        raise SeedanceError("state file has no request_id")
    if args.status:
        state["provider"] = api.status(state["request_id"])
        state["status"] = state["provider"]["status"]
        save(args.state, state)
        print(json.dumps(state["provider"], ensure_ascii=False))
        return 0
    if state.get("status") != "done":
        raise SeedanceError("download requires state status done; call --status first")
    api.download(state["request_id"], args.output)
    state["output"] = str(args.output)
    save(args.state, state)
    print(str(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
