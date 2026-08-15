#!/usr/bin/env python3
"""Render an owner-approved source clip into a 9:16 Reel."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def ass_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def ass_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}").replace("\n", "\\N")


def write_ass(path: Path, title: str, lines: list[str], duration: float = 60.0) -> None:
    usable = max(1, len(lines))
    segment = duration / usable
    rows = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1080",
        "PlayResY: 1920",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Hook,DejaVu Sans,64,&H00FFFFFF,&H00FFFFFF,&H00111111,&H99000000,1,0,0,0,100,100,0,0,1,4,1,8,48,48,80,1",
        "Style: Caption,DejaVu Sans,52,&H00FFFFFF,&H00FFFFFF,&H00111111,&H99000000,1,0,0,0,100,100,0,0,1,3,1,2,72,72,170,1",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        f"Dialogue: 0,{ass_time(0)},{ass_time(min(5.0, duration))},Hook,,0,0,0,,{ass_escape(title)}",
    ]
    for index, line in enumerate(lines):
        start = index * segment
        end = min(duration, (index + 1) * segment)
        rows.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Caption,,0,0,0,,{ass_escape(line)}")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--script", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--bgm", default="")
    args = parser.parse_args()

    source = Path(args.input)
    script_doc = json.loads(Path(args.script).read_text(encoding="utf-8"))
    script = script_doc["script"]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    if not source.exists():
        raise SystemExit(f"BLOCKED: source clip does not exist: {source}")
    if not Path(FONT).exists():
        raise SystemExit(f"BLOCKED: required font does not exist: {FONT}")

    with tempfile.TemporaryDirectory() as temp_dir:
        ass = Path(temp_dir) / "captions.ass"
        write_ass(ass, script["hook"], script["on_screen_lines"])
        video_filter = (
            "scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,setsar=1,"
            f"subtitles={ass.as_posix()}"
        )
        if args.bgm and Path(args.bgm).exists():
            cmd = [
                "ffmpeg", "-y", "-t", "60", "-i", str(source), "-stream_loop", "-1", "-i", args.bgm,
                "-filter_complex", f"[0:v]{video_filter}[v];[0:a]loudnorm=I=-14:TP=-1.5:LRA=11[a0];[1:a]volume=0.12,loudnorm=I=-22:TP=-2:LRA=11[a1];[a0][a1]amix=inputs=2:duration=first:dropout_transition=2[a]",
                "-map", "[v]", "-map", "[a]", "-shortest", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", str(output),
            ]
        else:
            cmd = [
                "ffmpeg", "-y", "-t", "60", "-i", str(source),
                "-vf", video_filter, "-map", "0:v:0", "-map", "0:a:0?", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", str(output),
            ]
        run(cmd)
    print(f"Rendered {output}")


if __name__ == "__main__":
    main()
