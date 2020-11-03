
@staticmethod
def from_raw_txn_and_ed25519_key(
    txn: RawTransaction,
    public_key: bytes,
    signature: bytes
) -> "SignedTransaction":
    return SignedTransaction(
        raw_txn=txn,
        authenticator=TransactionAuthenticator__Ed25519(
            public_key=Ed25519PublicKey(value=public_key),
            signature=Ed25519Signature(value=signature),
        ),
    )
