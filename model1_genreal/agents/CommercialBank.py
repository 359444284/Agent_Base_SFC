from agents.BasicAgent import BasicAgent
from agents.stockItems import Deposit, Reserve
import numpy as np
from typing import Tuple, List, Dict

class CommercialBank(BasicAgent):
    # stock 
    STOCK_AMOUNT = 4
    DEPOSIT = 0
    RESERVE = 1
    ADVANCE = 2
    LOAN = 3

    # flow
    FLOW_AMOUNT = 4
    DEPOSIT_DELTA = 0
    RESERVE_DELTA = 1
    INTEREST_DEPOSIT = 2
    INTEREST_LOAN = 3

    
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
    
        # global stock attributes
        self.globalStocks = np.zeros(self.STOCK_AMOUNT)

        # global flow attributes
        self.globalFlows = np.zeros(self.FLOW_AMOUNT)

        # local stock attributes
        self.localStocks = []

        self.Deposits = []
        self.Reserves = []
        self.Advances = []
        self.Loans = []

        self.localStocks.append(self.Deposits)
        self.localStocks.append(self.Reserves)
        self.localStocks.append(self.Advances)
        self.localStocks.append(self.Loans)


        # local flow attributes -- should be reset to 0 after the balance sheet
        self.localFlows = np.zeros(self.FLOW_AMOUNT)

        # -------------------------

        self.myBalancesheet = np.zeros((params['howManyCycles'], 8))
    

    def transfer(self, sourceDeposit, targetDeposit, amount):
        sourceBank = sourceDeposit.liabilityHolder
        targetBank = targetDeposit.liabilityHolder

        sourceBankReserve = sourceBank.Reserves[0]
        targetBankReserve = targetBank.Reserves[0]

        sourceDeposit.amount -= amount
        sourceBankReserve.amount -= amount
        sourceBank.localFlows[self.DEPOSIT_DELTA] -= amount
        sourceBank.localFlows[self.RESERVE_DELTA] -= amount

        targetDeposit.amount += amount
        targetBankReserve.amount += amount
        targetBank.localFlows[self.DEPOSIT_DELTA] += amount
        targetBank.localFlows[self.RESERVE_DELTA] += amount

    def payDepositInterests(self):
        for deposit in self.Deposits:
            depositor = deposit.assetHolder
            payInterests = self.depositInterestRate * deposit.amount
            self.localFlows[self.INTEREST_DEPOSIT] += payInterests
            # depositor.localFlows[depositor.INTEREST_DEPOSIT] += payInterests
            deposit.amount += payInterests

    def getNetWealth(self):
        return self.globalStocks[self.LOAN] + self.globalStocks[self.RESERVE] - self.globalStocks[self.ADVANCE] - self.globalStocks[self.DEPOSIT]

    def getCreditSupply(self):
        # capitalsValue = self.getNetWealth()

        capitalsValue = self.globalStocks[self.DEPOSIT]

        desiredLoansStock = max(capitalsValue*0.6, 0)

        currentLoans = self.globalStocks[self.LOAN]

        newLoansSupply = desiredLoansStock - currentLoans

        self.loanSupply = newLoansSupply

        return newLoansSupply


    def getAdvanceDemand(self):
        
        totalDeposits = self.globalStocks[self.DEPOSIT]
        totalReserves = self.globalStocks[self.RESERVE]

        self.advancesDemand = max(totalDeposits * self.targetedLiquidityRatio - totalReserves, 0)

        return self.advancesDemand

    def payInterests(self, currentTime):
        reserve = self.Reserves[0]
       
        for advance in self.Advances:
            timeDiff = currentTime - advance.startTick
            if timeDiff % advance.ObservePeriod == 0 and timeDiff > 0:
                
                interest = advance.interestRate * advance.amount
                principal = advance.iniAmount/advance.length

                self.localFlows[self.INTEREST_LOAN] += interest

                
                reserve.amount -= interest + principal
                advance.amount -= principal
                advance.age -= 1
        

    def makeBalancesheet(self, currentTime):

        self.myBalancesheet[currentTime, 0] = self.globalStocks[self.DEPOSIT]
        self.myBalancesheet[currentTime, 1] = self.globalStocks[self.RESERVE]
        self.myBalancesheet[currentTime, 2] = self.globalStocks[self.ADVANCE]
        self.myBalancesheet[currentTime, 3] = self.globalStocks[self.LOAN]

        self.myBalancesheet[currentTime, 4] = self.globalFlows[self.DEPOSIT_DELTA]
        self.myBalancesheet[currentTime, 5] = self.globalFlows[self.RESERVE_DELTA]
        self.myBalancesheet[currentTime, 6] = self.globalFlows[self.INTEREST_DEPOSIT]
        self.myBalancesheet[currentTime, 7] = self.globalFlows[self.INTEREST_LOAN]

        self.globalFlows.fill(0)
        self.localFlows.fill(0)


        self.cleanAdvance()

    def cleanAdvance(self):
        for i in range(len(self.Advances) - 1, -1, -1):
            if self.Advances[i].amount == 0 or self.Advances[i].age <= 0:
                advance = self.Advances[i]
                advance.liabilityHolder.Advances.remove(advance)
                self.Advances.pop(i)

            

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
            

    
