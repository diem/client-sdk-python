# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem import offchain
from diem.testing import LocalAccount
import cryptography, pytest


def test_serialize_deserialize():
    account = LocalAccount.generate()
    response = offchain.CommandResponseObject(
        status=offchain.CommandResponseStatus.success,
        cid="3185027f05746f5526683a38fdb5de98",
    )
    ret = offchain.jws.serialize(response, account.compliance_key.sign)

    resp = offchain.jws.deserialize(
        ret,
        offchain.CommandResponseObject,
        account.compliance_key.public_key().verify,
    )
    assert resp == response


def test_deserialize_error_for_invalid_signature():
    account = LocalAccount.generate()
    response = offchain.CommandResponseObject(
        status=offchain.CommandResponseStatus.success,
        cid="3185027f05746f5526683a38fdb5de98",
    )
    data = offchain.jws.serialize(response, account.compliance_key.sign)
    account2 = LocalAccount.generate()
    with pytest.raises(cryptography.exceptions.InvalidSignature):
        offchain.jws.deserialize(
            data,
            offchain.CommandResponseObject,
            account2.compliance_key.public_key().verify,
        )
