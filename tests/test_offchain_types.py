# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem import identifier, offchain, LocalAccount
import dataclasses, json, pytest, uuid


def test_entity_kyc_data():
    kyc_data = offchain.entity_kyc_data(
        given_name="hello",
        surname="world",
        address=offchain.AddressObject(city="San Francisco"),
        legal_entity_name="foo bar",
    )
    assert kyc_data.type == offchain.KycDataObjectType.entity


def test_dumps_and_loads_request_command():
    kyc_data = offchain.individual_kyc_data(
        given_name="hello",
        surname="world",
        address=offchain.AddressObject(city="San Francisco"),
        national_id=offchain.NationalIdObject(id_value="234121234"),
        legal_entity_name="foo bar",
    )
    assert offchain.from_json(offchain.to_json(kyc_data), offchain.KycDataObject) == kyc_data
    payment = offchain.PaymentObject(
        reference_id="4185027f-0574-6f55-2668-3a38fdb5de98",
        sender=offchain.PaymentActorObject(
            address="lbr1p7ujcndcl7nudzwt8fglhx6wxn08kgs5tm6mz4usw5p72t",
            status=offchain.StatusObject(status=offchain.Status.needs_kyc_data),
            kyc_data=kyc_data,
            metadata=["hello", "world"],
        ),
        receiver=offchain.PaymentActorObject(
            address="lbr1p7ujcndcl7nudzwt8fglhx6wxnvqqqqqqqqqqqqelu3xv",
            status=offchain.StatusObject(
                status=offchain.Status.abort,
                abort_code="code1",
                abort_message="code1 message",
            ),
        ),
        action=offchain.PaymentActionObject(amount=1_000_000_000_000, currency="XUS", timestamp=1604902048),
        original_payment_reference_id="0185027f-0574-6f55-2668-3a38fdb5de98",
    )
    assert offchain.from_json(offchain.to_json(payment), offchain.PaymentObject) == payment

    request = offchain.CommandRequestObject(
        command_type=offchain.CommandType.PaymentCommand,
        command=offchain.PaymentCommandObject(
            _ObjectType=offchain.CommandType.PaymentCommand,
            payment=payment,
        ),
        cid="3185027f-0574-6f55-2668-3a38fdb5de98",
    )
    assert offchain.from_json(offchain.to_json(request), offchain.CommandRequestObject) == request
    assert offchain.from_json(offchain.to_json(request)) == request

    assert json.loads(offchain.to_json(request)) == json.loads(
        """{
  "cid": "3185027f-0574-6f55-2668-3a38fdb5de98",
  "command_type": "PaymentCommand",
  "command": {
    "_ObjectType": "PaymentCommand",
    "payment": {
      "reference_id": "4185027f-0574-6f55-2668-3a38fdb5de98",
      "sender": {
        "address": "lbr1p7ujcndcl7nudzwt8fglhx6wxn08kgs5tm6mz4usw5p72t",
        "status": {
          "status": "needs_kyc_data"
        },
        "kyc_data": {
          "type": "individual",
          "payload_version": 1,
          "given_name": "hello",
          "surname": "world",
          "address": {
            "city": "San Francisco"
          },
          "national_id": {
            "id_value": "234121234"
          },
          "legal_entity_name": "foo bar"
        },
        "metadata": [
          "hello",
          "world"
        ]
      },
      "receiver": {
        "address": "lbr1p7ujcndcl7nudzwt8fglhx6wxnvqqqqqqqqqqqqelu3xv",
        "status": {
          "status": "abort",
          "abort_code": "code1",
          "abort_message": "code1 message"
        }
      },
      "action": {
        "amount": 1000000000000,
        "currency": "XUS",
        "action": "charge",
        "timestamp": 1604902048
      },
      "original_payment_reference_id": "0185027f-0574-6f55-2668-3a38fdb5de98"
    }
  },
  "_ObjectType": "CommandRequestObject"
}"""
    )


def test_dumps_and_loads_response_command():
    response = offchain.CommandResponseObject(
        status=offchain.CommandResponseStatus.success,
        cid="3185027f-0574-6f55-2668-3a38fdb5de98",
    )
    assert offchain.from_json(offchain.to_json(response), offchain.CommandResponseObject) == response
    assert offchain.from_json(offchain.to_json(response)) == response
    assert json.loads(offchain.to_json(response)) == json.loads(
        """{
  "status": "success",
  "_ObjectType": "CommandResponseObject",
  "cid": "3185027f-0574-6f55-2668-3a38fdb5de98"
}"""
    )
    response = offchain.CommandResponseObject(
        status=offchain.CommandResponseStatus.failure,
        error=offchain.OffChainErrorObject(
            type=offchain.OffChainErrorType.command_error,
            code="code2",
            field="signature",
            message="abc",
        ),
        cid="3185027f-0574-6f55-2668-3a38fdb5de98",
    )
    assert offchain.from_json(offchain.to_json(response), offchain.CommandResponseObject) == response
    assert offchain.from_json(offchain.to_json(response)) == response
    assert json.loads(offchain.to_json(response)) == json.loads(
        """{
  "status": "failure",
  "_ObjectType": "CommandResponseObject",
  "error": {
    "type": "command_error",
    "code": "code2",
    "field": "signature",
    "message": "abc"
  },
  "cid": "3185027f-0574-6f55-2668-3a38fdb5de98"
}"""
    )


def test_new_payment_request_and_object(factory):
    sender = LocalAccount.generate()
    receiver = LocalAccount.generate()
    payment = factory.new_payment_object(sender, receiver)
    request = offchain.new_payment_request(payment)
    reference_id = payment.reference_id

    assert reference_id
    assert_cid(request.cid)
    assert uuid.UUID(reference_id)
    assert "-" in reference_id

    payment = request.command.payment
    address, subaddress = identifier.decode_account(payment.sender.address, identifier.TDM)
    assert subaddress is not None
    assert address == sender.account_address
    address, subaddress = identifier.decode_account(payment.receiver.address, identifier.TDM)
    assert subaddress is not None
    assert address == receiver.account_address

    expected = f"""{{
  "cid": "{request.cid}",
  "command_type": "PaymentCommand",
  "command": {{
    "_ObjectType": "PaymentCommand",
    "payment": {{
      "reference_id": "{reference_id}",
      "sender": {{
        "address": "{payment.sender.address}",
        "status": {{
          "status": "needs_kyc_data"
        }},
        "kyc_data": {{
          "type": "individual",
          "payload_version": 1,
          "given_name": "Jack",
          "surname": "G",
          "address": {{
            "city": "San Francisco"
          }}
        }}
      }},
      "receiver": {{
        "address": "{payment.receiver.address}",
        "status": {{
          "status": "none"
        }}
      }},
      "action": {{
        "amount": 1000000000000,
        "currency": "XUS",
        "action": "charge",
        "timestamp": {payment.action.timestamp}
      }}
    }}
  }},
  "_ObjectType": "CommandRequestObject"
}}"""
    assert json.loads(offchain.to_json(request)) == json.loads(expected)
    assert request == offchain.from_json(expected, offchain.CommandRequestObject)
    assert request == offchain.from_json(expected)


def test_reply_request():
    resp = offchain.reply_request("cid")
    assert json.loads(offchain.to_json(resp)) == json.loads(
        """{
  "cid": "cid",
  "_ObjectType": "CommandResponseObject",
  "status": "success"
}"""
    )

    resp = offchain.reply_request(
        "cid",
        offchain.OffChainErrorObject(
            type=offchain.OffChainErrorType.command_error,
            field="kyc_data",
            code="code1",
            message="message",
        ),
    )
    assert json.loads(offchain.to_json(resp)) == json.loads(
        """{
  "cid": "cid",
  "_ObjectType": "CommandResponseObject",
  "status": "failure",
  "error": {
    "type": "command_error",
    "code": "code1",
    "field": "kyc_data",
    "message": "message"
  }
}"""
    )


def test_validate_write_once_fields():
    offchain.validate_write_once_fields("payment", None, None)

    payment = offchain.PaymentObject(
        reference_id="4185027f-0574-6f55-2668-3a38fdb5de98",
        sender=offchain.PaymentActorObject(
            address="lbr1p7ujcndcl7nudzwt8fglhx6wxn08kgs5tm6mz4usw5p72t",
            status=offchain.StatusObject(status=offchain.Status.needs_kyc_data),
            kyc_data=offchain.individual_kyc_data(
                given_name="hello",
            ),
            metadata=["hello", "world"],
        ),
        receiver=offchain.PaymentActorObject(
            address="lbr1p7ujcndcl7nudzwt8fglhx6wxnvqqqqqqqqqqqqelu3xv",
            status=offchain.StatusObject(
                status=offchain.Status.abort,
                abort_code="code1",
                abort_message="code1 message",
            ),
        ),
        action=offchain.PaymentActionObject(amount=1_000_000_000_000, currency="XUS", timestamp=1604902048),
        original_payment_reference_id="0185027f-0574-6f55-2668-3a38fdb5de98",
    )
    offchain.validate_write_once_fields("payment", payment, payment)
    offchain.validate_write_once_fields("payment", payment, None)
    offchain.validate_write_once_fields("payment", None, payment)

    new_payment = dataclasses.replace(
        payment, sender=offchain.replace_payment_actor(payment.sender, kyc_data=offchain.individual_kyc_data())
    )
    with pytest.raises(offchain.InvalidOverwriteError):
        offchain.validate_write_once_fields("payment", new_payment, payment)


def test_validate_write_once_fields_raises_type_error_if_value_type_mismatched():
    with pytest.raises(TypeError):
        offchain.validate_write_once_fields("payment", "str", False)


def test_validate_write_once_fields_raises_ignore_value_is_not_dataclass():
    offchain.validate_write_once_fields("payment", "str", "obj")
    offchain.validate_write_once_fields("payment", {"hello": 1}, {"world": 2})


def test_validate_write_once_fields_raises_overwrite_error_when_set_value_to_none():
    actor1 = offchain.PaymentActorObject(
        address="lbr1p7ujcndcl7nudzwt8fglhx6wxnvqqqqqqqqqqqqelu3xv",
        status=offchain.StatusObject(status=offchain.Status.none),
        additional_kyc_data="test",
    )
    actor2 = offchain.PaymentActorObject(
        address="lbr1p7ujcndcl7nudzwt8fglhx6wxnvqqqqqqqqqqqqelu3xv",
        status=offchain.StatusObject(status=offchain.Status.none),
        additional_kyc_data=None,
    )

    with pytest.raises(
        offchain.InvalidOverwriteError,
        match="write once field 'actor.additional_kyc_data': test => None",
    ):
        offchain.validate_write_once_fields("actor", actor2, actor1)


def test_invalid_object():
    request_json = "1111"
    with pytest.raises(offchain.FieldError, match="expect json object, but got int: ") as e:
        offchain.from_json(request_json)

    assert e.value.code == "invalid_object"

    request_json = "[22]"
    with pytest.raises(offchain.FieldError, match="expect json object, but got list: ") as e:
        offchain.from_json(request_json)

    assert e.value.code == "invalid_object"


def test_field_value_because_of_invalid_object_type_for_union_type():
    request_json = """{
  "cid": "3185027f-0574-6f55-2668-3a38fdb5de98",
  "command_type": "PaymentCommand",
  "command": "invalid",
  "_ObjectType": "CommandRequestObject"
}"""
    with pytest.raises(offchain.FieldError, match="expect json object, but got str: ") as e:
        offchain.from_json(request_json)

    assert e.value.code == "invalid_field_value"


def test_invalid_object_type():
    request_json = """{
  "cid": "3185027f-0574-6f55-2668-3a38fdb5de98",
  "command_type": "PaymentCommand",
  "command": {
    "_ObjectType": "InvalidCommand"
  },
  "_ObjectType": "CommandRequestObject"
}"""
    with pytest.raises(offchain.FieldError, match="could not find object type: InvalidCommand") as e:
        offchain.from_json(request_json)

    assert e.value.code == "invalid_field_value"


def test_object_type_is_not_provided_when_it_is_required():
    request_json = {
        "cid": "3185027f-0574-6f55-2668-3a38fdb5de98",
        "command_type": "PaymentCommand",
        "command": {"_ObjectType": "PaymentCommand"},
    }
    assert_field_error(request_json, "missing_field", "_ObjectType", "missing field: _ObjectType")

    request_json = {
        "cid": "3185027f-0574-6f55-2668-3a38fdb5de98",
        "command_type": "PaymentCommand",
        "command": {},
        "_ObjectType": "CommandRequestObject",
    }
    assert_field_error(request_json, "missing_field", "command._ObjectType", "missing field: command._ObjectType")


def test_invalid_enum_field_value():
    request_json = set_field(sample_request_json(), {"command.payment.sender.status.status": "invalid"})
    assert_field_error(
        request_json,
        "invalid_field_value",
        "command.payment.sender.status.status",
        "expect one of \\['none', 'needs_kyc_data', 'ready_for_settlement', 'abort', 'soft_match'\\], but got: invalid",
    )


def test_invalid_uuid_field_value():
    request_json = set_field(sample_request_json(), {"cid": "invalid"})
    assert_field_error(
        request_json,
        "invalid_field_value",
        "cid",
        "invalid does not match pattern",
    )

    request_json = set_field(sample_request_json(), {"command.payment.reference_id": "invalid"})
    assert_field_error(
        request_json,
        "invalid_field_value",
        "command.payment.reference_id",
        "invalid does not match pattern",
    )

    request_json = set_field(sample_request_json(), {"command.payment.original_payment_reference_id": "invalid"})

    assert_field_error(
        request_json,
        "invalid_field_value",
        "command.payment.original_payment_reference_id",
        "invalid does not match pattern",
    )


def test_unknown_field():
    request_json = set_field(
        sample_request_json(),
        {
            "command.payment.sender.status.unknown-field-1": "value",
            "command.payment.sender.status.unknown-field-2": "value",
        },
    )
    assert_field_error(
        request_json,
        "unknown_field",
        "command.payment.sender.status.unknown-field-1",
        "command.payment.sender.status: unknown-field-1, unknown-field-2",
    )


def test_missing_required_field():
    request_json = set_field(sample_request_json(), {"command.payment.sender.status.status": None})
    assert_field_error(
        request_json,
        "missing_field",
        "command.payment.sender.status.status",
        "missing field: command.payment.sender.status.status",
    )


def assert_cid(cid: str):
    assert isinstance(cid, str)
    assert uuid.UUID(cid)
    assert "-" in cid


def assert_field_error(json_dic, code, field, match):
    with pytest.raises(offchain.FieldError, match=match) as e:
        offchain.from_json(json.dumps(json_dic))

    assert e.value.code == code
    assert e.value.field == field


def set_field(root_dic, changes):
    for field, value in changes.items():
        path = field.split(".")
        dic = root_dic
        for f in path[0 : len(path) - 1]:
            if f not in dic:
                dic[f] = {}
            dic = dic[f]

        dic[path[len(path) - 1]] = value
    return root_dic


def sample_request_json():
    return json.loads(
        """{
  "cid": "3185027f-0574-6f55-2668-3a38fdb5de98",
  "command_type": "PaymentCommand",
  "command": {
    "_ObjectType": "PaymentCommand",
    "payment": {
      "reference_id": "2185027f-0574-6f55-2668-3a38fdb5de98",
      "sender": {
        "address": "lbr1p7ujcndcl7nudzwt8fglhx6wxnvqqqqqqqqqqqqelu3xv",
        "status": {
          "status": "needs_kyc_data"
        },
        "kyc_data": {
          "type": "individual",
          "payload_version": 1,
          "given_name": "Jack",
          "surname": "G",
          "address": {
            "city": "San Francisco"
          }
        }
      },
      "receiver": {
        "address": "lbr1p7ujcndcl7nudzwt8fglhx6wxnvqqqqqqqqqqqqelu3xv",
        "status": {
          "status": "none"
        }
      },
      "action": {
        "amount": 1000000000000,
        "currency": "XUS",
        "action": "charge",
        "timestamp": 1609391272
      }
    }
  },
  "_ObjectType": "CommandRequestObject"
}"""
    )
