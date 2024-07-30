from model1_general.agents.BasicAgent import BasicAgent
from model1_general.agents.stockItems.Deposit import Deposit
from model1_general.agents.stockItems.Reserve import Reserve
import numpy as np
from typing import Tuple, List, Dict

class CentralPlanner(BasicAgent):
    STOCK_TYPES = [('DEPOSIT', True)]
    FLOW_TYPES = [('INTEREST_DEPOSIT', True)]

    def __init__(self, uid:Tuple, model, isGlobal:bool, paramGroup:int,
                 incrementAndSubstitutions:str, noOrderGeneration:bool, askingInvGoodsProduction:str,
                 investmentVariation:float, randomOrderGeneration:bool, durationCoeff: float):
        super().__init__(uid=uid, isGlobal=isGlobal, paramGroup=paramGroup)

        # params
        self.params = model.params
        self.incrementAndSubstitutions = incrementAndSubstitutions
        self.noOrderGeneration = noOrderGeneration
        self.askingInvGoodsProduction = askingInvGoodsProduction
        self.investmentVariation = investmentVariation
        self.randomOrderGeneration = randomOrderGeneration
        self.durationCoeff = durationCoeff


        self.informationTable = np.zeros((self.params['howManyCycles'], 5))  # col 5 not used multiranks,
        # it only reports gross exp inv in output ##ptpt

        # workingMultirank use it only if rank > 0
        self.theCentralPlannerReporter = 0


        self.proportionalValue = 0
        self.proportionalValue = 0
        
        self.local_extra_info = np.zeros(8)
        self.global_extra_info = np.zeros(8)


    def preparingActions(self, model):

        # workingMultiRank
        # making decisions on assigning investment goods -> one of: ['zero', 'random', 'total','proportionally']
        # IT OCCURS IN THE plannerMethods.py for all the ranks

        # getting information for actions
        if model.t() > 0:
            # here we are summing data for each firm sectorial class
            # COLLECTED INVESTMENT GOODS

            # the planner has to know whether it received the investment goods produced by the firms
            # and it will read it from this information table, which is updated at t-1
            self.local_extra_info[0] = sum(model.totalInvGoodsRevenues[model.t() - 1])
            self.local_extra_info[1] = sum(model.totalInvGoodsInventories[model.t() - 1])
            self.local_extra_info[2] = sum(model.totalGrossInvestmentQ[model.t() - 1])
            currentPrice = model.context.agent(
                (0, self.params['FIRM_TYPE'], model.rank)).currentPriceOfDurableProductiveGoodsPerUnit
            self.local_extra_info[3] = sum(model.totalGrossInvestmentQ[model.t() - 1]) * currentPrice

            self.informationTable[model.t(), 0] = self.local_extra_info[0]
            self.informationTable[model.t(), 1] = self.local_extra_info[1]
            self.informationTable[model.t(), 2] = self.local_extra_info[2]
            self.informationTable[model.t(), 3] = self.local_extra_info[3]

    def diffusingProductionOrders(self, model):

        # no order basic case
        if self.noOrderGeneration:
            for aFirm in model.context.agents(agent_type=self.params['FIRM_TYPE']):
                aFirm.receivingNewOrder(0, \
                                        (aFirm.minOrderDuration + aFirm.maxOrderDuration) / 2)
            return

        invGoodsCapacity = 0
        consGoodsCapacity = 0
        if self.askingInvGoodsProduction == 'min' or self.askingInvGoodsProduction == 'max':
            # comparing firms' productive capacity
            for aFirm in model.context.agents(agent_type=self.params['FIRM_TYPE']):
                if aFirm.productionType in self.params["investmentGoods"]:
                    invGoodsCapacity += len(aFirm.employees) * aFirm.laborProductivity
                else:
                    consGoodsCapacity += len(aFirm.employees) * aFirm.laborProductivity
            consumptionVariation = (1 - self.investmentVariation) * invGoodsCapacity / consGoodsCapacity
            # consumptionVariation is equivalent to investmentVariation
            # accounting for different volumes of prod capacity

        # random order generation
        if self.randomOrderGeneration:
            for aFirm in model.context.agents(agent_type=self.params['FIRM_TYPE']):

                if self.askingInvGoodsProduction == 'regular':
                    aFirm.receivingNewOrder(model.rng.random() * aFirm.maxOrderProduction, \
                                            model.rng.integers(aFirm.minOrderDuration,
                                                         aFirm.maxOrderDuration + 1) * self.durationCoeff)

                elif (self.askingInvGoodsProduction == 'max' and self.investmentVariation > 0) \
                        or (
                        self.askingInvGoodsProduction == 'min' and self.investmentVariation < 0):

                    if aFirm.productionType in self.params['investmentGoods']:
                        # max or min (depending on how the coefficients are built)

                        aFirm.receivingNewOrder(model.rng.random() * aFirm.maxOrderProduction * \
                                                (1 + self.investmentVariation), \
                                                model.rng.integers(aFirm.minOrderDuration, aFirm.maxOrderDuration + 1) \
                                                * self.durationCoeff)
                        # maxOrderProductionMod = aFirm.maxOrderProduction * (1 + self.investmentVariation)
                        # aFirm.receivingNewOrder( \
                        #     maxOrderProductionMod * self.params["minOrderAsAShareOfMaxOrderProduction"] + \
                        #     model.rng.random() * maxOrderProductionMod * (1 - self.params["minOrderAsAShareOfMaxOrderProduction"]), \
                        #     model.rng.integers(aFirm.minOrderDuration,
                        #                  aFirm.maxOrderDuration + 1) * self.durationCoeff)

                    else:
                        aFirm.receivingNewOrder(model.rng.random() * aFirm.maxOrderProduction * (1 + consumptionVariation), \
                                                model.rng.integers(aFirm.minOrderDuration, aFirm.maxOrderDuration + 1) \
                                                * self.durationCoeff)

                        # maxOrderProductionMod = aFirm.maxOrderProduction * (1 + self.investmentVariation)
                        # aFirm.receivingNewOrder( \
                        #     maxOrderProductionMod * self.params["minOrderAsAShareOfMaxOrderProduction"] + \
                        #     model.rng.random() * maxOrderProductionMod * (1 - self.params["minOrderAsAShareOfMaxOrderProduction"]), \
                        #     model.rng.integers(aFirm.minOrderDuration,
                        #                  aFirm.maxOrderDuration + 1) * self.durationCoeff)

                else:
                    aFirm.receivingNewOrder(0, (aFirm.minOrderDuration + aFirm.maxOrderDuration) / 2)
                    print("ERROR! The investment variation coefficient must be consistent\
                    with the askingInvGoodsProduction case ('min' or 'max')")

                    """

                    if plannerMethods.askingInvGoodsProduction == 'regular':
                        aFirm.receivingNewOrder(rng.random()*aFirm.maxOrderProduction,\
                                rng.integers(aFirm.minOrderDuration, aFirm.maxOrderDuration+1))

                    if plannerMethods.askingInvGoodsProduction == 'min':
                        aFirm.receivingNewOrder(rng.random()*(1/plannerMethods.investmentVariation) \
                            * aFirm.maxOrderProduction, rng.integers(aFirm.minOrderDuration, aFirm.maxOrderDuration+1))
                    if plannerMethods.askingInvGoodsProduction == 'max':
                        aFirm.receivingNewOrder(rng.random()*plannerMethods.investmentVariation \
                            * aFirm.maxOrderProduction, rng.integers(aFirm.minOrderDuration, aFirm.maxOrderDuration+1))
                    """

    def generateDemandOrders(self, model):  # planner buying from firms
        # the central planner asks to firm a certain quantity of goods
        # we observe the outcome of this in the firms revenues

        for aFirm in model.context.agents(agent_type=self.params['FIRM_TYPE']):
            shareOfInventoriesBeingSold = self.params['minOfInventoriesBeingSold'] \
                                          + model.rng.random() * self.params['rangeOfInventoriesBeingSold']
            centralPlannerBuyingPriceCoefficient = self.params['centralPlannerPriceCoefficient']  # 0.8 + rng.random()*0.4
            aFirm.receiveSellingOrders(shareOfInventoriesBeingSold, centralPlannerBuyingPriceCoefficient)

    def askFirmsInvGoodsDemand(self, model):

        for aFirm in model.context.agents(agent_type=self.params['FIRM_TYPE']):
            (desiredCapitalQsubstitutions, requiredCapitalQincrement, \
             desiredCapitalSubstitutions, requiredCapitalIncrement) = aFirm.allowInformationToCentralPlanner()


            # TOTALIZING INVESTMENT GOODS REQUESTS
            self.local_extra_info[4] += desiredCapitalQsubstitutions
            self.local_extra_info[5] += requiredCapitalQincrement
            self.local_extra_info[6] += desiredCapitalSubstitutions
            self.local_extra_info[7] += requiredCapitalIncrement

        # print(self.local_extra_info[4:8])


        self.informationTable[model.t(), 4] = self.local_extra_info[6] + self.local_extra_info[7]

    def setProportionalValue(self, model):
        if (self.global_extra_info[6] + self.global_extra_info[7]) != 0:
            self.proportionalValue = self.global_extra_info[0] / (self.global_extra_info[6] + self.global_extra_info[7])

    def executeInvestmentGoodsDemandFromFirms(self, model):
        for aFirm in model.context.agents(agent_type=self.params['FIRM_TYPE']):
            (desiredCapitalQsubstitutions, requiredCapitalQincrement, \
             desiredCapitalSubstitutions, requiredCapitalIncrement) = aFirm.requestGoodsToTheCentralPlanner()

            # UNINFORMED CENTRAL PLANNER

            # give all, give zero, give random quantity, regardless of its previous action

            # give zero
            if self.incrementAndSubstitutions == 'zero':
                capitalQsubstitutions = 0
                capitalQincrement = 0
                capitalSubstitutions = 0
                capitalIncrement = 0

                # give random
            if self.incrementAndSubstitutions == 'random':
                randomValue = model.rng.random()
                totalQIncrementAndSubstitutions = randomValue * (
                            desiredCapitalQsubstitutions + requiredCapitalQincrement)
                totalIncrementAndSubstitutions = randomValue * (desiredCapitalSubstitutions + requiredCapitalIncrement)

                if totalQIncrementAndSubstitutions >= desiredCapitalQsubstitutions:
                    # and then totalIncrementAndSubstitutions >= desiredCapitalSubstitutions
                    capitalQsubstitutions = desiredCapitalQsubstitutions
                    capitalQincrement = totalQIncrementAndSubstitutions - capitalQsubstitutions
                    capitalSubstitutions = desiredCapitalSubstitutions
                    capitalIncrement = totalIncrementAndSubstitutions - capitalSubstitutions
                else:
                    capitalQsubstitutions = totalQIncrementAndSubstitutions
                    capitalQincrement = 0
                    capitalSubstitutions = totalIncrementAndSubstitutions
                    capitalIncrement = 0

            # PARTIALLY INFORMED CENTRAL PLANNER

            # give all
            if self.incrementAndSubstitutions == 'total':
                capitalQsubstitutions = desiredCapitalQsubstitutions
                capitalQincrement = requiredCapitalQincrement
                capitalSubstitutions = desiredCapitalSubstitutions
                capitalIncrement = requiredCapitalIncrement

            # FULLY INFORMED CENTRAL PLANNER ... BUT SHY
            # We introduce the informed central planner, which distritutes the goods under the label 'proportionally'

            if self.incrementAndSubstitutions == 'proportionally':

                if (self.local_extra_info[6] + self.local_extra_info[7]) == 0:
                    capitalQsubstitutions = 0
                    capitalQincrement = 0
                    capitalSubstitutions = 0
                    capitalIncrement = 0

                else:

                    # if aFirm.uid==(0,0,0): print(t(), proportionalValue, flush=True)
                    # if >1 firms have more K than what require and too many inventories


                    totalQIncrementAndSubstitutions = self.proportionalValue * (
                                desiredCapitalQsubstitutions + requiredCapitalQincrement)
                    totalIncrementAndSubstitutions = self.proportionalValue * (
                                desiredCapitalSubstitutions + requiredCapitalIncrement)

                    if totalQIncrementAndSubstitutions >= desiredCapitalQsubstitutions:
                        # and then totalIncrementAndSubstitutions >= desiredCapitalSubstitutions
                        capitalQsubstitutions = desiredCapitalQsubstitutions
                        capitalQincrement = totalQIncrementAndSubstitutions - capitalQsubstitutions
                        capitalSubstitutions = desiredCapitalSubstitutions
                        capitalIncrement = totalIncrementAndSubstitutions - capitalSubstitutions
                    else:
                        capitalQsubstitutions = totalQIncrementAndSubstitutions
                        capitalQincrement = 0
                        capitalSubstitutions = totalIncrementAndSubstitutions
                        capitalIncrement = 0

            # THE WISE CENTRAL PLANNER

            # self.informationTable[t(),1] #unbought inventories of investment goods
            # the inventories will turn out to be useful when the central planner will become wise

            aFirm.investmentGoodsGivenByThePlanner = (capitalQsubstitutions, capitalQincrement, \
                                                      capitalSubstitutions, capitalIncrement)

    def getInformationTableData(self):
        if self.isGhost:
            aggregate_data = (
                self._localFlows.copy(),
                self.aggrigateStocks(self._localStocks),
                self.local_extra_info.copy()
            )

            # -- reset the delta to 0
            return aggregate_data

    def mergeInformationTableData(self):

        if not self.isGhost:

            self._globalStocks[:] = self.aggrigateStocks(self._localStocks)

            # print(self.globalStocks)
            self._globalFlows.fill(0)
            self._globalFlows += self._localFlows
            self.global_extra_info.fill(0)
            self.global_extra_info += self.local_extra_info

            for theReporterGhost in self.reporterGhostList:
                self._globalFlows += theReporterGhost.tmp_info[0]
                self._globalStocks += theReporterGhost.tmp_info[1]
                self.global_extra_info += theReporterGhost.tmp_info[2]
    
    def resetFlows(self):
        self._globalFlows.fill(0)
        self._localFlows.fill(0)
        self.global_extra_info.fill(0)
        self.local_extra_info.fill(0)
        
    def save(self):
        basic_info = super().save()

        params = (
            self.proportionalValue
        )

        return (*basic_info, params)

    def update(self, basic_info, params=None):
        # fill this part
        super().update(basic_info)
        if params is not None:
            (
                self.proportionalValue) = params
