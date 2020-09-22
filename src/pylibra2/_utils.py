import hashlib
import typing
from dataclasses import dataclass

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from . import libra_types as libra, serde_types as st
from ._config import LIBRA_ADDRESS_LEN, LIBRA_HASH_PREFIX, LIBRA_PRIVATE_KEY_SIZE
from ._types import LibraLedgerState


def make_libra_account_address(addr: str) -> libra.AccountAddress:
    return libra.AccountAddress(
        tuple(st.uint8(x) for x in bytes.fromhex(addr))  # pyre-ignore
    )


def make_addr_str(addr: libra.AccountAddress) -> str:
    return bytes(typing.cast(typing.Iterable[int], addr.value)).hex()


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
                return make_addr_str(
                    typing.cast(
                        libra.TransactionArgument__Address, script.args[0]
                    ).value
                )


def extract_amount_if_any(signed_tx: libra.SignedTransaction) -> typing.Optional[int]:
    """ If the signed tx is a P2P, extract the transferred amount from payload """
    txn_payload = signed_tx.raw_txn.payload

    # It should be P2P script
    if isinstance(txn_payload, libra.TransactionPayload__Script):
        script = txn_payload.value

        # P2P script takes 4 arguments -> receiver, amount, metadata, metadata_signature
        if len(script.args) == 4:

            if isinstance(script.args[1], libra.TransactionArgument__U64):
                return int(
                    typing.cast(libra.TransactionArgument__U64, script.args[1]).value
                )


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


class LibraCryptoUtils:
    @dataclass
    class LibraAccount:
        private_key: bytes
        public_key: bytes
        auth_key: bytes
        address: bytes

        @classmethod
        def create(cls) -> "LibraCryptoUtils.LibraAccount":
            """Create new account

            Returns:
                LibraAccount: a data class containing info for the new account
            """
            private_key_bytes, _ = LibraCryptoUtils.create_new_ed25519_key_pair()
            return cls.create_from_private_key(private_key_bytes=private_key_bytes)

        @classmethod
        def create_from_private_key(
            cls, private_key_bytes: bytes
        ) -> "LibraCryptoUtils.LibraAccount":
            """Create new account from private key

            Args:
                private_key_bytes: Ed25519 private key bytes

            Returns:
                LibraAccount: a data class containing info for the new account
            """
            if len(private_key_bytes) != LIBRA_PRIVATE_KEY_SIZE:
                raise ValueError(f"Invalid private_key_bytes: {private_key_bytes}")

            public_key_bytes = LibraCryptoUtils.ed25519_public_key_from_private_key(
                private_key_bytes
            )
            auth_key, addr = LibraCryptoUtils.create_auth_key_and_addr(public_key_bytes)

            return cls(
                private_key=private_key_bytes,
                public_key=public_key_bytes,
                auth_key=auth_key,
                address=addr,
            )

    @staticmethod
    def create_new_ed25519_key_pair() -> typing.Tuple[bytes, bytes]:
        """ Create a new Ed25519 keypair

            Returns: Tuple[bytes, bytes]: private_key, public_key
        """
        private_key: Ed25519PrivateKey = Ed25519PrivateKey.generate()

        private_key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
        public_key_bytes = LibraCryptoUtils.ed25519_public_key_from_private_key(
            private_key_bytes
        )

        return private_key_bytes, public_key_bytes

    @staticmethod
    def ed25519_public_key_from_private_key(private_key_bytes: bytes) -> bytes:
        if len(private_key_bytes) != LIBRA_PRIVATE_KEY_SIZE:
            raise ValueError(f"Invalid private_key_bytes: {private_key_bytes}")

        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)
        public_key = private_key.public_key()
        return public_key.public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
        )

    @staticmethod
    def ed25519_sign(private_key_bytes: bytes, message: bytes) -> bytes:
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)
        return private_key.sign(message)

    @staticmethod
    def add_seed_to_raw_tx_bytes(raw_tx_bytes: bytes) -> bytes:
        seed = LibraCryptoUtils._get_seed()
        return seed + raw_tx_bytes

    @staticmethod
    def create_auth_key_and_addr(public_key_bytes: bytes) -> typing.Tuple[bytes, bytes]:

        hash = hashlib.sha3_256()
        hash.update(public_key_bytes)
        hash.update(b"\x00")  # Scheme: single key

        auth_key = hash.digest()

        # Last 16 bytes is the address
        addr = auth_key[-LIBRA_ADDRESS_LEN:]

        return auth_key, addr

    @staticmethod
    def _get_seed() -> bytes:
        hash = hashlib.sha3_256()
        hash.update(LIBRA_HASH_PREFIX)
        hash.update(b"RawTransaction")

        return hash.digest()
