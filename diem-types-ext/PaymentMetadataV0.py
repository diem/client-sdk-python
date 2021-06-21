def to_bytes(self) -> bytes:
    """Convert reference_id to bytes."""
    return bytes(typing.cast(typing.Iterable[int], self.reference_id))
