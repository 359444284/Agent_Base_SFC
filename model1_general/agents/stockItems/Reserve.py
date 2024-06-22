from model1_general.agents.BasicAgent import BasicAgent
from typing import Optional
from dataclasses import dataclass


@dataclass(slots=True)
class Reserve:
    value: float
    assetHolder: BasicAgent
    liabilityHolder: BasicAgent
