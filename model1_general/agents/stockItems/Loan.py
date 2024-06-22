from model1_general.agents.BasicAgent import BasicAgent
from typing import Optional
from dataclasses import dataclass, field

@dataclass(slots=True)
class Loan:
    value: float
    interestRate: float
    startTick: int
    length: int
    ObservePeriod: int
    assetHolder: BasicAgent
    liabilityHolder: BasicAgent
    iniValue: float = field(init=False)
    age: int = field(init=False)

    def __post_init__(self):
        self.iniValue = self.value
        self.age = self.length
