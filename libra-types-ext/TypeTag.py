
CORE_CODE_ADDRESS: AccountAddress = AccountAddress.from_hex("00000000000000000000000000000001")

@staticmethod
def from_currency_code(code: str) -> "TypeTag":
    if isinstance(code, str):
        return TypeTag__Struct(
            value=StructTag(
                address=TypeTag.CORE_CODE_ADDRESS,
                module=Identifier(code),
                name=Identifier(code),
                type_params=[],
            )
        )

    raise TypeError(f"unknown currency code type: {code}")


def to_currency_code(self) -> str:
    if isinstance(self, TypeTag__Struct):
        return self.value.name.value

    raise TypeError(f"unknown currency code type: {self}")
