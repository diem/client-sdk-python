# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem import offchain
from diem.testing import LocalAccount
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
import cryptography, pytest, base64


def test_serialize_deserialize():
    account = LocalAccount.generate()
    response = offchain.CommandResponseObject(
        status=offchain.CommandResponseStatus.success,
        cid="3185027f05746f5526683a38fdb5de98",
    )
    ret = offchain.jws.serialize(response, account.private_key.sign)

    resp = offchain.jws.deserialize(
        ret,
        offchain.CommandResponseObject,
        account.private_key.public_key().verify,
    )
    assert resp == response


def test_deserialize_error_if_not_3_parts():
    with pytest.raises(
        ValueError, match="invalid JWS compact message: header.payload, expect 3 parts: <header>.<payload>.<signature>"
    ):
        offchain.jws.deserialize(
            b".".join([b"header", b"payload"]),
            offchain.CommandResponseObject,
            lambda: None,
        )


def test_deserialize_error_for_mismatched_protected_header_alg():
    with pytest.raises(ValueError):
        offchain.jws.deserialize(
            b".".join(map(lambda t: base64.urlsafe_b64encode(t), [b'{"alg": "none"}', b"payload", b"sig"])),
            offchain.CommandResponseObject,
            lambda: None,
        )


def test_deserialize_error_for_header_is_not_json():
    with pytest.raises(ValueError):
        offchain.jws.deserialize(
            b".".join(map(lambda t: base64.urlsafe_b64encode(t), [b"header", b"payload", b"sig"])),
            offchain.CommandResponseObject,
            lambda: None,
        )


def test_deserialize_error_for_header_is_not_urlsafe_base64_encoded():
    with pytest.raises(ValueError):
        offchain.jws.deserialize(
            b".".join([b'{"alg": "EdDSA"}'] + list(map(base64.urlsafe_b64encode, [b"payload", b"sig"]))),
            offchain.CommandResponseObject,
            lambda: None,
        )


def test_deserialize_error_for_invalid_signature():
    account = LocalAccount.generate()
    response = offchain.CommandResponseObject(
        status=offchain.CommandResponseStatus.success,
        cid="3185027f05746f5526683a38fdb5de98",
    )
    data = offchain.jws.serialize(response, account.private_key.sign)
    account2 = LocalAccount.generate()
    with pytest.raises(cryptography.exceptions.InvalidSignature):
        offchain.jws.deserialize(
            data,
            offchain.CommandResponseObject,
            account2.private_key.public_key().verify,
        )


def test_deserialize_example_jws():
    example = "eyJhbGciOiJFZERTQSJ9.U2FtcGxlIHNpZ25lZCBwYXlsb2FkLg.dZvbycl2Jkl3H7NmQzL6P0_lDEW42s9FrZ8z-hXkLqYyxNq8yOlDjlP9wh3wyop5MU2sIOYvay-laBmpdW6OBQ"
    public_key = "bd47e3e7afb94debbd82e10ab7d410a885b589db49138628562ac2ec85726129"

    body, sig, msg = offchain.jws.deserialize_string(example.encode("utf-8"))
    assert body == "Sample signed payload."

    key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key))
    key.verify(sig, msg)


def test_serialize_and_deserialize_with_additional_protocted_headers():
    account = LocalAccount.generate()
    response = offchain.CommandResponseObject(
        status=offchain.CommandResponseStatus.success,
        cid="3185027f05746f5526683a38fdb5de98",
    )
    ret = offchain.jws.serialize(response, account.private_key.sign, headers={"keyId": "hello", "alg": "EdDSA"})

    resp = offchain.jws.deserialize(
        ret,
        offchain.CommandResponseObject,
        account.private_key.public_key().verify,
    )
    assert resp == response
