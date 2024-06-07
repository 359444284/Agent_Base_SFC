import random

from agents.BasicAgent import BasicAgent
from agents.stockItems import Deposit, Reserve

import numpy as np
from typing import Tuple, List, Dict


class Household(BasicAgent):
    # stock
    STOCK_AMOUNT = 2
    DEPOSIT_CB = 0
    RESERVE = 1
    ADVANCE = 2

    # flow
    FLOW_AMOUNT = 2
    DEPOSIT_DELTA = 0
    RESERVE_DELTA = 1

    def __init__(self, uid: Tuple, params: Dict, isGlobal: bool, paramGroup: int,):
        super().__init__(uid, isGlobal=isGlobal, paramGroup=paramGroup)

        self.params = params

        self.isEmployed = False
        self.wage = 0
        self.interestsReceived = 0

        self.globalStocks = np.zeros(self.STOCK_AMOUNT)

        # global flow attributes
        self.globalFlows = np.zeros(self.FLOW_AMOUNT)

        # local stock attributes
        self.localStocks = []

        self.Deposits = []
        self.ConsumptionGoods = []

        self.localStocks.append(self.Deposits)
        self.localStocks.append(self.ConsumptionGoods)

        # local flow attributes -- should be reset to 0 after the balance sheet
        self.localFlows = np.zeros(self.FLOW_AMOUNT)

    def getNetWealth(self):
        return self.globalStocks[self.ConsumptionGoods] - self.globalStocks[self.DEPOSIT]

    def getGrossIncome(self):
        grossIncome = self.wage if self.isEmployed else 0
        grossIncome += self.interestsReceived
        # grossIncome += dividendsReceived
        return grossIncome


    def getNetIncome(self):
        # taxes
        if self.isEmployed:
            grossIncome = self.getGrossIncome()
            return grossIncome
        else:
            return 0



    def computeConsumptionDemand(self):
        propensityOOI = 0.385
        propensityOOW = 0.25
        priceCoefficient = 0.8 + random.random()*0.4
        netIncome = self.getNetIncome()
        netWealth = self.getNetWealth()

        demand = (propensityOOI*(netIncome/priceCoefficient)+propensityOOW*(netWealth/priceCoefficient))
        return demand


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


