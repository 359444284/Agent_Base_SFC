from model1_general.agents.BasicAgent import BasicAgent
from model1_general.agents.stockItems.Deposit import Deposit
from model1_general.agents.stockItems.Reserve import Reserve
import numpy as np
from typing import Tuple, List, Dict
class CommercialBank(BasicAgent):
    # stock

    STOCK_TYPES = ['DEPOSIT', 'RESERVE', 'ADVANCE', 'LOAN']

    FLOW_TYPES = ['INTEREST_DEPOSIT', 'INTEREST_LOAN']


    
    def __init__(self, uid: Tuple, model, isGlobal: bool, paramGroup: int,
        depositInterestRate: float, loanInterestRate: float, targetedLiquidityRatio: float, capitalAdequacyRatio:float):
        super().__init__(uid=uid, isGlobal=isGlobal, paramGroup=paramGroup)

        # params (need to modify save and update function)
        self.params = model.params

        self.depositInterestRate = depositInterestRate
        self.loanInterestRate = loanInterestRate
        self.targetedLiquidityRatio = targetedLiquidityRatio
        self.capitalAdequacyRatio = capitalAdequacyRatio

        self.advancesDemand = 0
        self.loanSupply = 0

        # -------------------------
        self.myBalancesheet = np.zeros((self.params['howManyCycles'], 7))

    def transfer(self, sourceDeposit: Deposit, targetDeposit: Deposit, value: float):

        sourceBank = sourceDeposit.liabilityHolder
        targetBank = targetDeposit.liabilityHolder

        sourceBankReserve = sourceBank.localStocks.RESERVE[0]
        targetBankReserve = targetBank.localStocks.RESERVE[0]

        sourceDeposit.value -= value
        targetDeposit.value += value

        if sourceBank != targetBank:
            sourceBankReserve.value -= value
            targetBankReserve.value += value


    def payDepositInterests(self):
        for deposit in self.localStocks.DEPOSIT:
            depositor = deposit.assetHolder
            payInterests = self.depositInterestRate * deposit.value
            self.localFlows.INTEREST_DEPOSIT += payInterests
            # depositor.localFlows[depositor.INTEREST_DEPOSIT] += payInterests
            deposit.value += payInterests

    def getNetWealth(self):
        return self.globalStocks.LOAN + self.globalStocks.RESERVE - self.globalStocks.ADVANCE - self.globalStocks.DEPOSIT

    def getCreditSupply(self):
        capitalsValue = self.getNetWealth()

        # capitalsValue = self.globalStocks[self.DEPOSIT]

        desiredLoansStock = max(capitalsValue*0.6, 0)

        currentLoans = self.globalStocks.LOAN

        newLoansSupply = max(desiredLoansStock - currentLoans, 0)

        # newLoansSupply = 60

        self.loanSupply = newLoansSupply

        return newLoansSupply


    def getAdvanceDemand(self):
        
        totalDeposits = self.globalStocks.DEPOSIT
        totalReserves = self.globalStocks.RESERVE

        self.advancesDemand = max(totalDeposits * self.targetedLiquidityRatio - totalReserves, 0)

        return self.advancesDemand

    def payInterests(self, currentTime):
        reserve = self.localStocks.RESERVE[0]
       
        for advance in self.localStocks.ADVANCE:
            timeDiff = currentTime - advance.startTick
            if timeDiff % advance.ObservePeriod == 0 and timeDiff > 0:
                
                interest = advance.interestRate * advance.value
                principal = advance.iniValue/advance.length

                self.localFlows.INTEREST_LOAN += interest

                
                reserve.value -= interest + principal
                advance.value -= principal
                advance.age -= 1
        

    def makeBalancesheet(self, currentTime):



        netWealth = self.getNetWealth()
        self.myBalancesheet[currentTime, 0] = self.globalStocks.DEPOSIT
        self.myBalancesheet[currentTime, 1] = self.globalStocks.RESERVE
        self.myBalancesheet[currentTime, 2] = self.globalStocks.ADVANCE
        self.myBalancesheet[currentTime, 3] = self.globalStocks.LOAN

        self.myBalancesheet[currentTime, 4] = self.globalFlows.INTEREST_DEPOSIT
        self.myBalancesheet[currentTime, 5] = self.globalFlows.INTEREST_LOAN


        self.myBalancesheet[currentTime, 6] = netWealth

        # print(self.myBalancesheet[currentTime, :])

        # print(self._globalStocks)


        self.cleanAdvance()

    def cleanAdvance(self):
        # to_remove = []
        # for advance in self.Advances:
        #     if advance.value == 0 or advance.age <= 0:
        #         to_remove.append(advance)
        #
        # for advance in to_remove:
        #     advance.liabilityHolder.Advances.remove(advance)
        #     self.Advances.remove(advance)

        for i in range(len(self.localStocks.ADVANCE) - 1, -1, -1):
            if self.localStocks.ADVANCE[i].value == 0 or self.localStocks.ADVANCE[i].age <= 0:
                advance = self.localStocks.ADVANCE[i]
                advance.assetHolder.localStocks.ADVANCE.remove(advance)
                self.localStocks.ADVANCE.pop(i)

            

    def save(self):
        basic_info = super().save()

        params = (
            self.depositInterestRate,
            self.loanInterestRate,
            self.loanSupply
        )

        return (*basic_info, params)


    def update(self, basic_info, params=None):
        # fill this part
        super().update(basic_info)
        if params is not None:
            (
            self.depositInterestRate,
            self.loanInterestRate,
            self.loanSupply) = params
            

    
