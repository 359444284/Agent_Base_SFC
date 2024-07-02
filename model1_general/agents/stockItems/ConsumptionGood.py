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
    value: float = field(init=False)

    def __post_init__(self):
        self.iniValue = self.price * self.quantity
        self.age = self.length
        self._update_value()

    def _update_value(self):
        self.value = self.quantity * self.price
