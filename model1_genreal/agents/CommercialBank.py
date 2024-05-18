from agents.BasicAgent import BasicAgent
from agents.stockItems import Deposit, Reserve
import numpy as np
from typing import Tuple, List, Dict

class CommercialBank(BasicAgent):
    # stock
    STOCK_AMOUNT = 2
    DEPOSIT = 0
    RESERVE = 1

    # flow
    FLOW_AMOUNT = 3
    DEPOSIT_DELTA = 0
    RESERVE_DELTA = 1
    INTEREST_DEPOSIT = 2

    
    def __init__(self, uid: Tuple, params:dict, isGlobal: bool, paramGroup: int,
        depositInterestRate: float, loanInterestRate: float):
        super().__init__(uid=uid, isGlobal=isGlobal, paramGroup=paramGroup)

        # params (need to modify save and update function)

        self.depositInterestRate = depositInterestRate
        self.loanInterestRate = loanInterestRate

    
        # global stock attributes
        self.globalStocks = np.zeros(self.STOCK_AMOUNT)

        # global flow attributes
        self.globalFlows = np.zeros(self.FLOW_AMOUNT)

        # local stock attributes
        self.localStocks = []

        self.Deposits = []
        self.Reserves = []

        self.localStocks.append(self.Deposits)
        self.localStocks.append(self.Reserves)
        # self.Loans = []
        # self.Advances = []

        # local flow attributes -- should be reset to 0 after the balance sheet
        self.localFlows = np.zeros(self.FLOW_AMOUNT)

        # -------------------------

        self.myBalancesheet = np.zeros((params['howManyCycles'], 4))
    

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
 
    def makeBalancesheet(self, currentTime):

        self.myBalancesheet[currentTime, 0] = self.globalStocks[self.DEPOSIT]
        self.myBalancesheet[currentTime, 1] = self.globalStocks[self.RESERVE]
        self.myBalancesheet[currentTime, 2] = self.globalFlows[self.DEPOSIT_DELTA]
        self.myBalancesheet[currentTime, 3] = self.globalFlows[self.RESERVE_DELTA]

        self.globalFlows.fill(0)
        self.localFlows.fill(0)

    def save(self):
        basic_info = super().save()

        params = (
            self.depositInterestRate,
            self.loanInterestRate
        )

        return (*basic_info, params)


    def update(self, basic_info, params=None):
        # fill this part
        super().update(basic_info)
        if params is not None:
            (
            self.depositInterestRate,
            self.loanInterestRate) = params
            

    
