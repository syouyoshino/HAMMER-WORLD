"""Leased, checksum-verified public archive worker for Google Drive v3."""
import hashlib
import json
import os
import secrets
import urllib.parse
from dataclasses import dataclass
from typing import Protocol

import httpx


@dataclass(frozen=True)
class RemoteFile:
    file_id: str
    name: str
    folder_id: str
    payload: bytes


class DriveAdapter(Protocol):
    def generate_id(self) -> str: ...
    def create_file(self, file_id: str, name: str, folder_id: str, payload: bytes) -> None: ...
    def get_file(self, file_id: str) -> dict | None: ...
    def download_file(self, file_id: str) -> bytes: ...


class GoogleDriveV3:
    """Small REST adapter using a server-side OAuth access token."""
    base_url = "https://www.googleapis.com/drive/v3"
    upload_url = "https://www.googleapis.com/upload/drive/v3"

    def __init__(self, access_token: str, client: httpx.Client | None = None):
        if not access_token:
            raise ValueError("Drive access token is required")
        self.client = client or httpx.Client(timeout=30)
        self._owns_client = client is None
        self._headers = {"Authorization": f"Bearer {access_token}"}

    def _check(self, response):
        if response.is_error:
            raise RuntimeError(f"Drive API request failed (HTTP {response.status_code})")
        return response

    def generate_id(self):
        response = self._check(self.client.get(
            f"{self.base_url}/files/generateIds", params={"count": 1}, headers=self._headers))
        ids = response.json().get("ids", [])
        if not ids or not isinstance(ids[0], str):
            raise RuntimeError("Drive ID reservation returned no file ID")
        return ids[0]

    def create_file(self, file_id, name, folder_id, payload):
        boundary = f"hammerworld_{secrets.token_hex(16)}"
        metadata = json.dumps({
            "id": file_id, "name": name, "mimeType": "application/json", "parents": [folder_id]
        }, separators=(",", ":")).encode("utf-8")
        body = b"".join((
            f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n".encode(),
            metadata, b"\r\n", f"--{boundary}\r\nContent-Type: application/json\r\n\r\n".encode(),
            payload, b"\r\n", f"--{boundary}--\r\n".encode(),
        ))
        headers = dict(self._headers)
        headers["Content-Type"] = f"multipart/related; boundary={boundary}"
        response = self.client.post(
            f"{self.upload_url}/files", params={"uploadType": "multipart", "fields": "id"},
            content=body, headers=headers)
        self._check(response)

    def get_file(self, file_id):
        escaped = urllib.parse.quote(file_id, safe="")
        response = self.client.get(
            f"{self.base_url}/files/{escaped}",
            params={"fields": "id,name,mimeType,parents,trashed"}, headers=self._headers)
        if response.status_code == 404:
            return None
        return self._check(response).json()

    def download_file(self, file_id):
        escaped = urllib.parse.quote(file_id, safe="")
        response = self.client.get(
            f"{self.base_url}/files/{escaped}", params={"alt": "media"}, headers=self._headers)
        return self._check(response).content

    def close(self):
        if self._owns_client:
            self.client.close()


class ArchiveVerificationError(RuntimeError):
    pass


class ArchiveWorker:
    def __init__(self, store, adapter: DriveAdapter | None, folder_ids: dict[str, str | None],
                 lease_seconds=60, owner=None):
        self.store = store
        self.adapter = adapter
        self.folder_ids = folder_ids
        self.lease_seconds = lease_seconds
        self.owner = owner or f"archive-{secrets.token_urlsafe(16)}"

    @staticmethod
    def _filename(claim):
        return f"{claim['campaign_id']}-turn-{claim['turn']}-{claim['snapshot_id']}.json"

    def _verify(self, claim, file_id):
        metadata = self.adapter.get_file(file_id)
        if metadata is None:
            raise ArchiveVerificationError("remote file is missing")
        if (metadata.get("id") != file_id or metadata.get("mimeType") != "application/json"
                or metadata.get("parents") != [claim["folder_id"]]
                or metadata.get("trashed", False)):
            raise ArchiveVerificationError("remote file metadata does not match frozen archive")
        remote_bytes = self.adapter.download_file(file_id)
        if remote_bytes != claim["payload_bytes"]:
            raise ArchiveVerificationError("remote file bytes do not match frozen archive")
        if hashlib.sha256(remote_bytes).hexdigest() != claim["payload_checksum"]:
            raise ArchiveVerificationError("remote file checksum does not match frozen archive")

    @staticmethod
    def _safe_error(exc):
        status = getattr(getattr(exc, "response", None), "status_code", None)
        if status is not None:
            return f"drive_http_{status}"
        if isinstance(exc, ArchiveVerificationError):
            return "archive_verification_failed"
        return f"archive_error_{type(exc).__name__[:48]}"

    def sync(self, limit=1):
        if limit < 1:
            raise ValueError("limit must be positive")
        demo_folder = self.folder_ids.get("demo")
        real_folder = self.folder_ids.get("pregame")
        if demo_folder and real_folder and demo_folder == real_folder:
            return {"status": "disabled", "reason": "demo and real archive destinations must differ", "items": []}
        if self.adapter is None:
            return {"status": "disabled", "reason": "missing server-side Drive credentials", "items": []}
        items = []
        for _ in range(limit):
            claim = self.store.claim_archive(self.owner, self.lease_seconds, self.folder_ids)
            if claim is None:
                break
            if claim.get("disabled"):
                items.append({"snapshot_id": claim["snapshot_id"], "status": "disabled",
                              "reason": "archive folder is not configured"})
                break
            file_id = claim["remote_file_id"]
            try:
                if not file_id:
                    file_id = self.adapter.generate_id()
                    if not self.store.persist_archive_file_id(claim["snapshot_id"], self.owner, file_id):
                        raise RuntimeError("archive lease lost before file ID was persisted")
                    claim["remote_file_id"] = file_id
                existing = self.adapter.get_file(file_id)
                if existing is None:
                    try:
                        self.adapter.create_file(
                            file_id, self._filename(claim), claim["folder_id"], claim["payload_bytes"])
                    except Exception:
                        # The remote create may have succeeded before a connection failed.
                        # Verify the same reserved ID before deciding that the attempt failed.
                        if self.adapter.get_file(file_id) is None:
                            raise
                self._verify(claim, file_id)
                if not self.store.mark_archive_verified(claim["snapshot_id"], self.owner, file_id):
                    raise RuntimeError("archive lease lost before verification was recorded")
                items.append({"snapshot_id": claim["snapshot_id"], "status": "verified",
                              "remote_file_id": file_id})
            except Exception as exc:
                self.store.release_archive(claim["snapshot_id"], self.owner, self._safe_error(exc))
                items.append({"snapshot_id": claim["snapshot_id"], "status": "pending",
                              "error": self._safe_error(exc)})
                # A failing oldest item should not be hot-looped in a one-shot run.
                break
        return {"status": "complete" if all(x["status"] == "verified" for x in items)
                else (items[0]["status"] if items else "idle"), "items": items}


def worker_from_environment(store, environ=None):
    environ = os.environ if environ is None else environ
    token = environ.get("WOLD_DRIVE_ACCESS_TOKEN")
    adapter = GoogleDriveV3(token) if token else None
    folders = {
        "demo": environ.get("WOLD_DRIVE_DEMO_FOLDER_ID"),
        "pregame": environ.get("WOLD_DRIVE_FOLDER_ID"),
    }
    return ArchiveWorker(store, adapter, folders)
