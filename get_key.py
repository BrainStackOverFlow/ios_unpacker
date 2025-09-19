#!/usr/bin/env python3

# Modified from Nicolas's initial script
# Thx to Siguza and Snoolie for AEA auth block parsing information

# Requirements: pip3 install requests pyhpke

# Modified https://github.com/dhinakg/aeota

import argparse
import base64
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from pprint import pprint

import requests
from pyhpke import AEADId, CipherSuite, KDFId, KEMId, KEMKey

AEA_PROFILE__HKDF_SHA256_AESCTR_HMAC__SYMMETRIC__NONE = 1

suite = CipherSuite.new(
    KEMId.DHKEM_P256_HKDF_SHA256, KDFId.HKDF_SHA256, AEADId.AES256_GCM
)


@dataclass(frozen=True)
class AEAKey:
    key_raw: bytes
    key_base64: str


def get_key(f, verbose: bool = False) -> AEAKey:
    fields = {}
    header = f.read(12)
    if len(header) != 12:
        raise RuntimeError(f"Expected 12 bytes, got {len(header)}")

    magic = header[:4]
    if magic != b"AEA1":
        raise RuntimeError(f"Invalid magic: {magic.hex()}")

    profile = int.from_bytes(header[4:7], "little")
    if profile != AEA_PROFILE__HKDF_SHA256_AESCTR_HMAC__SYMMETRIC__NONE:
        raise RuntimeError(f"Invalid AEA profile: {profile}")

    auth_data_blob_size = int.from_bytes(header[8:12], "little")

    if auth_data_blob_size == 0:
        raise RuntimeError("No auth data blob")

    auth_data_blob = f.read(auth_data_blob_size)
    if len(auth_data_blob) != auth_data_blob_size:
        raise RuntimeError(
            f"Expected {auth_data_blob_size} bytes, got {len(auth_data_blob)}"
        )

    assert auth_data_blob[:4]

    while len(auth_data_blob) > 0:
        field_size = int.from_bytes(auth_data_blob[:4], "little")
        field_blob = auth_data_blob[:field_size]

        key, value = field_blob[4:].split(b"\x00", 1)

        fields[key.decode()] = value.decode()

        auth_data_blob = auth_data_blob[field_size:]

    if verbose:
        pprint(fields, stream=sys.stderr)

    if "com.apple.wkms.fcs-response" not in fields:
        raise RuntimeError("No fcs-response field found!")

    if "com.apple.wkms.fcs-key-url" not in fields:
        raise RuntimeError("No fcs-key-url field found!")

    fcs_response = json.loads(fields["com.apple.wkms.fcs-response"])
    enc_request = base64.b64decode(fcs_response["enc-request"])
    wrapped_key = base64.b64decode(fcs_response["wrapped-key"])
    url = fields["com.apple.wkms.fcs-key-url"]

    r = requests.get(url, timeout=10)
    r.raise_for_status()

    privkey = KEMKey.from_pem(r.text)

    recipient = suite.create_recipient_context(enc_request, privkey)
    pt = recipient.open(wrapped_key)

    if verbose:
        print(f"Key: {base64.b64encode(pt).decode()}")

    return AEAKey(pt, base64.b64encode(pt).decode())


def main(aea_path: Path, verbose: bool = False):
    with aea_path.open("rb") as f:
        print(get_key(f, verbose))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get the key for an AEA file or URL")
    parser.add_argument("path", help="Path or URL to the AEA file")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show verbose output"
    )
    args = parser.parse_args()

    main(Path(args.path), args.verbose)
