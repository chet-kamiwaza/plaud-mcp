#!/usr/bin/env python3
"""
Extract Plaud bearer token and device ID from the Plaud desktop app on macOS.

Reads the encrypted token from Electron safeStorage (Chromium v10 AES-128-CBC),
decrypts it using the key stored in the macOS Keychain, and prints the values
ready to paste into your .env file.

Requirements:
  pip install cryptography
  Plaud desktop app installed and signed in at least once.
  macOS only (uses the macOS Keychain via the `security` CLI).
"""
import argparse
import base64
import json
import subprocess  # nosec B404 - used only for macOS `security` CLI with fixed argv
import sys
from pathlib import Path

PLAUD_APP_SUPPORT = Path.home() / "Library" / "Application Support" / "Plaud"
ENCRYPTION_JSON = PLAUD_APP_SUPPORT / "encryption.json"
MISC_JSON = PLAUD_APP_SUPPORT / "misc.json"


def ensure_cryptography_installed() -> None:
    try:
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC  # noqa: F401
    except ImportError:
        print("ERROR: 'cryptography' package not found.")
        print("Install it with:  pip install cryptography")
        sys.exit(1)


def get_keychain_password() -> str:
    # Invokes the macOS `security` CLI with a fixed argv (no shell, no user
    # input). `security` is a system binary at /usr/bin/security; resolving
    # via PATH is acceptable for a developer helper script on macOS.
    result = subprocess.run(  # nosec B603 B607
        ["security", "find-generic-password",
         "-s", "Plaud Safe Storage",
         "-a", "Plaud Key",
         "-w"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        print("ERROR: Could not read Plaud key from Keychain.")
        print("Make sure the Plaud desktop app is installed and you've signed in at least once.")
        sys.exit(1)
    return result.stdout.strip()


def derive_key(password: str) -> bytes:
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
    # SHA1 and these PBKDF2 parameters are mandated by Chromium's safeStorage
    # format (Electron's encryption.json). They are not a security choice we
    # control; they are required to decrypt a file Plaud's desktop app wrote.
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA1(),  # nosec B303 - Chromium safeStorage compatibility
        length=16,
        salt=b"saltysalt",
        iterations=1003,
        backend=default_backend(),
    )
    return kdf.derive(password.encode("utf-8"))


def decrypt_token(encrypted_b64: str, key: bytes) -> str:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    ciphertext = base64.b64decode(encrypted_b64)
    # Strip the 3-byte "v10" prefix used by Chromium
    ciphertext = ciphertext[3:]
    iv = b" " * 16
    # AES-128-CBC is what Chromium safeStorage produces; authentication is not
    # available in this legacy format. We are decrypting, not designing, crypto.
    # nosemgrep: python.cryptography.security.mode-without-authentication.crypto-mode-without-authentication
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    # Remove PKCS7 padding
    pad_len = padded[-1]
    return padded[:-pad_len].decode("utf-8")


def get_device_id() -> str:
    if not MISC_JSON.exists():
        return ""
    data = json.loads(MISC_JSON.read_text())
    return data.get("systemInfo", {}).get("uuid", "")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract the Plaud bearer token and optional device ID."
    )
    parser.add_argument(
        "--output",
        help="Write the decrypted bearer token to this file instead of printing it.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None):
    args = parse_args(argv)
    ensure_cryptography_installed()

    if not ENCRYPTION_JSON.exists():
        print(f"ERROR: {ENCRYPTION_JSON} not found.")
        print("Make sure the Plaud desktop app is installed and you've signed in.")
        sys.exit(1)

    enc_data = json.loads(ENCRYPTION_JSON.read_text())
    encrypted_b64 = enc_data.get("authToken")
    if not encrypted_b64:
        print("ERROR: 'authToken' key not found in encryption.json.")
        sys.exit(1)

    keychain_password = get_keychain_password()
    key = derive_key(keychain_password)
    token = decrypt_token(encrypted_b64, key)
    device_id = get_device_id()

    if args.output:
        output_path = Path(args.output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(f"{token}\n", encoding="utf-8")
        print(f"Token written to {output_path}")
        if device_id:
            print(f"PLAUD_DEVICE_ID={device_id}")
        else:
            print("# PLAUD_DEVICE_ID not found — check misc.json manually")
        return

    print("# Add these to your .env file:\n")
    print(f"PLAUD_TOKEN={token}")
    if device_id:
        print(f"PLAUD_DEVICE_ID={device_id}")
    else:
        print("# PLAUD_DEVICE_ID not found — check misc.json manually")


if __name__ == "__main__":
    main()
