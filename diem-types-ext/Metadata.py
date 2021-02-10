
def decode_structure(self) -> typing.Union[None, 'GeneralMetadataV0', 'TravelRuleMetadataV0', 'RefundMetadataV0']:
    """decode metadata structure

    Returns None for a non-structure type or undefined
    """

    type_index = type(self).INDEX
    if type_index == 1:
        return typing.cast(GeneralMetadataV0, self.value.value)
    elif type_index == 2:
        return typing.cast(TravelRuleMetadataV0, self.value.value)
    elif type_index == 4:
        return typing.cast(RefundMetadataV0, self.value.value)
    elif type_index == 5:
        return typing.cast(CoinTradeMetadataV0, self.value.value)
    return None
