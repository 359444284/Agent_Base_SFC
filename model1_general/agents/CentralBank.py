from model1_general.agents.BasicAgent import BasicAgent
from model1_general.agents.stockItems.Deposit import Deposit
from model1_general.agents.stockItems.Reserve import Reserve

import numpy as np
from typing import Tuple, List, Dict

class CentralBank(BasicAgent):

    STOCK_TYPES = [('RESERVE', False), ('ADVANCE', True)]

    FLOW_TYPES = [('INTEREST_ADVANCE', True)]

    def __init__(self, uid: Tuple, model, isGlobal: bool, paramGroup: int,
    advanceInterestRate:float):
        super().__init__(uid, isGlobal=isGlobal, paramGroup=paramGroup)

        self.params = model.params

        self.advanceInterestRate = advanceInterestRate


    # def save(self):
    #     basic_info = super().save()
    #
    #     params = (
    #         None
    #     )
    #
    #     return (*basic_info, params)
    #
    # def update(self, basic_info, params=None):
    #     # fill this part
    #     super().update(basic_info)
    #     if params is not None:
    #         (
    #             None) = params


    