#!/usr/bin/env python3
"""Fail-closed technical validation for a rendered Reel."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def probe(path: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: validate_reel.py output.mp4")
    path = Path(sys.argv[1])
    if not path.exists():
        raise SystemExit(f"BLOCKED: missing output file {path}")
    data = probe(path)
    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    errors: list[str] = []
    if not video:
        errors.append("missing video stream")
    else:
        if video.get("codec_name") != "h264":
            errors.append(f"video codec must be h264, got {video.get('codec_name')}")
        if video.get("width") != 1080 or video.get("height") != 1920:
            errors.append(f"video must be 1080x1920, got {video.get('width')}x{video.get('height')}")
        duration = float(video.get("duration") or data.get("format", {}).get("duration") or 0)
        if duration < 3 or duration > 90:
            errors.append(f"duration must be 3-90 seconds, got {duration:.2f}")
    if not audio:
        errors.append("missing audio stream")
    else:
        if audio.get("codec_name") != "aac":
            errors.append(f"audio codec must be aac, got {audio.get('codec_name')}")
        if int(audio.get("sample_rate") or 0) != 48000:
            errors.append(f"audio sample rate must be 48000, got {audio.get('sample_rate')}")
    if errors:
        raise SystemExit("BLOCKED: " + "; ".join(errors))
    print(f"PASS: {path} meets Meta-friendly technical constraints")


if __name__ == "__main__":
    main()
