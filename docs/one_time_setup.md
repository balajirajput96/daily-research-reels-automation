# One-time activation

The workflow and daily schedule are already committed to the private repository. The remaining step is credential provisioning. GitHub Actions must receive credentials as repository Secrets; browser cookies and the authenticated Google Workspace CLI token cannot be copied into a hosted runner.

## Required GitHub Actions Secrets

Add these in **Repository → Settings → Secrets and variables → Actions → New repository secret**:

| Secret | Required for |
|---|---|
| `GEMINI_API_KEY` | Script generation |
| `SOURCE_MEDIA_URL` | Downloading the owner's approved face/voice source clip |
| `META_IG_ACCESS_TOKEN` | Instagram professional-account publishing |
| `META_IG_USER_ID` | Instagram professional-account destination |
| `PUBLIC_MEDIA_URL` | A public URL for the rendered MP4 during the Instagram API publish step |
| `META_FB_PAGE_ACCESS_TOKEN` | Facebook Page Reel publishing |
| `META_FB_PAGE_ID` | Facebook Page destination |

`BGM_URL` is optional. `AI_AVATAR_PROVIDER_KEY` is optional and should only be added if a provider is deliberately selected for the owner's own authorized face/voice. The current renderer safely works with the owner's source clip and AI-assisted captions/visual treatment without requiring a synthetic identity provider.

## Required Meta setup

The Instagram destination must be an eligible professional account. The Facebook destination must be a Facebook Page, because Meta's Reels Publishing API does not publish Reels to a personal Facebook profile. The Meta app must grant the permissions documented by Meta, and the Page access token must have the content-creation task on the Page.

## Source-media requirement

`SOURCE_MEDIA_URL` must be a stable, downloadable URL for the owner's approved source clip. Do not commit the source clip to Git. For private storage, use a signed URL with an expiry long enough for the scheduled run, or add a secure download adapter that authenticates using a separate repository secret.

## Public media requirement

Instagram's documented API flow fetches the video from a public URL. The current repository expects `PUBLIC_MEDIA_URL` to point to the rendered file. A production-grade version should add an upload step to an approved object-storage provider and pass the resulting public, short-lived URL to the Instagram adapter. The workflow intentionally stops before publishing if this URL is absent.

## Schedule

The workflow is active on the default branch and runs daily at 03:30 UTC, which is 09:00 IST. It can also be started manually from the GitHub Actions tab. GitHub scheduled triggers are best-effort and may run late during high platform load.

## Safety behavior

The workflow will not publish if any required secret is missing, the source clip is unavailable, the script lacks the required disclaimer, a claim cites an unapproved source, or the rendered file fails technical validation. It uploads diagnostic artifacts for inspection and retains no raw credentials.
