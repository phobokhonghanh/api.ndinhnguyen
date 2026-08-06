import os
import sys
import time
from pathlib import Path

# Add src to python path
ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.auth import generate_jwt, verify_jwt


def load_dev_vars(env_file_path: Path) -> dict:
    vars_dict = {}
    if env_file_path.exists():
        with open(env_file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    vars_dict[key.strip()] = value.strip()
    return vars_dict


def generate_system_token(days_valid: int = 30) -> str:
    dev_vars = load_dev_vars(ROOT_DIR / ".dev.vars")
    jwt_secret = os.getenv("JWT_SECRET") or dev_vars.get("JWT_SECRET") or "admin.ndinhnguyen"

    payload = {
        "sub": "system",
        "email": "system@ndinhnguyen.com",
        "role": "admin",
        "exp": int(time.time()) + (days_valid * 24 * 60 * 60),
    }

    return generate_jwt(payload, jwt_secret)


def main():
    dev_vars = load_dev_vars(ROOT_DIR / ".dev.vars")
    jwt_secret = os.getenv("JWT_SECRET") or dev_vars.get("JWT_SECRET") or "admin.ndinhnguyen"
    token = generate_system_token(30)
    decoded = verify_jwt(token, jwt_secret)

    print("=" * 60)
    print("TOKEN CHO USER 'system':")
    print("=" * 60)
    print(token)
    print("=" * 60)
    print("\nChi tiết Payload:")
    print(decoded)
    print("\nVí dụ sử dụng trong cURL / HTTP Client:")
    print(f'curl -H "Authorization: Bearer {token}" http://localhost:8787/api/bookmarks')
    print("=" * 60)


if __name__ == "__main__":
    main()
