from model1_general.agents.BasicAgent import BasicAgent
from model1_general.agents.stockItems.Deposit import Deposit
from model1_general.agents.stockItems.Reserve import Reserve
from model1_general.agents.stockItems.ConsumptionGood import ConsumptionGood
import numpy as np
from typing import Tuple, List, Dict
import random
def any(iterable):
    for element in iterable:
        if element != 0:
            return True
    return False


class Firm(BasicAgent):
    STOCK_TYPES = [('DEPOSIT', True), ('LOAN', False), ('CONS_GOOD', True), ('DEPOSIT_Q', True)]
    FLOW_TYPES = [('INTEREST_DEPOSIT', True), ('INTEREST_LOAN', False), ('CONSUMPTION', False)]
    LAG_TYPES = ['REAL_SALES']

    def __init__(self, uid: Tuple, model, isGlobal: bool, paramGroup: int,
                 labor: int, capital:float, minOrderDuration: int, maxOrderDuration: int, recipe: float, laborProductivity: float, maxOrderProduction: float, \
                 assetsUsefulLife: float, plannedMarkup: float, orderObservationFrequency: int, productionType: int):
        super().__init__(uid=uid, isGlobal=isGlobal, paramGroup=paramGroup)


        self.params = model.params
        self.model = model

        self.laborExpect = labor
        self.iniCapital = capital
        self.minOrderDuration = minOrderDuration
        self.maxOrderDuration = maxOrderDuration
        self.recipe = recipe
        self.laborProductivity = laborProductivity
        self.maxOrderProduction = maxOrderProduction
        self.assetsUsefulLife = assetsUsefulLife
        self.plannedMarkup = plannedMarkup
        self.orderObservationFrequency = orderObservationFrequency
        self.productionType = productionType
        self.sectorialClass = paramGroup


        # local stock attributes

        self.unavailableLabor = 0
        self.unavailableCapitalQ = 0
        self.lostProduction = 0
        self.inventories = 0
        self.inProgressInventories = 0
        self.appRepository = []  # aPP is aProductiveProcess

        self.profits = 0
        self.revenues = 0
        self.totalCosts = 0
        self.totalCostOfLabor = 0
        self.totalCostOfCapital = 0
        self.addedValue = 0
        self.initialInventories = 0
        self.grossInvestmentQ = 0

        self.receiveLoan = 0
        self.desiredOutput = None
        self.price = 0
        self.markUp = 0
        self.lag_sales = 0
        self.myBalancesheet = np.zeros((self.params['howManyCycles'], 20))

        self.movAvQuantitiesInEachPeriod = []
        self.movAvDurations = []

        self.productiveProcessIdGenerator = 0

        self.theCentralPlanner = 0




        self.employees = []


    # activated by the Model
    def estimatingInitialPricePerProdUnit(self):

        total = (1 / self.laborProductivity) * self.params['wage']
        total += (1 / self.laborProductivity) * self.recipe * self.params['costOfCapital'] / self.params['timeFraction']
        total += (1 / self.laborProductivity) * self.recipe / (self.assetsUsefulLife * self.params['timeFraction'])
        if self.params['usingMarkup']: total *= (1 + self.plannedMarkup)
        total *= ((self.maxOrderDuration + self.minOrderDuration) / 2)
        return total

    def settingCapitalQ(self, investmentGoodPrices):
        #############pt temporary solution
        # we temporary use this vector with a unique position as there is only one investment good at the moment
        self.priceOfDurableProductiveGoodsPerUnit = investmentGoodPrices[0]  # 1
        self.currentPriceOfDurableProductiveGoodsPerUnit = investmentGoodPrices[
            0]  # 1  # the price to be paid to acquire
        # new capital in term of quantity

        # pt TMP TMP TMP TMP TMP TMP TMP TMP TMP TMP TMP TMP TMP TMP TMP TMP TMP TMP TMP
        #############   underlying idea:
        #               the actual initial price of durable productive goods (per unit of quantity) must be
        #               consistent with the initial cost of production of the durable productive goods;
        #
        #               the recipe set the ratio K/L where K is expressed in value;
        #
        #               having a price we implicitly set the "quantity";
        #
        #               substitution costs will consider both the change of the quantity and of the price
        #               at which the firm will pay the new productive goods;
        #
        #               the used v. unused capital measures are calculated as addenda of the capital in quantity
        #
        #               the costOfCapital (ratio of interests or rents) will be applied to the current value
        #               of the capital, after calculating the changes in quantity and then in value (considering
        #               changes in q. and their value using the price of the new acquisitions)
        #
        #               as it evolves over time, the mean price of durable productive goods is an idiosyncratic
        #               property of the firm
        #
        #               L productivity is expressed in quantity as orders are expressed in quantity

        self.resetCapitalQ()

    # For simplify, we assume that firms do not need to buy capital goods.
    def resetCapitalQ(self):
        capitalQ_ratio = 0.8
        total_capital = (self.localStocks.DEPOSIT[0].value + self.localStocks.DEPOSIT_Q[0].quantity * self.priceOfDurableProductiveGoodsPerUnit)
        reallocatedCapitalQ =  total_capital * capitalQ_ratio
        reallocatedCapital = total_capital * (1 - capitalQ_ratio)

        self.localStocks.DEPOSIT_Q[0].quantity = reallocatedCapitalQ / self.priceOfDurableProductiveGoodsPerUnit
        self.localStocks.DEPOSIT_Q[0].priceOfDurableProductiveGoodsPerUnit = self.priceOfDurableProductiveGoodsPerUnit

        self.localStocks.DEPOSIT[0].value = reallocatedCapital

        # self.capitalQ = self.capital / self.priceOfDurableProductiveGoodsPerUnit
        # self.localStocks.CAP_GOOD[0].value = self.capital / self.priceOfDurableProductiveGoodsPerUnit


    def dealingMovAvElements(self, freq, x, y):

        self.movAvQuantitiesInEachPeriod.append(x / y)
        if len(self.movAvQuantitiesInEachPeriod) > freq: self.movAvQuantitiesInEachPeriod.pop(0)

        self.movAvDurations.append(y)
        if len(self.movAvDurations) > freq: self.movAvDurations.pop(0)

    def receivingNewOrder(self, productionOrder: float, orderDuration):

        # creates a statistics of the values of the received order
        self.dealingMovAvElements(self.orderObservationFrequency, productionOrder, orderDuration)

        # decision on accepting or refusing the new order
        productionOrderQuantityByPeriod = productionOrder / orderDuration
        requiredLabor = np.ceil(productionOrderQuantityByPeriod / self.laborProductivity)
        requiredCapitalQ = requiredLabor * self.recipe / self.priceOfDurableProductiveGoodsPerUnit
        # if self.uid[0]==29 and self.uid[2]==2:
        #    print("***1",t(),"new order q. per period", productionOrderQuantityByPeriod,\
        #          "req L", requiredLabor, "L", self.labor)

        # create a new aPP or skip the order
        if requiredLabor <= len(self.employees) and requiredCapitalQ <= self.localStocks.DEPOSIT_Q[0].quantity:
            self.productiveProcessIdGenerator += 1
            productiveProcessId = (self.uid[0], self.uid[1], self.uid[2], self.productiveProcessIdGenerator)
            aProductiveProcess = ProductiveProcess(productiveProcessId, productionOrderQuantityByPeriod, \
                                                   requiredLabor, requiredCapitalQ, orderDuration, \
                                                   self.priceOfDurableProductiveGoodsPerUnit, \
                                                   self.assetsUsefulLife)
            self.appRepository.append(aProductiveProcess)

    def produce(self, current_time, rng) -> tuple:

        # total values of the firm in the current interval unit
        self.currentTotalCostOfProductionOrder = 0
        self.currentTotalOutput = 0
        self.currentTotalCostOfUnusedFactors = 0
        self.currentTotalLostProduction = 0
        self.currentTotalCostOfLostProduction = 0

        avgRequiredLabor = 0
        avgRequiredCapitalQ = 0

        if current_time == 0:
            self.initialInventories = 0
        else:
            self.initialInventories = self.inventories + self.inProgressInventories

        # activity within a time unit
        for aProductiveProcess in self.appRepository:

            if not aProductiveProcess.hasResources and \
                    (len(self.employees) - self.unavailableLabor >= aProductiveProcess.requiredLabor and \
                     self.localStocks.DEPOSIT_Q[0].quantity - self.unavailableCapitalQ >= aProductiveProcess.requiredCapitalQ):
                self.unavailableLabor += aProductiveProcess.requiredLabor
                self.unavailableCapitalQ += aProductiveProcess.requiredCapitalQ
                aProductiveProcess.hasResources = True

            if aProductiveProcess.hasResources:  # resources may be just assigned above
                # production
                (aPPoutputOfThePeriod, aPPrequiredLabor, aPPrequiredCapitalQ, aPPlostProduction, \
                 aPPcostOfLostProduction) = aProductiveProcess.step(rng, self.params)

                self.currentTotalOutput += aPPoutputOfThePeriod

                cost = aPPrequiredLabor * self.params['wage'] \
                       + aPPrequiredCapitalQ * self.priceOfDurableProductiveGoodsPerUnit \
                       * self.params['costOfCapital'] / self.params['timeFraction'] \
                       + aPPrequiredCapitalQ * self.priceOfDurableProductiveGoodsPerUnit / \
                       (self.assetsUsefulLife * self.params['timeFraction'])

                self.currentTotalCostOfProductionOrder += cost

                self.currentTotalLostProduction += aPPlostProduction
                self.currentTotalCostOfLostProduction += aPPcostOfLostProduction

                if not self.params['usingMarkup']: self.plannedMarkup = 0
                if aProductiveProcess.failure:
                    # consider markup
                    self.inProgressInventories -= cost * (aProductiveProcess.productionClock - 1) * (
                                1 + self.plannedMarkup)

                    # NB this is an approximation because in multiperiodal production processes the
                    #   priceOfDurableProductiveGoodsPerUnit may change, but it is a realistic
                    #   approximation in firm accounting

                else:
                    if aProductiveProcess.productionClock < aProductiveProcess.orderDuration:
                        self.inProgressInventories += cost * (1 + self.plannedMarkup)  # consider markup
                    else:
                        self.inventories += cost * aProductiveProcess.orderDuration * (1 + self.plannedMarkup)
                        cons_goods = self.localStocks.CONS_GOOD[0]

                        cons_goods.quantity += cost * aProductiveProcess.orderDuration * (1 + self.plannedMarkup)
                        self.inProgressInventories -= cost * (aProductiveProcess.orderDuration - 1) * (
                                    1 + self.plannedMarkup)
                        # consider markup (it is added in the final and subtracted by the inProgress)

        self.currentTotalCostOfUnusedFactors = (len(self.employees) - self.unavailableLabor) * self.params['wage'] + \
                                               (self.localStocks.DEPOSIT_Q[0].quantity - self.unavailableCapitalQ) * \
                                               self.priceOfDurableProductiveGoodsPerUnit * \
                                               self.params['costOfCapital'] / self.params['timeFraction'] + \
                                               (self.localStocks.DEPOSIT_Q[0].quantity - self.unavailableCapitalQ) * \
                                               self.priceOfDurableProductiveGoodsPerUnit / \
                                               (self.assetsUsefulLife * self.params['timeFraction'])
        # considering substitutions also for the idle capital

        # print("ORDER MOV AV",self.uid, sum(self.movAvQuantitiesInEachPeriod)/ len(self.movAvQuantitiesInEachPeriod), flush=True)
        avgRequiredLabor = np.ceil(
            ((sum(self.movAvQuantitiesInEachPeriod) / len(self.movAvQuantitiesInEachPeriod)) / self.laborProductivity) \
            * (sum(self.movAvDurations) / len(self.movAvDurations)))

        # total cost of labor
        self.totalCostOfLabor = len(self.employees) * self.params['wage']

        # labor adjustments (frequency at orderObservationFrequency)
        if current_time % self.orderObservationFrequency == 0 and current_time > 0:
            if len(self.employees) > (1 + self.params['tollerance']) * avgRequiredLabor:
                self.laborExpect = np.ceil((1 + self.params['tollerance']) * avgRequiredLabor)  # max accepted q. of L (firing)
            if len(self.employees) < (1 / (1 + self.params['tollerance'])) * avgRequiredLabor:
                self.laborExpect = np.ceil(
                    (1 / (1 + self.params['tollerance'])) * avgRequiredLabor)  # min accepted q. of L (hiring)
            # if self.uid==(32,0,0): print("***",self.uid, "labM",avgRequiredLabor,"L", self.labor, flush=True)

        # capital adjustments (frequency at each cycle)
        # here the following variables are disambiguated between actual and desired values, so they appear in a double shape:
        # i) capital and capitalQ, ii) desiredCapitalSubstistutions and desiredCapitalQsubstitutions

        self.capitalBeforeAdjustment = self.localStocks.DEPOSIT[0].value
        desiredCapitalQsubstitutions = 0
        desiredCapitalSubstitutions = 0
        requiredCapitalQincrement = 0
        requiredCapitalIncrement = 0

        if current_time > self.orderObservationFrequency:  # no corrections before the end of the first correction interval
            # where orders are under the standard flow of the firm
            capitalQmin = self.localStocks.DEPOSIT_Q[0].quantity / (1 + self.params['tollerance'])
            capitalQmax = self.localStocks.DEPOSIT_Q[0].quantity * (1 + self.params['tollerance'])

            avgRequiredCapital = avgRequiredLabor * self.recipe
            avgRequiredCapitalQ = avgRequiredCapital / self.currentPriceOfDurableProductiveGoodsPerUnit

            requiredCapitalSubstitution = self.localStocks.DEPOSIT[0].value / (self.assetsUsefulLife * self.params['timeFraction'])
            requiredCapitalSubstitutionQ = self.localStocks.DEPOSIT_Q[0].value / (self.assetsUsefulLife * self.params['timeFraction'])

            # obsolescence  and deterioration effect
            self.localStocks.DEPOSIT[0].value -= requiredCapitalSubstitution
            self.localStocks.DEPOSIT_Q[0].quantity -= requiredCapitalSubstitutionQ

            a = (-requiredCapitalSubstitutionQ)
            # A=(-requiredCapitalSubstitution)

            # case I
            if avgRequiredCapitalQ < capitalQmin:
                b = avgRequiredCapitalQ - capitalQmin  # being b<0
                # quantities
                if b <= a: desiredCapitalQsubstitutions = 0
                if b > a: desiredCapitalQsubstitutions = abs(a) - abs(b)

                # values
                desiredCapitalSubstitutions = desiredCapitalQsubstitutions * self.currentPriceOfDurableProductiveGoodsPerUnit

            # case II
            if capitalQmin <= avgRequiredCapitalQ and avgRequiredCapitalQ <= capitalQmax:
                # quantities
                desiredCapitalQsubstitutions = abs(a)

                # values
                desiredCapitalSubstitutions = desiredCapitalQsubstitutions * self.currentPriceOfDurableProductiveGoodsPerUnit

            # case III
            if avgRequiredCapitalQ > capitalQmax:
                # quantities
                desiredCapitalQsubstitutions = abs(a)
                requiredCapitalQincrement = avgRequiredCapitalQ - capitalQmax

                # values
                desiredCapitalSubstitutions = desiredCapitalQsubstitutions * self.currentPriceOfDurableProductiveGoodsPerUnit
                requiredCapitalIncrement = requiredCapitalQincrement * self.currentPriceOfDurableProductiveGoodsPerUnit

        self.desiredCapitalQsubstitutions = desiredCapitalQsubstitutions
        self.requiredCapitalQincrement = requiredCapitalQincrement
        self.desiredCapitalSubstitutions = desiredCapitalSubstitutions
        self.requiredCapitalIncrement = requiredCapitalIncrement

        # =========================================================================================
        # the key local variables are:
        #
        # desiredCapitalQsubstitutions & desiredCapitalSubstitutions
        #
        # requiredCapitalQincrement & requiredCapitalIncrement
        #
        #
        # giving:
        #
        # self.capitalQ increment (with +=) from desiredCapitalQsubstitutions + requiredCapitalQincrement
        #
        # self.capital increment (with +=) from desiredCapitalSubstitutions + requiredCapitalIncrement
        #
        # self.grossInvestmentQ = desiredCapitalQsubstitutions+requiredCapitalQincrement, for reporting reasons
        #
        #
        # with return:
        #
        # self.capital
        # self.grossInvestmentQ
        # =========================================================================================

    def allowInformationToCentralPlanner(self) -> tuple:
        return (self.desiredCapitalQsubstitutions, self.requiredCapitalQincrement, \
                self.desiredCapitalSubstitutions, self.requiredCapitalIncrement)

    def requestGoodsToTheCentralPlanner(self) -> tuple:
        return (self.desiredCapitalQsubstitutions, self.requiredCapitalQincrement, \
                self.desiredCapitalSubstitutions, self.requiredCapitalIncrement)

    def concludeProduction(self):

        # action of the planner
        # capitalQsubstitutions = self.investmentGoodsGivenByThePlanner[0]
        # capitalQincrement = self.investmentGoodsGivenByThePlanner[1]
        # capitalSubstitutions = self.investmentGoodsGivenByThePlanner[2]
        # capitalIncrement = self.investmentGoodsGivenByThePlanner[3]

        desiredCapitalQChange = (self.desiredCapitalQsubstitutions + self.requiredCapitalQincrement)
        desiredCapitalChange = self.desiredCapitalSubstitutions + self.requiredCapitalIncrement
        assert desiredCapitalQChange >= 0
        assert desiredCapitalChange >= 0

        realCapitalQChange = 0
        if self.receiveLoan > 0:
            # print(self.receiveLoan, desiredCapitalQChange*self.currentPriceOfDurableProductiveGoodsPerUnit, desiredCapitalChange)
            qRatio = desiredCapitalQChange / (desiredCapitalQChange*self.currentPriceOfDurableProductiveGoodsPerUnit + desiredCapitalChange)
            realCapitalQChange = self.receiveLoan * qRatio
            # effects
            self.localStocks.DEPOSIT_Q[0].quantity += realCapitalQChange/self.currentPriceOfDurableProductiveGoodsPerUnit
            self.localStocks.DEPOSIT[0].value -= realCapitalQChange

        self.grossInvestmentQ = realCapitalQChange


        # total cost of capital, common by aiden: i do not know what means for totalCostOfCapital, so i just ignore it
        # self.totalCostOfCapital = self.capitalBeforeAdjustment * self.params['costOfCapital'] / self.params['timeFraction'] \
        #                           + capitalQsubstitutions * self.currentPriceOfDurableProductiveGoodsPerUnit

        self.totalCostOfCapital = 0

        # remove concluded aPPs from the list (backward to avoid skipping when deleting)
        for i in range(len(self.appRepository) - 1, -1, -1):
            if self.appRepository[i].productionClock == self.appRepository[i].orderDuration:
                self.unavailableLabor -= self.appRepository[i].requiredLabor
                self.unavailableCapitalQ -= self.appRepository[i].requiredCapitalQ
                del self.appRepository[i]

        return (self.currentTotalOutput, self.currentTotalCostOfProductionOrder, self.currentTotalCostOfUnusedFactors,
                self.inventories, \
                self.inProgressInventories, self.currentTotalLostProduction, self.currentTotalCostOfLostProduction, \
                len(self.employees), self.localStocks.DEPOSIT[0].value, self.grossInvestmentQ)
        # labor, capital modified just above

    def receiveSellingOrders(self, shareOfInventoriesBeingSold: float, centralPlannerBuyingPriceCoefficient: float):
        nominalQuantitySold = shareOfInventoriesBeingSold * self.inventories
        self.revenues = centralPlannerBuyingPriceCoefficient * nominalQuantitySold
        self.inventories -= nominalQuantitySold

    def computeDebtPayments(self, currentTime):

        payments = np.zeros((len(self.localStocks.LOAN), 3))
        toPay = 0
        totInterests = 0

        for i, loan in enumerate(self.localStocks.LOAN):
            timeDiff = currentTime - loan.startTick
            if timeDiff % loan.ObservePeriod == 0 and timeDiff > 0:
                iRate = loan.interestRate
                iniValue = loan.iniValue
                length = loan.length

                interests = iRate * loan.value
                payments[i, 0] = interests
                principal = iniValue / length

                payments[i, 1] = principal
                payments[i, 2] = loan.value

                toPay += principal + interests
                totInterests += interests
            else:
                payments[i, 0] = 0
                payments[i, 1] = 0
                payments[i, 2] = loan.value

        self.debtPayments = payments
        self.debtBurden = toPay
        self.debtInterests = totInterests

    def payInterests(self, currentTime):
        self.computeDebtPayments(currentTime)

        deposit = self.localStocks.DEPOSIT[0]

        if deposit.value > self.debtBurden:
            for i, loan in enumerate(self.localStocks.LOAN):
                interestToPay, principalToPay = self.debtPayments[i, 0], self.debtPayments[i, 1]
                valueToPay = interestToPay + principalToPay
                if valueToPay > 0:
                    deposit.value -= valueToPay
                    loan.age -= 1
                    if deposit.liabilityHolder != loan.assetHolder:
                        loan.assetHolder.localStocks.RESERVE[0].value += valueToPay
                        deposit.liabilityHolder.localStocks.RESERVE[0].value -= valueToPay
                        loan.assetHolder.localFlows.INTEREST_LOAN += interestToPay
                        loan.liabilityHolder.localFlows.INTEREST_LOAN += interestToPay
                    loan.value -= self.debtPayments[i, 1]
        else:
            print(f'Firm:{self.uid}  Default due to debt service')

    def payWage(self):
        if len(self.employees) > 0:
            frimDeposit = self.localStocks.DEPOSIT[0]
            depositLiabilityHolder = frimDeposit.liabilityHolder
            totalWage = 0
            for employee in self.employees:
                totalWage += employee.wage

            if totalWage > frimDeposit.value:
                print(f'Firm:{self.uid}  Default wage due to debt service')
            else:
                for employee in self.employees:
                    wage = employee.wage
                    depositLiabilityHolder.transfer(frimDeposit, employee.localStocks.DEPOSIT[0], wage)

    def computeLaborDemand(self):
        currentWorkers = len(self.employees)

        expect_labor = max(0, self.laborExpect)

        if currentWorkers > expect_labor:
            self.laborDemand = 0
            fireWorker = int(currentWorkers - expect_labor)
            random.shuffle(self.employees)
            for i in range(len(self.employees) - 1, len(self.employees) - 1 - fireWorker, -1):
                employee = self.employees[i]
                employee.employer = None
                self.employees.pop(i)
        else:
            self.laborDemand = expect_labor - currentWorkers

        return self.laborDemand

    def computeDesiredOutput(self):
        shareOfInventoriesBeingSold = self.params['minOfInventoriesBeingSold'] \
                                      + self.model.rng.random() * self.params['rangeOfInventoriesBeingSold']
        inventories = self.localStocks.CONS_GOOD[0].quantity
        self.desiredOutput = shareOfInventoriesBeingSold * inventories
        return self.desiredOutput

    def getPriceLowerBound(self):
        if self.desiredOutput == 0:
            return 0
        return (self.currentTotalCostOfProductionOrder+self.currentTotalCostOfUnusedFactors)/self.desiredOutput

    def computePrice(self):
        curr_price = self.price
        if self.lag_sales != 0:
            referenceVariable = self.localStocks.CONS_GOOD[0].quantity/self.lag_sales
        else:
            referenceVariable = 1
        previousLowerBound = curr_price / (1+self.markUp)

        priceLowerBound = self.getPriceLowerBound()
        if referenceVariable > 0.1:
            self.markUp -= self.markUp+random.random()*1
        else:
            self.markUp += self.markUp+random.random()*1

        if priceLowerBound != 0:
            curr_price = priceLowerBound*(1+self.markUp)
        else:
            curr_price = previousLowerBound*(1+self.markUp)
            return curr_price

        if curr_price == np.inf or curr_price == np.nan:
            print("NaN Markup")

        if curr_price > priceLowerBound:
            return curr_price
        else:
            return priceLowerBound


    def makeBalancesheet(self, current_time):

        self.totalCosts = self.currentTotalCostOfProductionOrder + self.currentTotalCostOfUnusedFactors
        """
        if params['usingMarkup']:
            self.inventories *= (1+self.plannedMarkup) #planned because != ex post
            self.inProgressInventories *= (1+self.plannedMarkup) 
        """

        self.profits = self.revenues + (self.inventories + self.inProgressInventories) \
                       - self.totalCosts - self.initialInventories
        self.addedValue = self.profits + self.totalCosts

        self.myBalancesheet[current_time, 0] = self.sectorialClass  # i.e. row number in firms-features

        self.myBalancesheet[current_time, 1] = self.initialInventories
        self.myBalancesheet[current_time, 2] = self.totalCosts

        if not self.productionType in self.params["investmentGoods"]:
            self.myBalancesheet[current_time, 3] = self.revenues
        else:
            self.myBalancesheet[current_time, 4] = self.revenues

        if not self.productionType in self.params["investmentGoods"]:
            self.myBalancesheet[current_time, 5] = self.inventories
        else:
            self.myBalancesheet[current_time, 6] = self.inventories

        if not self.productionType in self.params["investmentGoods"]:
            self.myBalancesheet[current_time, 7] = self.inProgressInventories
        else:
            self.myBalancesheet[current_time, 8] = self.inProgressInventories

        self.myBalancesheet[current_time, 9] = self.profits
        self.myBalancesheet[current_time, 10] = self.addedValue
        self.myBalancesheet[current_time, 11] = self.currentTotalOutput
        self.myBalancesheet[current_time, 12] = self.currentTotalCostOfProductionOrder
        self.myBalancesheet[current_time, 13] = self.currentTotalCostOfUnusedFactors
        self.myBalancesheet[current_time, 14] = self.currentTotalLostProduction
        self.myBalancesheet[current_time, 15] = self.currentTotalCostOfLostProduction
        self.myBalancesheet[current_time, 16] = self.totalCostOfLabor
        self.myBalancesheet[current_time, 17] = self.totalCostOfCapital
        self.myBalancesheet[current_time, 18] = self.grossInvestmentQ
        self.myBalancesheet[current_time, 19] = self.productionType

        self.cleanLoan()

    def cleanLoan(self):
        # to_remove = []
        # for loan in self.Loans:
        #     if loan.value == 0 or loan.age <= 0:
        #         to_remove.append(loan)
        #
        # for loan in to_remove:
        #     loan.assetHolder.Loans.remove(loan)
        #     self.Loans.remove(loan)
        for i in range(len(self.localStocks.LOAN) - 1, -1, -1):
            if self.localStocks.LOAN[i].value == 0 or self.localStocks.LOAN[i].age <= 0:
                loan = self.localStocks.LOAN[i]
                loan.assetHolder.localStocks.LOAN.remove(loan)
                self.localStocks.LOAN.pop(i)



############################################################################################################################
###########################################################################################################################


class ProductiveProcess():
    def __init__(self, productiveProcessId: tuple, targetProductionOfThePeriod: float, requiredLabor: int, \
                 requiredCapitalQ: float, orderDuration: int, priceOfDurableProductiveGoodsPerUnit: float, \
                 assetsUsefulLife: float):
        self.targetProductionOfThePeriod = targetProductionOfThePeriod
        self.requiredLabor = requiredLabor
        self.requiredCapitalQ = requiredCapitalQ
        self.orderDuration = orderDuration
        self.productionClock = 0
        self.hasResources = False
        self.productiveProcessId = productiveProcessId
        self.priceOfDurableProductiveGoodsPerUnit = priceOfDurableProductiveGoodsPerUnit
        self.assetsUsefulLife = assetsUsefulLife

    # def step(self, productionOrder)->tuple:
    def step(self, rng, params) -> tuple:
        lostProduction = 0
        costOfLostProduction = 0
        self.productionClock += 1
        self.failure = False

        # production failure
        if params['probabilityToFailProductionChoices'] >= rng.random():
            self.failure = True
            # if self.productiveProcessId[0]==29 and self.productiveProcessId[2]==2:
            #    print("***2",t(),"failure")
            # print("failure",flush=True)
            lostProduction = self.targetProductionOfThePeriod * self.productionClock
            self.targetProductionOfThePeriod = 0
            costOfLostProduction = (params['wage'] * self.requiredLabor + \
                                    (params['costOfCapital'] / params['timeFraction']) * self.requiredCapitalQ * \
                                    self.priceOfDurableProductiveGoodsPerUnit) * self.productionClock + \
                                   (self.requiredCapitalQ * self.priceOfDurableProductiveGoodsPerUnit) / \
                                   (self.assetsUsefulLife * params['timeFraction'])
            self.orderDuration = self.productionClock

        return (self.targetProductionOfThePeriod, self.requiredLabor, self.requiredCapitalQ, \
                lostProduction, costOfLostProduction)