import hashlib
import typing

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from pylibra import libra_types as libra, serde_types as st

from ._config import LIBRA_HASH_PREFIX
from ._types import LibraLedgerState


def make_libra_account_address(addr: str) -> libra.AccountAddress:
    return libra.AccountAddress(tuple(st.uint8(x) for x in bytes.fromhex(addr)))


def make_addr_str(addr: libra.AccountAddress) -> str:
    return bytes(addr.value).hex()


# TODO (ssinghaldev) can there be better way extract receiver & amount?
# Or shoud we change the get_transaction_status API interface (have separate one for P2P txs) to allow user to give the receiver & amount
def extract_receiver_if_any(signed_tx: libra.SignedTransaction) -> typing.Optional[str]:
    """ If the signed tx is a P2P, extract the receiver from payload """
    txn_payload = signed_tx.raw_txn.payload

    # It should be P2P script
    if isinstance(txn_payload, libra.TransactionPayload__Script):
        script = txn_payload.value

        # P2P script takes 4 arguments -> receiver, amount, metadata, metadata_signature
        if len(script.args) == 4:

            if isinstance(script.args[0], libra.TransactionArgument__Address):
                return make_addr_str(script.args[0].value)


def extract_amount_if_any(signed_tx: libra.SignedTransaction) -> typing.Optional[int]:
    """ If the signed tx is a P2P, extract the transferred amount from payload """
    txn_payload = signed_tx.raw_txn.payload

    # It should be P2P script
    if isinstance(txn_payload, libra.TransactionPayload__Script):
        script = txn_payload.value

        # P2P script takes 4 arguments -> receiver, amount, metadata, metadata_signature
        if len(script.args) == 4:

            if isinstance(script.args[1], libra.TransactionArgument__U64):
                return int(script.args[1].value)


def add_seed_to_raw_tx_bytes(raw_tx_bytes: bytes) -> bytes:
    def _get_seed() -> bytes:
        hash = hashlib.sha3_256()
        hash.update(LIBRA_HASH_PREFIX)
        hash.update(b"RawTransaction")

        return hash.digest()

    seed = _get_seed()

    return seed + raw_tx_bytes


def ed25519_private_key_from_bytes(private_key: bytes) -> Ed25519PrivateKey:
    return ed25519.Ed25519PrivateKey.from_private_bytes(private_key)


def ed25519_sign(private_key: Ed25519PrivateKey, message: bytes) -> bytes:
    return private_key.sign(message)


def validate_ledger_state(
    last_seen_state: LibraLedgerState,
    curr_state: LibraLedgerState,
    minimum_blockchain_timestamp_usecs: typing.Optional[int] = None,
) -> None:
    if curr_state.chain_id != last_seen_state.chain_id:
        raise ValueError(
            f"chain_id mismatch! Expected: {last_seen_state.chain_id} Received: {curr_state.chain_id}"
        )

    if (
        curr_state.blockchain_version < last_seen_state.blockchain_version
        or curr_state.blockchain_timestamp_usecs
        < last_seen_state.blockchain_timestamp_usecs
    ):
        raise ValueError(
            f"Current ledger state stale:\n"
            f"current_blockchain_version: {curr_state.blockchain_version} last_seen_blockchain_version: {last_seen_state.blockchain_version}"
            f"current_blockchain_timestamp_usecs: {curr_state.blockchain_timestamp_usecs} last_seen_blockchain_timestamp_usecs: {last_seen_state.blockchain_timestamp_usecs}"
        )

    if (
        minimum_blockchain_timestamp_usecs
        and curr_state.blockchain_timestamp_usecs < minimum_blockchain_timestamp_usecs
    ):
        raise ValueError(
            f"Current ledger state stale:\n"
            f"current_blockchain_timestamp_usecs: {curr_state.blockchain_timestamp_usecs}  is less than minimum_blockchain_timestamp_usecs: {minimum_blockchain_timestamp_usecs}"
        )
