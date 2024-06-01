class Loan():
    __slots__ = ['amount', 'iniAmount', 'interestRate', 'startTick', 'length', 'age', 'ObservePeriod', 'assetHolder', 'liabilityHolder']

    def __init__(self, amount, interestRate, startTick, length, ObservePeriod, assetHolder, liabilityHolder):
        self.amount = amount
        self.iniAmount = amount
        self.interestRate = interestRate
        self.startTick = startTick
        self.length = length
        self.age = length
        self.ObservePeriod = ObservePeriod

        self.assetHolder = assetHolder
        self.liabilityHolder = liabilityHolder