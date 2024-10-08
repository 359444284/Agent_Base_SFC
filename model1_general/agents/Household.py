import random

from model1_general.agents.BasicAgent import BasicAgent
from model1_general.agents.stockItems.Deposit import Deposit
from model1_general.agents.stockItems.Reserve import Reserve

import numpy as np
from typing import Tuple, List, Dict


class Household(BasicAgent):
    # stock
    STOCK_TYPES = [('DEPOSIT', True), ('CONS_GOOD', True)]

    FLOW_TYPES = [('INTEREST_DEPOSIT', True), ('CONSUMPTION', False), ('WAGE', True)]
    LAG_TYPES = ['EMPLOYED']

    def __init__(self, uid: Tuple, model, isGlobal: bool, paramGroup: int,):
        super().__init__(uid, isGlobal=isGlobal, paramGroup=paramGroup)

        self.params = model.params
        self.context = model.context

        self.wage = 0
        self.interestsReceived = 0
        self.employmentWageLag = 4

        self.employer = None


    def getNetWealth(self):
        return self.globalStocks.CONS_GOOD + self.globalStocks.DEPOSIT

    def getGrossIncome(self):
        grossIncome = self.wage if self.employer else 0
        grossIncome += self.interestsReceived
        # grossIncome += dividendsReceived
        return grossIncome


    def getNetIncome(self):
        # taxes
        if self.employer:
            grossIncome = self.getGrossIncome()
            return grossIncome
        else:
            return 0

    def computeConsumptionDemand(self):
        asset = self.localStocks.DEPOSIT[0].value

        propensityOOI = 0.385
        propensityOOW = 0.25
        netIncome = self.getNetIncome()
        netWealth = self.getNetWealth()

        demand = (propensityOOI * netIncome + propensityOOW * netWealth)
        if demand > 0 or asset > 0:
            return [demand, asset]
        else:
            return None

    def computeWage(self):

        # employmentRate = self.getMicroEmploymentRate()
        # wage = self.wage
        #
        # if employmentRate <= 0.49:
        #     wage -= 0.5 * wage * random.random()
        # else:
        #     macroReferenceVariable = self.getMacroUnemploymentRate()
        #     if macroReferenceVariable <= 0.08:
        #         wage += 0.5 * wage * random.random()
        #
        # self.wage = max(wage, 0)
        return self.wage

    def computeLaborSupply(self):
        self.computeWage()

        if self.employer is not None:
            return [1]
        else:
            return None

    def getMicroEmploymentRate(self):
        if self.employer is None:
            averageEmployment = 0
            for i in range(0, self.employmentWageLag-1):
                averageEmployment += self.lagValues.EMPLOYED[i]

            return averageEmployment / self.employmentWageLag
        else:
            return 0

    def getMacroUnemploymentRate(self):
        if self.employer is None:
            return 0
        else:
            return 0

    def updateLag(self):
        self.lagValues.EMPLOYED.appendleft(1 if self.employer else 0)

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

