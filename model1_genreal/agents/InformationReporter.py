from repast4py import core
import numpy as np
from typing import Tuple, List, Dict

class InformationReporter(core.Agent):
    
    def __init__(self, local_id: int, type_id:int, rank_id: int):
        super().__init__(id=local_id, type=type_id, rank=rank_id)


        self.flowInfo = []  # superflous
        self.stockInfo = []
        self.connectAgent = None


    def reciveInformationLastCol(self):
        
        self.flowInfo, self.stockInfo = self.connectAgent.getInformationTableData()
    
    def save(self) -> Tuple: # mandatory, used by request_agents and by synchronizazion
        """
        Saves the state of the CentralPlannerReporter as a Tuple.

        Returns:
            The saved state of this CentralPlannerReporter.
        """
        # ??the structure of the save is ( ,( )) due to an incosistent use of the 
        # save output in update internal structure /fixed in v. 1.1.2???)
        #return (self.uid,(self.informationTable,)) #the comma is relevant for positional reasons
        #print(rank, "save",self.informationTableLastCol,flush=True)
        return (self.uid,(self.flowInfo, self.stockInfo))

    def update(self, dynState: Tuple): # mandatory, used by synchronize
        #print(rank, "updt",dynState,flush=True)
        #print("from reporter upddat, rank=",rank,"t=",t(),dynState,flush=True)
        self.flowInfo = dynState[0]  # superflous
        self.stockInfo = dynState[1]