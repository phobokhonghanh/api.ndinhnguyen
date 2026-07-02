import hmac
import hashlib
import base64
import json
import time


def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def base64url_decode(data: str) -> bytes:
    padded = data + "=" * (4 - len(data) % 4)
    return base64.urlsafe_b64decode(padded.encode("utf-8"))


def generate_jwt(payload: dict, secret: str) -> str:
    """
    Generates a standard HS256 JWT token.
    """
    header = {"alg": "HS256", "typ": "JWT"}
    header_json = json.dumps(header, separators=(",", ":"))
    payload_json = json.dumps(payload, separators=(",", ":"))

    header_b64 = base64url_encode(header_json.encode("utf-8"))
    payload_b64 = base64url_encode(payload_json.encode("utf-8"))

    signing_input = f"{header_b64}.{payload_b64}"
    signature = hmac.new(
        secret.encode("utf-8"), signing_input.encode("utf-8"), hashlib.sha256
    ).digest()
    signature_b64 = base64url_encode(signature)

    return f"{signing_input}.{signature_b64}"


def verify_jwt(token: str, secret: str) -> dict | None:
    """
    Verifies a standard HS256 JWT token and returns its payload if valid and not expired.
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, signature_b64 = parts

        signing_input = f"{header_b64}.{payload_b64}"
        expected_signature = hmac.new(
            secret.encode("utf-8"), signing_input.encode("utf-8"), hashlib.sha256
        ).digest()
        expected_signature_b64 = base64url_encode(expected_signature)

        if not hmac.compare_digest(signature_b64, expected_signature_b64):
            return None

        payload_bytes = base64url_decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))

        if "exp" in payload:
            if payload["exp"] < time.time():
                return None

        return payload
    except Exception:
        return None
