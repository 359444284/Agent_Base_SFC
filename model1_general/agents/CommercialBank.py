from model1_general.agents.BasicAgent import BasicAgent
from model1_general.agents.stockItems.Deposit import Deposit
from model1_general.agents.stockItems.Reserve import Reserve
import numpy as np
from typing import Tuple, List, Dict
class CommercialBank(BasicAgent):
    # stock

    STOCK_TYPES = ['DEPOSIT', 'RESERVE', 'ADVANCE', 'LOAN']

    FLOW_TYPES = ['INTEREST_DEPOSIT', 'INTEREST_LOAN']


    
    def __init__(self, uid: Tuple, params:dict, isGlobal: bool, paramGroup: int,
        depositInterestRate: float, loanInterestRate: float, targetedLiquidityRatio: float, capitalAdequacyRatio:float):
        super().__init__(uid=uid, isGlobal=isGlobal, paramGroup=paramGroup)

        # params (need to modify save and update function)

        self.depositInterestRate = depositInterestRate
        self.loanInterestRate = loanInterestRate
        self.targetedLiquidityRatio = targetedLiquidityRatio
        self.capitalAdequacyRatio = capitalAdequacyRatio

        self.advancesDemand = 0
        self.loanSupply = 0

        # -------------------------
        self.myBalancesheet = np.zeros((params['howManyCycles'], 7))

    def transfer(self, sourceDeposit: Deposit, targetDeposit: Deposit, value: float):

        sourceBank = sourceDeposit.liabilityHolder
        targetBank = targetDeposit.liabilityHolder

        sourceBankReserve = sourceBank.localStocksNamed.RESERVE[0]
        targetBankReserve = targetBank.localStocksNamed.RESERVE[0]

        sourceDeposit.value -= value
        targetDeposit.value += value

        if sourceBank != targetBank:
            sourceBankReserve.value -= value
            targetBankReserve.value += value

    def payDepositInterests(self):
        for deposit in self.localStocksNamed.DEPOSIT:
            depositor = deposit.assetHolder
            payInterests = self.depositInterestRate * deposit.value
            self.localFlowsNamed.INTEREST_DEPOSIT += payInterests
            # depositor.localFlows[depositor.INTEREST_DEPOSIT] += payInterests
            deposit.value += payInterests

    def getNetWealth(self):
        return self.globalStocksNamed.LOAN + self.globalStocksNamed.RESERVE - self.globalStocksNamed.ADVANCE - self.globalStocksNamed.DEPOSIT

    def getCreditSupply(self):
        capitalsValue = self.getNetWealth()

        # capitalsValue = self.globalStocks[self.DEPOSIT]

        desiredLoansStock = max(capitalsValue*0.6, 0)

        currentLoans = self.globalStocksNamed.LOAN

        newLoansSupply = max(desiredLoansStock - currentLoans, 0)

        # newLoansSupply = 60

        self.loanSupply = newLoansSupply

        return newLoansSupply


    def getAdvanceDemand(self):
        
        totalDeposits = self.globalStocksNamed.DEPOSIT
        totalReserves = self.globalStocksNamed.RESERVE

        self.advancesDemand = max(totalDeposits * self.targetedLiquidityRatio - totalReserves, 0)

        return self.advancesDemand

    def payInterests(self, currentTime):
        reserve = self.localStocksNamed.RESERVE[0]
       
        for advance in self.localStocksNamed.ADVANCE:
            timeDiff = currentTime - advance.startTick
            if timeDiff % advance.ObservePeriod == 0 and timeDiff > 0:
                
                interest = advance.interestRate * advance.value
                principal = advance.iniValue/advance.length

                self.localFlowsNamed.INTEREST_LOAN += interest

                
                reserve.value -= interest + principal
                advance.value -= principal
                advance.age -= 1
        

    def makeBalancesheet(self, currentTime):

        netWealth = self.getNetWealth()
        self.myBalancesheet[currentTime, 0] = self.globalStocksNamed.DEPOSIT
        self.myBalancesheet[currentTime, 1] = self.globalStocksNamed.RESERVE
        self.myBalancesheet[currentTime, 2] = self.globalStocksNamed.ADVANCE
        self.myBalancesheet[currentTime, 3] = self.globalStocksNamed.LOAN

        self.myBalancesheet[currentTime, 4] = self.globalFlowsNamed.INTEREST_DEPOSIT
        self.myBalancesheet[currentTime, 5] = self.globalFlowsNamed.INTEREST_LOAN


        self.myBalancesheet[currentTime, 6] = netWealth

        self.globalFlows.fill(0)
        self.localFlows.fill(0)


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

        for i in range(len(self.localStocksNamed.ADVANCE) - 1, -1, -1):
            if self.localStocksNamed.ADVANCE[i].value == 0 or self.localStocksNamed.ADVANCE[i].age <= 0:
                advance = self.localStocksNamed.ADVANCE[i]
                advance.assetHolder.localStocksNamed.ADVANCE.remove(advance)
                self.localStocksNamed.ADVANCE.pop(i)

            

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
            

    
