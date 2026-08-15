# Daily Research Reels Automation

This private repository is a **fail-closed daily production pipeline** for one approximately 60-second, 9:16 research-based Reel per day. It is designed for the owner's supplied face and voice only, Hinglish delivery, visible AI disclosure, and a general-education medical disclaimer.

The workflow can research a topic, generate a script, render a vertical MP4 with FFmpeg, validate the output, and publish through Meta's official APIs when the required account permissions and secrets are configured. It never stores access tokens, raw face/voice media, or private source URLs in Git.

## What is implemented

The repository contains a scheduled GitHub Actions workflow, a structured topic queue, a script-generation adapter, deterministic video rendering and validation, and separate Instagram and Facebook Page publishing adapters. If a required credential, source clip, public media URL, destination ID, or safety check is missing, the workflow produces a blocker report and does not publish.

## One-time setup

Create the following GitHub Actions Secrets in the repository settings. Secret values must be added by the account owner; they are intentionally not included in this repository.

| Secret or variable | Purpose |
|---|---|
| `GEMINI_API_KEY` | Official model API credential for script generation |
| `GEMINI_MODEL` | Approved Gemini model name |
| `META_IG_ACCESS_TOKEN` | Instagram professional-account publishing token |
| `META_IG_USER_ID` | Instagram professional-account ID |
| `META_FB_PAGE_ACCESS_TOKEN` | Facebook Page publishing token |
| `META_FB_PAGE_ID` | Facebook Page ID |
| `SOURCE_MEDIA_URL` | URL for the owner's approved source face/voice clip |
| `PUBLIC_MEDIA_UPLOAD_URL` | Public object-storage or upload endpoint used by the Meta adapter |
| `AI_AVATAR_PROVIDER_KEY` | Optional; only for an explicitly supported identity-rendering provider |

The Facebook destination must be a **Facebook Page**, not a personal Facebook profile. The Instagram destination must be an eligible professional account. API access must be granted by the account owner through Meta's official developer flow.

## Daily schedule

The workflow is scheduled for 03:30 UTC, equivalent to 09:00 IST, and can also be started manually from the Actions tab. GitHub scheduled jobs are a daily time window rather than a guaranteed exact publication timestamp.

## Identity and health safeguards

The pipeline uses only media declared as owner-approved. It does not clone or imitate another person's face or voice. Synthetic identity generation is disabled unless an explicitly configured provider is added. Health scripts are educational only and must include this disclaimer:

> This content is for general education only, not medical advice. For personal concerns, consult a qualified healthcare professional.

The script policy rejects diagnosis, individualized treatment, medication instructions, unsafe dieting prescriptions, guaranteed outcomes, and unsupported certainty. Research claims must retain source URLs and confidence labels.

## Local test

Install Python dependencies and ensure FFmpeg is available, then run the renderer against a local owner-approved source clip. Do not commit the clip or generated output to Git.

```bash
python3 -m pip install -r requirements.txt
python3 scripts/render_reel.py --input /path/to/owner-approved-source.mp4 --script artifacts/script.json --output artifacts/reel.mp4
python3 scripts/validate_reel.py artifacts/reel.mp4
```

## References

[1]: https://developers.facebook.com/documentation/instagram-platform/content-publishing
[2]: https://developers.facebook.com/documentation/video-api/guides/reels-publishing
[3]: https://docs.github.com/actions/using-workflows/events-that-trigger-workflows
