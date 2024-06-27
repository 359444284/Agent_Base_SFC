import abc
from collections import deque

from repast4py import core
import numpy as np
from typing import Tuple, List, Dict, Optional

# enable us get stock or flow items by string
class NamedAccessor:
    __slots__ = ('_agent', '_attribute_name', '_name_to_index')

    def __init__(self, agent, attribute_name, names):
        self._agent = agent
        self._attribute_name = attribute_name
        self._name_to_index = {name: i for i, name in enumerate(names)}

    def __getattr__(self, name):
        try:
            return self._agent.__dict__[self._attribute_name][self._name_to_index[name]]
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        if name in ('_agent', '_attribute_name', '_name_to_index'):
            object.__setattr__(self, name, value)
        else:
            try:
                self._agent.__dict__[self._attribute_name][self._name_to_index[name]] = value
            except KeyError:
                raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __getitem__(self, key):
        if isinstance(key, str):
            return self._agent.__dict__[self._attribute_name][self._name_to_index[key]]
        return self._agent.__dict__[self._attribute_name][key]

    def __setitem__(self, key, value):
        if isinstance(key, str):
            self._agent.__dict__[self._attribute_name][self._name_to_index[key]] = value
        else:
            self._agent.__dict__[self._attribute_name][key] = value

class BasicAgent(core.Agent, abc.ABC):

    def __init__(self, uid: Tuple, isGlobal:bool, paramGroup):
        super().__init__(id=uid[0], type=uid[1], rank=uid[2])

        self.isGlobal: bool = isGlobal
        self.paramGroup: int = paramGroup

        self.globalStocksNamed: Optional[NamedAccessor] = None
        self.globalFlowsNamed: Optional[NamedAccessor] = None
        self.localFlowsNamed: Optional[NamedAccessor] = None
        self.localStocksNamed: Optional[NamedAccessor] = None
        self.expectationsNamed: Optional[NamedAccessor] = None

        self.globalStocks: Optional[np.ndarray] = None
        self.globalFlows: Optional[np.ndarray] = None
        self.localFlows: Optional[np.ndarray] = None
        self.localStocks: Optional[List[List]] = None
        self.expectations: Optional[List[deque]] = None

        self.STOCK_TYPES = getattr(self, 'STOCK_TYPES', [])
        self.FLOW_TYPES = getattr(self, 'FLOW_TYPES', [])
        self.EXP_TYPES = getattr(self, 'EXP_TYPES', [])

        self.globalStocks = np.zeros(len(self.STOCK_TYPES))
        self.globalStocksNamed = NamedAccessor(self, 'globalStocks', self.STOCK_TYPES)
        self.localStocks = [[] for _ in range(len(self.STOCK_TYPES))]
        self.localStocksNamed = NamedAccessor(self, 'localStocks', self.STOCK_TYPES)


        self.globalFlows = np.zeros(len(self.FLOW_TYPES))
        self.globalFlowsNamed = NamedAccessor(self, 'globalFlows', self.FLOW_TYPES)
        self.localFlows = np.zeros(len(self.FLOW_TYPES))
        self.localFlowsNamed = NamedAccessor(self, 'localFlows', self.FLOW_TYPES)


        self.expectations = [None for _ in range(len(self.EXP_TYPES))]
        self.expectationsNamed = NamedAccessor(self, 'expectations', self.EXP_TYPES)


        self.reporterGhostList = []
        self.counterPart = None


    
    # only call by reporter
    def getInformationTableData(self):

        aggregate_data = (
            self.localFlows.copy(),
            self.aggrigateStocks(self.localStocks),
            )

        # -- reset the delta to 0
        return aggregate_data


    def aggrigateStocks(self, stocks):
        counter = np.zeros(len(stocks))

        for i, stockType in enumerate(stocks):
            for stock in stockType:
                counter[i] += stock.value

        return counter
    

    def mergeInformationTableData(self):

        self.globalStocks[:] = self.aggrigateStocks(self.localStocks)

        # print(self.globalStocks)
        self.globalFlows.fill(0)
        self.globalFlows += self.localFlows

        for theReporterGhost in self.reporterGhostList:
            self.globalFlows += theReporterGhost.flowInfo
            self.globalStocks += theReporterGhost.stockInfo


    def resetFlows(self):
        self.globalFlows.fill(0)
        self.localFlows.fill(0)




    def save(self):
        return (self.uid, 
               (self.isGlobal, self.paramGroup, self.globalStocks, self.globalFlows)
               )

    def update(self, basic_info):
        self.isGlobal, self.paramGroup, self.globalStocks[:], self.globalFlows[:] = basic_info

#
