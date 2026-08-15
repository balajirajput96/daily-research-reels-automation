#!/usr/bin/env python3
"""Publish a rendered Reel through official Meta APIs.

No browser-cookie automation is used. Missing credentials or destination IDs
cause a hard failure before any publish request is attempted.
"""
from __future__ import annotations

import argparse
import os
import time
from pathlib import Path
from typing import Any

import requests

API_VERSION = os.environ.get("META_API_VERSION", "v26.0")


def require(*names: str) -> dict[str, str]:
    values = {name: os.environ.get(name, "") for name in names}
    missing = [name for name, value in values.items() if not value]
    if missing:
        raise SystemExit("BLOCKED: missing required secrets/variables: " + ", ".join(missing))
    return values


def publish_instagram(video_url: str, caption: str) -> dict[str, Any]:
    values = require("META_IG_ACCESS_TOKEN", "META_IG_USER_ID")
    base = f"https://graph.instagram.com/{API_VERSION}"
    headers = {"Authorization": f"Bearer {values['META_IG_ACCESS_TOKEN']}"}
    create = requests.post(
        f"{base}/{values['META_IG_USER_ID']}/media",
        headers=headers,
        data={"media_type": "REELS", "video_url": video_url, "caption": caption, "is_ai_generated": "true"},
        timeout=60,
    )
    create.raise_for_status()
    container_id = create.json().get("id")
    if not container_id:
        raise RuntimeError("Instagram did not return a media container ID")
    for _ in range(10):
        status = requests.get(f"{base}/{container_id}", headers=headers, params={"fields": "status_code"}, timeout=30)
        status.raise_for_status()
        code = status.json().get("status_code")
        if code == "FINISHED":
            break
        if code == "ERROR":
            raise RuntimeError("Instagram media container entered ERROR state")
        time.sleep(30)
    else:
        raise RuntimeError("Instagram media container did not finish within the retry window")
    publish = requests.post(
        f"{base}/{values['META_IG_USER_ID']}/media_publish",
        headers=headers,
        data={"creation_id": container_id},
        timeout=60,
    )
    publish.raise_for_status()
    return {"platform": "instagram", "media_id": publish.json().get("id"), "container_id": container_id}


def publish_facebook_page(video: Path, description: str) -> dict[str, Any]:
    values = require("META_FB_PAGE_ACCESS_TOKEN", "META_FB_PAGE_ID")
    start = requests.post(
        f"https://graph.facebook.com/{API_VERSION}/{values['META_FB_PAGE_ID']}/video_reels",
        data={"upload_phase": "start", "access_token": values["META_FB_PAGE_ACCESS_TOKEN"]},
        timeout=60,
    )
    start.raise_for_status()
    payload = start.json()
    video_id = payload.get("video_id")
    upload_url = payload.get("upload_url")
    if not video_id or not upload_url:
        raise RuntimeError("Facebook did not return an upload session")
    size = video.stat().st_size
    with video.open("rb") as handle:
        upload = requests.post(
            upload_url,
            headers={
                "Authorization": f"OAuth {values['META_FB_PAGE_ACCESS_TOKEN']}",
                "offset": "0",
                "file_size": str(size),
                "Content-Type": "application/octet-stream",
            },
            data=handle,
            timeout=300,
        )
    upload.raise_for_status()
    finish = requests.post(
        f"https://graph.facebook.com/{API_VERSION}/{values['META_FB_PAGE_ID']}/video_reels",
        data={
            "access_token": values["META_FB_PAGE_ACCESS_TOKEN"],
            "video_id": video_id,
            "upload_phase": "finish",
            "video_state": "PUBLISHED",
            "description": description,
        },
        timeout=60,
    )
    finish.raise_for_status()
    return {"platform": "facebook_page", "video_id": video_id, "response": finish.json()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True)
    parser.add_argument("--caption", required=True)
    parser.add_argument("--instagram-url", default=os.environ.get("PUBLIC_MEDIA_URL", ""))
    parser.add_argument("--platforms", default="instagram,facebook_page")
    args = parser.parse_args()
    video = Path(args.video)
    if not video.exists():
        raise SystemExit(f"BLOCKED: missing rendered video {video}")
    platforms = {item.strip() for item in args.platforms.split(",") if item.strip()}
    results: list[dict[str, Any]] = []
    if "instagram" in platforms:
        if not args.instagram_url:
            raise SystemExit("BLOCKED: Instagram requires PUBLIC_MEDIA_URL or --instagram-url")
        results.append(publish_instagram(args.instagram_url, args.caption))
    if "facebook_page" in platforms:
        results.append(publish_facebook_page(video, args.caption))
    print({"published": results})


if __name__ == "__main__":
    main()
