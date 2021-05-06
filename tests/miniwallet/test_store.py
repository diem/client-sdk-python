# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


from diem.testing.miniwallet.app import store, Event, PaymentCommand, Account, Subaddress
import pytest


def test_create_event():
    s = store.InMemoryStore()
    event = s.create_event("1", "create-abc", "test data")
    assert event.id
    assert event.account_id == "1"
    assert event.type == "create-abc"
    assert event.data == "test data"
    assert event.timestamp

    assert s.find_all(Event) == [event]


def test_create_with_id():
    s = store.InMemoryStore()
    account = s.create(Account, id="abc")
    assert account.id == "abc"


def test_find_returns_one_matched_item():
    s = store.InMemoryStore()
    s.create_event("1", "create-abc", "test data")
    second = s.create_event("1", "create-hello", "test data")
    s.create_event("1", "create-world", "test data")
    s.create_event("1", "create-abc", "test data")

    assert s.find(Event, type="create-hello") == second

    with pytest.raises(store.NotFoundError):
        s.find(Event, account_id="unknown")
    with pytest.raises(ValueError):
        s.find(Event, account_id="1")


def test_find_all():
    s = store.InMemoryStore()
    assert s.find_all(Event) == []
    one = s.create_event("1", "create-abc", "test data")
    two = s.create_event("1", "create-hello", "test data")
    three = s.create_event("1", "create-world", "test data")
    four = s.create_event("1", "create-abc", "test data")
    assert s.find_all(Event) == [one, two, three, four]


def test_find_all_by_matching_default_none():
    s = store.InMemoryStore()
    cmd = s.create(
        PaymentCommand, account_id="1", reference_id="2", cid="3", is_sender=True, process_error=None, payment_object={}
    )
    assert s.find_all(PaymentCommand, process_error=None, account_id="1") == [cmd]
    assert s.find_all(PaymentCommand, currency="XUS") == []


def test_find_all_by_matching_default_bool_values():
    s = store.InMemoryStore()
    cmd = s.create(PaymentCommand, account_id="1", reference_id="2", cid="3", is_sender=True, payment_object={})
    assert cmd
    assert s.find_all(PaymentCommand, is_inbound=False) == [cmd]
    assert s.find_all(PaymentCommand, is_inbound=True) == []


def test_before_create_hook():
    s = store.InMemoryStore()

    def validate(data):
        raise ValueError("before create error")

    with pytest.raises(ValueError, match="before create error"):
        s.create(Event, before_create=validate)

    assert s.find_all(Event) == []


def test_before_update_hook():
    s = store.InMemoryStore()
    event = s.create(Event, account_id="1", type="hello", data="world", timestamp=11)

    def validate(data):
        raise ValueError("before update error")

    with pytest.raises(ValueError, match="before update error"):
        s.update(event, before_update=validate)


def test_next_id():
    s = store.InMemoryStore()
    for i in range(100):
        assert s.next_id() == i + 1


def test_create_should_create_record_event():
    s = store.InMemoryStore()
    s.create(Subaddress, account_id="account_123", subaddress_hex="cf64428bdeb62af2")
    events = s.find_all(Event)
    assert len(events) == 1
    assert events[0].account_id == "account_123"
    assert events[0].type == "created_subaddress"
    assert events[0].data == '{"account_id": "account_123", "subaddress_hex": "cf64428bdeb62af2", "id": "1"}'


def test_update():
    s = store.InMemoryStore()
    subaddress = s.create(Subaddress, account_id="account_123", subaddress_hex="cf64428bdeb62af2")

    s.update(subaddress, subaddress_hex="aaaaa28bdeb62af2")
    assert subaddress.subaddress_hex == "aaaaa28bdeb62af2"
    assert s.find(Subaddress, id=subaddress.id).subaddress_hex == "aaaaa28bdeb62af2"
    events = s.find_all(Event)
    assert len(events) == 2
    assert events[1].account_id == "account_123"
    assert events[1].type == "updated_subaddress"
    assert events[1].data == '{"subaddress_hex": "aaaaa28bdeb62af2", "id": "1"}'


def test_record_create_account_event():
    s = store.InMemoryStore()
    assert s.create(Account, kyc_data="kyc-data")
    events = s.find_all(Event)
    assert len(events) == 1
    assert events[0].account_id == "1"
    assert events[0].type == "created_account"


def test_update_obj_not_found():
    s = store.InMemoryStore()
    subaddress = s.create(Subaddress, account_id="1", subaddress_hex="cf64428bdeb62af2")
    subaddress.id = "unknown"
    with pytest.raises(store.NotFoundError):
        s.update(subaddress, subaddress_hex="0000000000000000")
