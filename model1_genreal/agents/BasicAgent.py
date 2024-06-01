import abc
from repast4py import core
import numpy as np
from typing import Tuple, List, Dict


class BasicAgent(core.Agent, abc.ABC):
    def __init__(self, uid: Tuple, isGlobal:bool, paramGroup):
        super().__init__(id=uid[0], type=uid[1], rank=uid[2])

        self.isGlobal = paramGroup
        self.paramGroup = paramGroup

        self.globalStocks = None
        self.globalFlows = None
        self.localStocks = None
        self.localFlows = None

        self.reporterGhostList = []
        self.counterPart = None
    
    # only call by reporter
    def getInformationTableData(self):

        aggrate_data = (
            self.localFlows.copy(),
            self.aggrigateStocks(self.localStocks),
            )

        # -- reset the delta to 0
        self.localFlows.fill(0)

        return aggrate_data


    def aggrigateStocks(self, stocks):
        counter = np.zeros(len(stocks))

        for i, stockType in enumerate(stocks):
            for stock in stockType:
                counter[i] += stock.amount
        
        return counter
    

    def mergeInformationTableData(self):
        # if rank == self.uid[2]:

        self.globalStocks = self.aggrigateStocks(self.localStocks)

        for theReporterGhost in self.reporterGhostList:
            self.globalFlows += theReporterGhost.flowInfo
            self.globalStocks += theReporterGhost.stockInfo

        self.globalFlows += self.localFlows

        # -- reset the delta to 0
        self.localFlows.fill(0)


    def save(self):
        return (self.uid, 
               (self.globalStocks, self.globalFlows, self.isGlobal, self.paramGroup)
               )

    def update(self, basic_info):
        self.globalStocks, self.globalFlows, self.isGlobal, self.paramGroup = basic_info
    