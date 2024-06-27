import random

from model1_general.agents.BasicAgent import BasicAgent
from model1_general.agents.stockItems.Deposit import Deposit
from model1_general.agents.stockItems.Reserve import Reserve

import numpy as np
from typing import Tuple, List, Dict


class Household(BasicAgent):
    # stock
    STOCK_TYPES = ['DEPOSIT', 'CONS_GOOD']

    EXP_TYPES = ['CONS_PRICE']
    def __init__(self, uid: Tuple, model, isGlobal: bool, paramGroup: int,):
        super().__init__(uid, isGlobal=isGlobal, paramGroup=paramGroup)

        self.params = model.params

        self.wage = 0
        self.interestsReceived = 0

        self.employer = None


    def getNetWealth(self):
        return self.globalStocksNamed.CONS_GOOD + self.globalStocksNamed.DEPOSIT

    def getGrossIncome(self):
        grossIncome = self.wage if self.employer else 0
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
        self.mergeInformationTableData()

        propensityOOI = 0.385
        propensityOOW = 0.25
        priceCoefficient = 0.8 + random.random()*0.4
        netIncome = self.getNetIncome()
        netWealth = self.getNetWealth()

        demand = (propensityOOI*(netIncome/priceCoefficient)+propensityOOW*(netWealth/priceCoefficient))
        return demand

    def getWage(self):
        basicWage = 1
        return max(0, basicWage)

    def updateExpectations(self):
        pass

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
    #             ) = params
    #

