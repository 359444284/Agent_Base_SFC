class ConsumptionGood():
    __slots__ = ['value', 'iniValue', 'quantity', 'price', 'startTick', 'length', 'age', 'ObservePeriod', 'assetHolder', 'liabilityHolder']

    def __init__(self,price, quantity, startTick, length, ObservePeriod, assetHolder, liabilityHolder):
        self.value = lambda _: self.quantity * self.price
        self.quantity = quantity
        self.price = price
        self.iniValue = price * quantity
        self.startTick = startTick
        self.length = length
        self.age = length
        self.ObservePeriod = ObservePeriod

        self.assetHolder = assetHolder
        self.liabilityHolder = liabilityHolder
