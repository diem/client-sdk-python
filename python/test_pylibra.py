from pylibra import *

from pylibra import transport

BLOB = bytes.fromhex("020000002100000001674deac5e7fca75f00ca92b1ba3697f5f01ef585011beea7b361150f4504638f0800000002000000000000002100000001a208df134fefed8442b1f01fab59071898f5a1af5164e12c594de55a7004a91c8e0000002000000036ccb9ba8b4f0cd1f3e2d99338806893dff7478c69acee9b8e1247c053783a4800e876481700000000000200000000000000200000000b14ed4f5af8f8f077c7ec4313c6d395b9a7eb5f41eab9ec15367215ca9e420a01000000000000002000000032f56f77b09773aa64c78ee39943da7ec73f91cd757e325098e11b3edc4eccb10100000000000000")


def test_account_state_blob():
    ar = AccountResource.create(BLOB)
    assert ar.balance == 100000000000
    assert ar.sequence == 1
    assert ar.authentication_key == b'6\xcc\xb9\xba\x8bO\x0c\xd1\xf3\xe2\xd9\x938\x80h\x93\xdf\xf7G\x8ci\xac\xee\x9b\x8e\x12G\xc0Sx:H'
    assert ar.delegated_key_rotation_capability == False
    assert ar.delegated_withdrawal_capability == False
    assert ar.sent_events.count == 1
    assert ar.sent_events.key == b'2\xf5ow\xb0\x97s\xaad\xc7\x8e\xe3\x99C\xda~\xc7?\x91\xcdu~2P\x98\xe1\x1b>\xdcN\xcc\xb1'
    assert ar.received_events.count == 2
    assert ar.received_events.key == b'\x0b\x14\xedOZ\xf8\xf8\xf0w\xc7\xecC\x13\xc6\xd3\x95\xb9\xa7\xeb_A\xea\xb9\xec\x156r\x15\xca\x9eB\n'


# TODO setup our own account with mint, so we can test non-zero cases
def test_account_state_block_from_testnet():
    addr_hex = "00" * 32
    blob = transport.get_account_state_blob(addr_hex)
    print("Blob:", blob)

    ar = AccountResource.create(blob)
    assert ar.balance == 0
    assert ar.sequence == 0
    assert ar.authentication_key == bytes.fromhex(addr_hex)
    assert not ar.delegated_key_rotation_capability
    assert not ar.delegated_withdrawal_capability
    assert ar.sent_events.count == 0
    assert ar.sent_events.key == b'\x1d\x05F\xc8)1\xc9\xcaW\xf0\xc2Qe\xf7\xeeb\x97\x0b\xaev\xccW\x02\x0f}\xcdj\xc2\x93\xa3Z\xc3'
    assert ar.received_events.count == 0
    assert ar.received_events.key == b'\xfd\xa6\xe1\xeb\xc2\xf1u\x80(p\xc8\xc0N"\xe7\r\xfe\x18\xd3K\xf7\x02\xcc^0"~\x9d\xa0\xa6\x92\xda'
