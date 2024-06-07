class Reserve:
    __slots__ = ['value', 'assetHolder', 'liabilityHolder']

    def __init__(self, value, assetHolder, liabilityHolder):
        self.value = value
        self.assetHolder = assetHolder
        self.liabilityHolder = liabilityHolder