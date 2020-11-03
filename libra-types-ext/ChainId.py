
@staticmethod
def from_int(id: int) -> "ChainId":
    return ChainId(value=st.uint8(id))

def to_int(self) -> int:
    return int(self.value)
