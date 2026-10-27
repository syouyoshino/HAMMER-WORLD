"""Bounded content identities for immutable, separately persisted map detail."""
import hashlib
import json
import re

DETAIL_VERSION = "planet-detail-v2"
DETAIL_WIDTH, DETAIL_HEIGHT = 1024, 640
MAX_DETAIL_BYTES = 8 * 1024 * 1024
REF_KEYS = ("version", "sha256", "width", "height", "byte_length")


def asset_bytes(payload):
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf8")
    if not 0 < len(raw) <= MAX_DETAIL_BYTES:
        raise ValueError("planet detail exceeds its bounded asset size")
    return raw


def detail_reference(payload):
    raw = asset_bytes(payload)
    ref = {"version": payload.get("version"), "sha256": hashlib.sha256(raw).hexdigest(),
           "width": payload.get("width"), "height": payload.get("height"), "byte_length": len(raw)}
    validate_detail_reference(ref)
    return ref


def validate_detail_reference(ref):
    if (not isinstance(ref, dict) or set(ref) != set(REF_KEYS)
            or ref["version"] != DETAIL_VERSION
            or type(ref["width"]) is not int or ref["width"] != DETAIL_WIDTH
            or type(ref["height"]) is not int or ref["height"] != DETAIL_HEIGHT
            or not isinstance(ref["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", ref["sha256"])
            or type(ref["byte_length"]) is not int or not 0 < ref["byte_length"] <= MAX_DETAIL_BYTES):
        raise ValueError("invalid planet detail reference")


def project_detail_reference(ref):
    validate_detail_reference(ref)
    return {key: ref[key] for key in REF_KEYS}
