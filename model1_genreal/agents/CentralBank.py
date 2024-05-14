from agents.BasicAgent import BasicAgent
from agents.stockItems import Deposit, Reserve

import numpy as np
from typing import Tuple, List, Dict

class CentralBank(BasicAgent):
        # stock
    STOCK_AMOUNT = 2
    DEPOSIT = 0
    RESERVE = 1

    # flow
    FLOW_AMOUNT = 2
    DEPOSIT_DELTA = 0
    RESERVE_DELTA = 1
    
    def __init__(self, uid: Tuple):
        super().__init__(uid)


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

        self.reporterGhostList = []

    

    