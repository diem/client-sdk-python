# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem import jws
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
import pytest


HEX_KEY = "ccf2700f8b2d001a8caf80ca2bfc5b7cc71df1f799e02c78bc3f07ea3af79a98"
KEY = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(HEX_KEY))
PUBLIC_KEY = KEY.public_key()
HEADERS = {"keyId": "hello", "alg": "EdDSA"}
MSG = "msg"


def test_encode_decode_message():
    sig = jws.encode(MSG, KEY.sign)
    headers, body = jws.decode(sig, PUBLIC_KEY.verify)
    assert headers == {"alg": "EdDSA"}
    assert body == MSG

    assert (
        sig
        == b"eyJhbGciOiJFZERTQSJ9.bXNn.xtWbB8A-Jp-UYspmnYYrVGgfGRzV9TCTZ5j5z7Z_y-FtsI116Jkp81_n7OkkPInOk4P9Df2X11paOXaSs_0QCQ"
    )


def test_decode_error_with_different_public_key():
    sig = jws.encode(MSG, KEY.sign)
    diff_key = Ed25519PrivateKey.generate().public_key()
    with pytest.raises(InvalidSignature):
        jws.decode(sig, diff_key.verify)


def test_decode_error_with_invalid_signature():
    with pytest.raises(InvalidSignature):
        jws.decode(b"eyJhbGciOiAiRWREU0EifQ.bXNn.bXNn", PUBLIC_KEY.verify)


def test_encode_decode_message_with_headers():
    sig = jws.encode(MSG, KEY.sign, headers=HEADERS)
    headers, body = jws.decode(sig, PUBLIC_KEY.verify)
    assert headers == HEADERS
    assert body == MSG

    assert (
        sig
        == b"eyJrZXlJZCI6ImhlbGxvIiwiYWxnIjoiRWREU0EifQ.bXNn.UrP61njLyFIZvjPxw6PAiut_NVk37ULy609PqI-7Vc3HWg4omcSDG95MHbGuif2-2YxHUkxmaWvleZ1BNlEaAQ"
    )


def test_encode_decode_message_with_headers_and_content_detached():
    sig = jws.encode(MSG, KEY.sign, headers=HEADERS, content_detached=True)
    headers, body = jws.decode(sig, PUBLIC_KEY.verify, detached_content=b"msg")
    assert headers == HEADERS
    assert body == MSG

    assert (
        sig
        == b"eyJrZXlJZCI6ImhlbGxvIiwiYWxnIjoiRWREU0EifQ..UrP61njLyFIZvjPxw6PAiut_NVk37ULy609PqI-7Vc3HWg4omcSDG95MHbGuif2-2YxHUkxmaWvleZ1BNlEaAQ"
    )


def test_decode_example_jws():
    example = "eyJhbGciOiJFZERTQSJ9.U2FtcGxlIHNpZ25lZCBwYXlsb2FkLg.dZvbycl2Jkl3H7NmQzL6P0_lDEW42s9FrZ8z-hXkLqYyxNq8yOlDjlP9wh3wyop5MU2sIOYvay-laBmpdW6OBQ"
    public_key = "bd47e3e7afb94debbd82e10ab7d410a885b589db49138628562ac2ec85726129"
    key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key))

    headers, body = jws.decode(example.encode("utf-8"), key.verify)
    assert body == "Sample signed payload."
    assert headers == {"alg": "EdDSA"}


def test_encode_example_jws():
    example = "eyJhbGciOiJFZERTQSJ9.U2FtcGxlIHNpZ25lZCBwYXlsb2FkLg.dZvbycl2Jkl3H7NmQzL6P0_lDEW42s9FrZ8z-hXkLqYyxNq8yOlDjlP9wh3wyop5MU2sIOYvay-laBmpdW6OBQ"
    private_key = "bcbb56781ee4b7b7dc30f964d351a11a6a566131d8aa719165450def6013d4ae"

    key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(private_key))
    msg = jws.encode("Sample signed payload.", key.sign)
    assert msg.decode("utf-8") == example


def test_decode_error_if_not_3_parts():
    with pytest.raises(ValueError, match="invalid JWS compact message: b'header.payload'"):
        jws.decode(b".".join([b"header", b"payload"]), PUBLIC_KEY.verify)


def test_decode_error_for_invalid_protected_header_json():
    with pytest.raises(ValueError, match='invalid JWS message header: "alg": "none"'):
        jws.decode(b".".join(b64_urlsafe([b'"alg": "none"', b"{}", b"sig"])), PUBLIC_KEY.verify)


def test_decode_error_for_invalid_protected_header_json_type():
    with pytest.raises(ValueError, match='invalid JWS message header: "alg"'):
        jws.decode(b".".join(b64_urlsafe([b'"alg"', b"{}", b"sig"])), PUBLIC_KEY.verify)


def test_decode_error_for_invalid_protected_header_is_not_b64_urlsafe():
    with pytest.raises(ValueError, match='invalid JWS message header: b\'{"alg": "EdDSA"}\''):
        jws.decode(
            b".".join([b'{"alg": "EdDSA"}'] + b64_urlsafe([b"payload", b"sig"])),
            PUBLIC_KEY.verify,
        )


def test_decode_error_for_mismatched_protected_header_alg():
    with pytest.raises(ValueError, match='invalid JWS message header: {"alg": "none"}'):
        jws.decode(b".".join(map(jws.base64.urlsafe_b64encode, [b'{"alg": "none"}', b"{}", b"sig"])), PUBLIC_KEY.verify)


def b64_urlsafe(data):
    return list(map(jws.base64.urlsafe_b64encode, data))
