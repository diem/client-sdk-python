from pylibra import AccountResource

BLOB = bytes.fromhex(
    "020000002100000001674deac5e7fca75f00ca92b1ba3697f5f01ef585011beea7b361150f4504638f0800000002000000000000002100000001a208df134fefed8442b1f01fab59071898f5a1af5164e12c594de55a7004a91c8e0000002000000036ccb9ba8b4f0cd1f3e2d99338806893dff7478c69acee9b8e1247c053783a4800e876481700000000000200000000000000200000000b14ed4f5af8f8f077c7ec4313c6d395b9a7eb5f41eab9ec15367215ca9e420a01000000000000002000000032f56f77b09773aa64c78ee39943da7ec73f91cd757e325098e11b3edc4eccb10100000000000000"
)


def test_account_state_blob():
    ar = AccountResource.create(BLOB)
    assert ar.balance == 100000000000
    assert ar.sequence == 1
    assert (
        ar.authentication_key
        == b"6\xcc\xb9\xba\x8bO\x0c\xd1\xf3\xe2\xd9\x938\x80h\x93\xdf\xf7G\x8ci\xac\xee\x9b\x8e\x12G\xc0Sx:H"
    )
    assert ar.delegated_key_rotation_capability is False
    assert ar.delegated_withdrawal_capability is False
    assert ar.sent_events.count == 1
    assert (
        ar.sent_events.key == b"2\xf5ow\xb0\x97s\xaad\xc7\x8e\xe3\x99C\xda~\xc7?\x91\xcdu~2P\x98\xe1\x1b>\xdcN\xcc\xb1"
    )
    assert ar.received_events.count == 2
    assert (
        ar.received_events.key
        == b"\x0b\x14\xedOZ\xf8\xf8\xf0w\xc7\xecC\x13\xc6\xd3\x95\xb9\xa7\xeb_A\xea\xb9\xec\x156r\x15\xca\x9eB\n"
    )
