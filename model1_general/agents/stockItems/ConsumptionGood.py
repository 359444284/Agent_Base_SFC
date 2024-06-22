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
    iniValue: float = field(init=False)
    age: int = field(init=False)
    value: callable = field(init=False)

    def __post_init__(self):
        self.iniValue = self.price * self.quantity
        self.age = self.length
        # Lambda to calculate value, set up after the object is fully initialized
        self.value = lambda: self.quantity * self.price
