import abc
from repast4py import core
import numpy as np
from typing import Tuple, List, Dict, Optional

# enable us get stock or flow items by string
class NamedAccessor:
    def __init__(self, array, names):
        self._array = array
        for i, name in enumerate(names):
            setattr(self, name, self._array[i])

    def __getitem__(self, key):
        if isinstance(key, str):
            return getattr(self, key)
        return self._array[key]

    def __setitem__(self, key, value):
        if isinstance(key, str):
            setattr(self, key, value)
        self._array[key] = value

class BasicAgent(core.Agent, abc.ABC):

    def __init__(self, uid: Tuple, isGlobal:bool, paramGroup):
        super().__init__(id=uid[0], type=uid[1], rank=uid[2])

        self.isGlobal: bool = isGlobal
        self.paramGroup: int = paramGroup

        self.globalStocks: Optional[np.ndarray] = None
        self.globalFlows: Optional[np.ndarray] = None
        self.localFlows: Optional[np.ndarray] = None
        self.localStocks: Optional[List[List]] = None

        self.globalStocksNamed: Optional[NamedAccessor] = None
        self.globalFlowsNamed: Optional[NamedAccessor] = None
        self.localFlowsNamed: Optional[NamedAccessor] = None
        self.localStocksNamed: Optional[NamedAccessor] = None


        if not hasattr(self, 'STOCK_TYPES'):
            self.STOCK_TYPES = []

        self.globalStocks = np.zeros(len(self.STOCK_TYPES))
        self.globalStocksNamed = NamedAccessor(self.globalStocks, self.STOCK_TYPES)
        self.localStocks = [[] for _ in range(len(self.STOCK_TYPES))]
        self.localStocksNamed = NamedAccessor(self.localStocks, self.STOCK_TYPES)

        if not hasattr(self, 'FLOW_TYPES'):
            self.FLOW_TYPES = []

        self.globalFlows = np.zeros(len(self.FLOW_TYPES))
        self.globalFlowsNamed = NamedAccessor(self.globalFlows, self.FLOW_TYPES)
        self.localFlows = np.zeros(len(self.FLOW_TYPES))
        self.localFlowsNamed = NamedAccessor(self.localFlows, self.FLOW_TYPES)


        self.reporterGhostList = []
        self.counterPart = None


    
    # only call by reporter
    def getInformationTableData(self):

        aggregate_data = (
            self.localFlows.copy(),
            self.aggrigateStocks(self.localStocks),
            )

        # -- reset the delta to 0
        self.localFlows.fill(0)
        return aggregate_data


    def aggrigateStocks(self, stocks):
        counter = np.zeros(len(stocks))

        for i, stockType in enumerate(stocks):
            for stock in stockType:
                counter[i] += stock.value
        
        return counter
    

    def mergeInformationTableData(self):

        self.globalStocks = self.aggrigateStocks(self.localStocks)

        for theReporterGhost in self.reporterGhostList:
            self.globalFlows += theReporterGhost.flowInfo
            self.globalStocks += theReporterGhost.stockInfo

        self.globalFlows += self.localFlows

        # -- reset the delta to 0
        self.localFlows.fill(0)


    def save(self):
        return (self.uid, 
               (self.isGlobal, self.paramGroup, self.globalStocks, self.globalFlows)
               )

    def update(self, basic_info):
        self.isGlobal, self.paramGroup, self.globalStocks, self.globalFlows = basic_info
    