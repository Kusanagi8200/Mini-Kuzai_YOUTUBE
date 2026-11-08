#!/usr/bin/env python3
"""Controlled YouTube uploader for Mini-Kuzai.

Safety rules:
- credentials live outside Git
- authenticated channel must match the frozen target Channel ID
- uploads are forced to PRIVATE
- duplicate media SHA256 values are blocked by a local journal
- default mode is preflight only; --execute is required to upload
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


ROOT = Path(__file__).resolve().parents[1]

TARGET_CHANNEL_ID = "UC9MDfq5s-6j_twe4xJH_XXA"

TOKEN_FILE = Path("/root/.config/mini-kuzai-youtube/token.json")
CLIENT_FILE = Path("/root/.config/mini-kuzai-youtube/oauth-client.json")

STATE_DIR = Path("/root/.local/state/mini-kuzai-youtube")
JOURNAL_FILE = STATE_DIR / "upload-journal.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ensure_private_file(path: Path, label: str) -> None:
    if not path.is_file():
        raise RuntimeError(f"{label} not found: {path}")

    mode = path.stat().st_mode & 0o777
    if mode != 0o600:
        raise RuntimeError(
            f"{label} must have mode 600, got {mode:03o}: {path}"
        )


def load_credentials() -> Credentials:
    ensure_private_file(CLIENT_FILE, "OAuth client file")
    ensure_private_file(TOKEN_FILE, "OAuth token file")

    credentials = Credentials.from_authorized_user_file(
        str(TOKEN_FILE),
        scopes=SCOPES,
    )

    if credentials.expired:
        if not credentials.refresh_token:
            raise RuntimeError("OAuth token expired and no refresh token is available")

        credentials.refresh(Request())
        TOKEN_FILE.write_text(credentials.to_json(), encoding="utf-8")
        os.chmod(TOKEN_FILE, 0o600)

    if not credentials.valid:
        raise RuntimeError("OAuth credentials are not valid")

    granted = set(credentials.scopes or [])
    missing = set(SCOPES) - granted
    if missing:
        raise RuntimeError(
            "OAuth token is missing required scopes: "
            + ", ".join(sorted(missing))
        )

    return credentials


def build_youtube(credentials: Credentials):
    return build(
        "youtube",
        "v3",
        credentials=credentials,
        cache_discovery=False,
    )


def verify_channel(youtube) -> tuple[str, str]:
    response = youtube.channels().list(
        part="id,snippet",
        mine=True,
    ).execute()

    items = response.get("items", [])
    if len(items) != 1:
        raise RuntimeError(
            f"Expected exactly one authenticated channel, got {len(items)}"
        )

    channel = items[0]
    channel_id = channel.get("id", "")
    channel_title = channel.get("snippet", {}).get("title", "")

    if channel_id != TARGET_CHANNEL_ID:
        raise RuntimeError(
            f"Authenticated channel mismatch: {channel_id!r}"
        )

    return channel_id, channel_title


def load_journal() -> dict:
    if not JOURNAL_FILE.exists():
        return {
            "schema_version": 1,
            "uploads": [],
        }

    data = json.loads(JOURNAL_FILE.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise RuntimeError("Unsupported upload journal schema")

    uploads = data.get("uploads")
    if not isinstance(uploads, list):
        raise RuntimeError("Invalid upload journal")

    return data


def duplicate_for_sha(journal: dict, media_sha256: str) -> dict | None:
    for entry in journal.get("uploads", []):
        if entry.get("media_sha256") == media_sha256:
            return entry
    return None


def save_journal(journal: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(STATE_DIR, 0o700)

    temporary = JOURNAL_FILE.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(journal, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.chmod(temporary, 0o600)
    temporary.replace(JOURNAL_FILE)
    os.chmod(JOURNAL_FILE, 0o600)


def upload_private(
    youtube,
    video: Path,
    title: str,
    description: str,
    tags: list[str],
) -> str:
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
        },
        "status": {
            "privacyStatus": "private",
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        str(video),
        mimetype="video/mp4",
        resumable=True,
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        _, response = request.next_chunk()

    video_id = response.get("id", "")
    if not video_id:
        raise RuntimeError("YouTube API returned no video ID")

    return video_id


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--title")
    parser.add_argument("--description", default="")
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    video = args.video.resolve()

    if not video.is_file():
        raise RuntimeError(f"Video not found: {video}")

    if video.suffix.lower() != ".mp4":
        raise RuntimeError("Only MP4 media is accepted")

    media_sha256 = sha256_file(video)

    credentials = load_credentials()
    youtube = build_youtube(credentials)
    channel_id, channel_title = verify_channel(youtube)

    journal = load_journal()
    duplicate = duplicate_for_sha(journal, media_sha256)

    print("##### SECTION RESULTS FOR ASSISTANT ######")
    print("PREFLIGHT=PASS")
    print(f"TARGET_CHANNEL_MATCH={int(channel_id == TARGET_CHANNEL_ID)}")
    print(f"CHANNEL_ID={channel_id}")
    print(f"CHANNEL_TITLE={channel_title}")
    print("PRIVACY_POLICY=PRIVATE_ONLY")
    print(f"VIDEO_PRESENT={int(video.is_file())}")
    print(f"VIDEO_SIZE_BYTES={video.stat().st_size}")
    print(f"VIDEO_SHA256={media_sha256}")
    print(f"JOURNAL_PRESENT={int(JOURNAL_FILE.is_file())}")
    print(f"DUPLICATE_SHA256={int(duplicate is not None)}")
    print(f"EXECUTE_REQUESTED={int(args.execute)}")

    if duplicate is not None:
        print("UPLOAD_BLOCKED=DUPLICATE_MEDIA")
        return 3

    if not args.execute:
        print("UPLOAD_PERFORMED=0")
        return 0

    if not args.title or not args.title.strip():
        raise RuntimeError("--title is required with --execute")

    video_id = upload_private(
        youtube=youtube,
        video=video,
        title=args.title.strip(),
        description=args.description,
        tags=args.tag,
    )

    journal["uploads"].append(
        {
            "uploaded_at_utc": datetime.now(timezone.utc).isoformat(),
            "channel_id": channel_id,
            "media_sha256": media_sha256,
            "privacy_status": "private",
            "video_id": video_id,
        }
    )
    save_journal(journal)

    print("UPLOAD_PERFORMED=1")
    print("UPLOAD_PRIVACY=private")
    print(f"VIDEO_ID={video_id}")
    print(f"JOURNAL_FILE={JOURNAL_FILE}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR={exc}", file=sys.stderr)
        raise
