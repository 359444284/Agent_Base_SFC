class Loan():
    __slots__ = ['value', 'iniValue', 'interestRate', 'startTick', 'length', 'age', 'ObservePeriod', 'assetHolder', 'liabilityHolder']

    def __init__(self, value, interestRate, startTick, length, ObservePeriod, assetHolder, liabilityHolder):
        self.value = value
        self.iniValue = value
        self.interestRate = interestRate
        self.startTick = startTick
        self.length = length
        self.age = length
        self.ObservePeriod = ObservePeriod

        self.assetHolder = assetHolder
        self.liabilityHolder = liabilityHolder