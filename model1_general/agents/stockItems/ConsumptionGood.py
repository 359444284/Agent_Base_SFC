from model1_general.agents.BasicAgent import BasicAgent
from typing import Optional
from dataclasses import dataclass, field


@dataclass(slots=True)
class ConsumptionGood:
    quantity: int
    price: float
    startTick: int
    length: int
    ObservePeriod: int
    assetHolder: BasicAgent
    liabilityHolder: BasicAgent
    producer: BasicAgent
    iniValue: float = field(init=False)
    age: int = field(init=False)

    def __post_init__(self):
        self.iniValue = self.price * self.quantity
        self.age = self.length

    @property
    def value(self):
        return self.quantity * self.price
