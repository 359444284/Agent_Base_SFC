from agents.BasicAgent import BasicAgent
from agents.stockItems import Deposit, Reserve
import numpy as np
from typing import Tuple, List, Dict

class CentralPlanner(BasicAgent):

    def __init__(self, uid:Tuple, params:dict, isGlobal:bool, paramGroup:int,
                 incrementAndSubstitutions:str, noOrderGeneration:bool, askingInvGoodsProduction:str,
                 investmentVariation:float, randomOrderGeneration:bool, durationCoeff: float):
        super().__init__(uid=uid, isGlobal=isGlobal, paramGroup=paramGroup)

        self.params = params

        self.incrementAndSubstitutions = incrementAndSubstitutions
        self.noOrderGeneration = noOrderGeneration
        self.askingInvGoodsProduction = askingInvGoodsProduction
        self.investmentVariation = investmentVariation
        self.randomOrderGeneration = randomOrderGeneration
        self.durationCoeff = durationCoeff


        self.informationTable = np.zeros((params['howManyCycles'], 5))  # col 5 not used multiranks,
        # it only reports gross exp inv in output ##ptpt
        # workingMultirank only
        self.informationTableMultirank = np.zeros(4)
        self.allFirmsDesiredCapitalQsubstitutionsMultirank = 0
        self.allFirmsRequiredCapitalQincrementMultirank = 0
        self.allFirmsDesiredCapitalSubstitutionsMultirank = 0
        self.allFirmsRequiredCapitalIncrementMultirank = 0
        # workingMultirank use it only if rank > 0
        self.theCentralPlannerReporter = 0


        self.proportionalValue = 0

        self.Deposits = []
        self.localStocks = []
        self.localStocks.append(self.Deposits)
        self.globalStocks = np.zeros(1)

        self.globalFlows = np.zeros(8)
        self.localFlows = np.zeros(8)


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

            self.informationTable[model.t(), 0] = sum(model.totalInvGoodsRevenues[
                                                          model.t() - 1])  # inv goods bought by the planner=sum(model.totalInvGoodsRevenues[t()-1]) #inv goods bought by the planner
            self.informationTable[model.t(), 1] = sum(
                model.totalInvGoodsInventories[model.t() - 1])  # unbought and still available for the planner (stock)
            self.informationTable[model.t(), 2] = sum(model.totalGrossInvestmentQ[model.t() - 1])
            currentPrice = model.context.agent(
                (0, self.params['FIRM_TYPE'], model.rank)).currentPriceOfDurableProductiveGoodsPerUnit
            self.informationTable[model.t(), 3] = sum(model.totalGrossInvestmentQ[model.t() - 1]) * currentPrice

            self.localFlows[0] = sum(model.totalInvGoodsRevenues[model.t() - 1])
            self.localFlows[1] = sum(model.totalInvGoodsInventories[model.t() - 1])
            self.localFlows[2] = sum(model.totalGrossInvestmentQ[model.t() - 1])
            self.localFlows[3] = sum(model.totalGrossInvestmentQ[model.t() - 1]) * currentPrice



            # workingMultiRank
        # if rank>0 sending infos to the centralPlannerReporter
        if model.rank > 0:
            self.theCentralPlannerReporter.informationTableLastCols(
            self.informationTable[model.t(), 0], \
            self.informationTable[model.t(), 1], \
            self.informationTable[model.t(), 2], \
            self.informationTable[model.t(), 3])

    def mergeInformationTableData1(self, theCentralPlannerReporterGhostList, model):
        # merge data from central planner reporter ghosts
        # starting with rank 0's data and adding those of the others ranks in the for cycle
        for j in range(4):
            if model.rank == 0: self.informationTableMultirank[j] = self.informationTable[model.t(), j]
            for i in range(1, model.rankNum):
                self.informationTableMultirank[j] += \
                    theCentralPlannerReporterGhostList[i - 1].informationTableLastCol[j]
                # to be used ONLY to calculate the proportionalValue in multirank runs

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
                    invGoodsCapacity += aFirm.labor * aFirm.laborProductivity
                else:
                    consGoodsCapacity += aFirm.labor * aFirm.laborProductivity
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

                    else:
                        aFirm.receivingNewOrder(model.rng.random() * aFirm.maxOrderProduction * (1 + consumptionVariation), \
                                                model.rng.integers(aFirm.minOrderDuration, aFirm.maxOrderDuration + 1) \
                                                * self.durationCoeff)
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

        self.allFirmsDesiredCapitalQsubstitutions = 0
        self.allFirmsRequiredCapitalQincrement = 0
        self.allFirmsDesiredCapitalSubstitutions = 0
        self.allFirmsRequiredCapitalIncrement = 0

        for aFirm in model.context.agents(agent_type=self.params['FIRM_TYPE']):
            (desiredCapitalQsubstitutions, requiredCapitalQincrement, \
             desiredCapitalSubstitutions, requiredCapitalIncrement) = aFirm.allowInformationToCentralPlanner()

            # TOTALIZING INVESTMENT GOODS REQUESTS
            self.allFirmsDesiredCapitalQsubstitutions += desiredCapitalQsubstitutions
            self.allFirmsRequiredCapitalQincrement += requiredCapitalQincrement
            self.allFirmsDesiredCapitalSubstitutions += desiredCapitalSubstitutions
            self.allFirmsRequiredCapitalIncrement += requiredCapitalIncrement


        ##ptpt
        # to report in output the gross expected investments in value
        self.informationTable[model.t(), 4] = self.allFirmsDesiredCapitalSubstitutions + \
                                              self.allFirmsRequiredCapitalIncrement

        # workingMultiRank
        # if rank>0 sending infos to the centralPlannerReporter
        if model.rank > 0:
            self.theCentralPlannerReporter.invGoodsDemand(
            self.allFirmsDesiredCapitalQsubstitutions, \
            self.allFirmsRequiredCapitalQincrement, \
            self.allFirmsDesiredCapitalSubstitutions, \
            self.allFirmsRequiredCapitalIncrement)

        self.localFlows[4] = self.allFirmsDesiredCapitalQsubstitutions
        self.localFlows[5] = self.allFirmsRequiredCapitalQincrement
        self.localFlows[6] = self.allFirmsDesiredCapitalSubstitutions
        self.localFlows[7] = self.allFirmsRequiredCapitalIncrement


    def mergeInvGoodsDemand(self, theCentralPlannerReporterGhostList, model):
        if model.rank == 0:
            self.allFirmsDesiredCapitalQsubstitutionsMultirank = self.allFirmsDesiredCapitalQsubstitutions
            self.allFirmsRequiredCapitalQincrementMultirank = self.allFirmsRequiredCapitalQincrement
            self.allFirmsDesiredCapitalSubstitutionsMultirank = self.allFirmsDesiredCapitalSubstitutions
            self.allFirmsRequiredCapitalIncrementMultirank = self.allFirmsRequiredCapitalIncrement

        for i in range(1, model.rankNum):
            # print("rank",i,theCentralPlannerReporterGhostList[i-1].invGoodsDemandList,flush=True)
            self.allFirmsDesiredCapitalQsubstitutionsMultirank += \
                theCentralPlannerReporterGhostList[i - 1].invGoodsDemandList[0]
            self.allFirmsRequiredCapitalQincrementMultirank += \
                theCentralPlannerReporterGhostList[i - 1].invGoodsDemandList[1]
            self.allFirmsDesiredCapitalSubstitutionsMultirank += \
                theCentralPlannerReporterGhostList[i - 1].invGoodsDemandList[2]
            self.allFirmsRequiredCapitalIncrementMultirank += \
                theCentralPlannerReporterGhostList[i - 1].invGoodsDemandList[3]

    # used if the proportionally option is active
    def setProportionalValue(self, model):
        if model.rankNum == 1:
            if (self.allFirmsDesiredCapitalSubstitutions + self.allFirmsRequiredCapitalIncrement) != 0:
                self.proportionalValue = self.informationTable[model.t(), 0] \
                                         / (
                                                     self.allFirmsDesiredCapitalSubstitutions + self.allFirmsRequiredCapitalIncrement)

        else:
            if (
                    self.allFirmsDesiredCapitalSubstitutionsMultirank + self.allFirmsRequiredCapitalIncrementMultirank) != 0:
                self.proportionalValue = self.informationTableMultirank[0] \
                                         / (
                                                     self.allFirmsDesiredCapitalSubstitutionsMultirank + self.allFirmsRequiredCapitalIncrementMultirank)

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

                if (self.allFirmsDesiredCapitalSubstitutions + self.allFirmsRequiredCapitalIncrement) == 0:
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

    def resetAttribute(self):

        self.globalFlows.fill(0)
        self.localFlows.fill(0)

    def save(self):
        basic_info = super().save()

        params = (
            self.isGlobal,
            self.paramGroup,
            self.proportionalValue,
        )

        return (*basic_info, params)

    def update(self, basic_info, params=None):
        # fill this part
        super().update(basic_info)
        if params is not None:
            (
                self.isGlobal,
                self.paramGroup,
                self.proportionalValue) = params
