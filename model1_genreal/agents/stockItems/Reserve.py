class Reserve:
    __slots__ = ['amount', 'assetHolder', 'liabilityHolder']

    def __init__(self, amount, assetHolder, liabilityHolder):
        self.amount = amount
        self.assetHolder = assetHolder
        self.liabilityHolder = liabilityHolder