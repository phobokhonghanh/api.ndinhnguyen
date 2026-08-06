import os
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
SCRIPTS_DIR = ROOT_DIR / "scripts"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from core.auth import verify_jwt
from generate_system_token import generate_system_token, load_dev_vars


def test_system_token_generation_and_verification():
    dev_vars = load_dev_vars(ROOT_DIR / ".dev.vars")
    jwt_secret = os.getenv("JWT_SECRET") or dev_vars.get("JWT_SECRET") or "admin.ndinhnguyen"

    token = generate_system_token(days_valid=7)
    assert token is not None

    decoded = verify_jwt(token, jwt_secret)
    assert decoded is not None
    assert decoded["sub"] == "system"
    assert decoded["role"] == "admin"
    assert decoded["email"] == "system@ndinhnguyen.com"
    assert decoded["exp"] > time.time()
