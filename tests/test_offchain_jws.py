# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem import offchain, LocalAccount
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
import cryptography, pytest


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


def test_deserialize_error_for_mismatched_protected_header():
    with pytest.raises(ValueError):
        offchain.jws.deserialize(
            b".".join([b"header", b"payload", b"sig"]),
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


def test_serialize_deserialize_preapproval():
    account = LocalAccount.generate()

    preapproval = offchain.FundPullPreApprovalObject(
        address="lbr1pgfpyysjzgfpyysjzgfpyysjzgf3xycnzvf3xycsm957ne",
        biller_address="lbr1pg9q5zs2pg9q5zs2pg9q5zs2pg9skzctpv9skzcg9kmwta",
        funds_pull_pre_approval_id="lbr1pg9q5zs2pg9q5zs2pg9q5zs2pgyqqqqqqqqqqqqqqspa3m_7b8404c986f53fe072301fe950d030de",
        scope=offchain.FundPullPreApprovalScopeObject(
            type=offchain.FundPullPreApprovalType.consent,
            expiration_timestamp=72322,
            max_cumulative_amount=offchain.ScopedCumulativeAmountObject(
                unit=offchain.TimeUnit.week,
                value=1,
                max_amount=offchain.CurrencyObject(amount=100, currency="XUS"),
            ),
            max_transaction_amount=offchain.CurrencyObject(
                amount=100_000_000,
                currency="XUS",
            ),
        ),
        status=offchain.FundPullPreApprovalStatus.pending,
        description="Pre-approval without default values",
    )
    command = offchain.FundsPullPreApprovalCommand(
        my_actor_address=preapproval.address,
        funds_pull_pre_approval=preapproval,
        inbound=False,
    )
    request = command.new_request()

    serialized = offchain.jws.serialize(request, account.private_key.sign)

    deserialized = offchain.jws.deserialize(
        serialized,
        offchain.CommandRequestObject,
        account.private_key.public_key().verify,
    )
    assert request == deserialized
