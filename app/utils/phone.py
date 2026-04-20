"""Normalize contact phone: digits only, max 11 characters."""

import re

_MAX_LEN = 11


def normalize_contact_phone(raw: str | None) -> str | None:
    if not raw:
        return None
    digits = re.sub(r"\D", "", str(raw).strip())
    if not digits:
        return None
    if len(digits) > _MAX_LEN:
        return None
    return digits


def is_valid_contact_phone(raw: str | None) -> bool:
    if not (raw or "").strip():
        return True
    n = normalize_contact_phone(raw)
    return n is not None and len(n) <= _MAX_LEN
