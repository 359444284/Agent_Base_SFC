import random

import numpy as np
from typing import Tuple, List, Dict
from repast4py import core

class CreditMarket(core.Agent):

    def __init__(self, uid: Tuple, params: Dict, isGlobal: bool, paramGroup: int):
        super().__init__(id=uid[0], type=uid[1], rank=uid[2])

        self.isGlobal = isGlobal
        self.paramGroup = paramGroup

        self.params = params
        self.matchStrategy = 0



        # {agentUid: [totalLoanDemand]}
        self.globalDemandersInfo = {}
        # {agentUid: [totalLoanSupply]}
        self.globalSuppliersInfo = {}

        self.localDemandersInfo = {}
        self.localSuppliersInfo = {}

        # Demander vs Supplier : one to many
        #
        self.globalCreditDemanders = []
        self.globalCreditSuppliers = []

        # list of uid
        self.creditDemanders = []
        # list of uid
        self.creditSuppliers = []

        # {demainderUid, [supplyerUid, amount]}
        self.matched_info = {}

        self.reporterGhostList = []

    def collectSupplyer(self, supplierList):
        self.creditSuppliers = supplierList

    def collectDemander(self, demandList):
        self.creditDemanders = demandList

    def collectSupplyInfo(self, uid, info):
        self.localSuppliersInfo[uid] = info

    def collectDemandInfo(self, uid, info):
        self.localDemandersInfo[uid] = info

    def getInformationTableData(self):

        aggrate_data = (
            self.localDemandersInfo.copy(),
            self.localSuppliersInfo.copy(),
            self.creditDemanders.copy(),
            self.creditSuppliers.copy(),
            )

        # -- reset the delta to 0
        self.localSuppliersInfo = {}
        self.localDemandersInfo = {}
        self.creditDemanders = []
        self.creditSuppliers = []

        return aggrate_data

    def mergeInformationTableData(self):
        self.globalDemandersInfo = {}
        self.globalSuppliersInfo = {}
        self.globalCreditDemanders = []
        self.globalCreditSuppliers = []

        self.globalSuppliersInfo |= self.localSuppliersInfo
        self.globalDemandersInfo |= self.localDemandersInfo

        self.globalCreditDemanders.append(self.creditDemanders)
        self.globalCreditSuppliers.append(self.creditSuppliers)

        for theReporterGhost in self.reporterGhostList:
            self.globalDemandersInfo |= theReporterGhost.demandersInfo
            self.globalSuppliersInfo |= theReporterGhost.suppliersInfo
            self.globalCreditDemanders.append(theReporterGhost.creditDemanders)
            self.globalCreditSuppliers.append(theReporterGhost.creditSuppliers)

        self.localSuppliersInfo = {}
        self.localDemandersInfo = {}
        self.creditDemanders = []
        self.creditSuppliers = []

    def excute(self):
        self.matched_info = {}

        for list in self.globalCreditDemanders:
            random.shuffle(list)
        for list in self.globalCreditSuppliers:
            random.shuffle(list)

        remind_demander = [len(self.globalCreditDemanders[i]) for i in range(len(self.globalCreditDemanders))]


        while sum(remind_demander) > 0:

            for rank_id in range(len(remind_demander)):
                if remind_demander[rank_id] <= 0:
                    continue

                demanderUid = self.globalCreditDemanders[rank_id][remind_demander[rank_id] - 1]
                demanderInfo = self.globalDemandersInfo[demanderUid]

                supplierUid = random.choice(self.globalCreditSuppliers[rank_id])
                while self.globalSuppliersInfo[supplierUid][0] == 0:
                    self.globalCreditSuppliers[rank_id].remove(supplierUid)
                    if len(self.globalCreditSuppliers[rank_id]) == 0:
                        remind_demander[rank_id] = 0
                        break
                    supplierUid = random.choice(self.globalCreditSuppliers[rank_id])


                supplierInfo = self.globalSuppliersInfo[supplierUid]

                require = demanderInfo[0]

                if require <= 0:
                    remind_demander[rank_id] -= 1
                    continue

                offered = supplierInfo[0]
                amount = max(0, min(offered, require))
                if amount > 0:
                    self.globalDemandersInfo[demanderUid][0] -= amount
                    self.globalSuppliersInfo[supplierUid][0] -= amount

                    self.matched_info[demanderUid] = (supplierUid, amount)

                    # if self.globalDemandersInfo[demanderUid][0] == 0:
                    remind_demander[rank_id] -= 1

                    if self.globalSuppliersInfo[supplierUid][0] == 0:
                        self.globalCreditSuppliers[rank_id].remove(supplierUid)
                        if len(self.globalCreditSuppliers[rank_id]) == 0:
                            remind_demander[rank_id] = 0

        # print(self.matched_info)



    def save(self):
        return (self.uid, (self.matched_info, None, self.isGlobal, self.paramGroup))

    def update(self, basic_info):
        self.matched_info, _, self.isGlobal, self.paramGroup = basic_info






