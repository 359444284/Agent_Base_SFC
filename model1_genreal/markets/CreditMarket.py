import random
from collections import defaultdict

import numpy as np
from typing import Tuple, List, Dict
from repast4py import core

class CreditMarket(core.Agent):

    def __init__(self, uid: Tuple, params: Dict, isGlobal: bool, paramGroup: int,
                 nround:int):
        super().__init__(id=uid[0], type=uid[1], rank=uid[2])

        self.isGlobal = isGlobal
        self.paramGroup = paramGroup

        self.params = params

        self.nround = nround

        self.matchStrategy = 0
        self.active = True



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
        self.matched_info = defaultdict(list)

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
        self.matched_info.clear()
        alive_demander = set(self.globalDemandersInfo.keys())
        remind_supplier = [len(ls) for ls in self.globalCreditSuppliers]

        for _ in range(self.nround):

            self.shuffle_demanders(alive_demander)

            demander_idx = [len(ls) for ls in self.globalCreditDemanders]

            while any(d * s > 0 for d, s in zip(demander_idx, remind_supplier)):
                for rank_id in range(len(demander_idx)):
                    if demander_idx[rank_id] <= 0 or remind_supplier[rank_id] <= 0:
                        continue

                    demanderUid = self.globalCreditDemanders[rank_id][demander_idx[rank_id] - 1]
                    demanderInfo = self.globalDemandersInfo[demanderUid]

                    require = demanderInfo[0]
                    if require <= 0:
                        alive_demander.remove(demanderUid)
                        demander_idx[rank_id] -= 1
                        continue

                    supplierUid = self.match_suppliers(rank_id, remind_supplier)
                    if supplierUid is None:
                        break
                    supplierInfo = self.globalSuppliersInfo[supplierUid]

                    offered = supplierInfo[0]
                    amount = max(0, min(offered, require))

                    if amount > 0:
                        demanderInfo[0] -= amount
                        supplierInfo[0] -= amount

                        self.matched_info[demanderUid].append((supplierUid, amount))

                        if demanderInfo[0] == 0:
                            alive_demander.remove(demanderUid)

                        if supplierInfo[0] == 0:
                            self.globalCreditSuppliers[rank_id].remove(supplierUid)
                            remind_supplier[rank_id] -= 1
                            if remind_supplier[rank_id] <= 0:
                                demander_idx[rank_id] = 0

                    demander_idx[rank_id] -= 1

    # def process_demander
    def shuffle_demanders(self, alive_demanders):
        for i, demanders in enumerate(self.globalCreditDemanders):
            self.globalCreditDemanders[i] = [uid for uid in demanders if uid in alive_demanders]
            random.shuffle(self.globalCreditDemanders[i])
    def match_suppliers(self, rank_id, remind_suppliers):
        supplierUid = random.choice(self.globalCreditSuppliers[rank_id])
        while self.globalSuppliersInfo[supplierUid][0] == 0:
            self.globalCreditSuppliers[rank_id].remove(supplierUid)
            remind_suppliers[rank_id] -= 1
            if remind_suppliers[rank_id] <= 0:
                remind_suppliers[rank_id] = 0
                return None
            supplierUid = random.choice(self.globalCreditSuppliers[rank_id])

        return supplierUid


    def save(self):
        return (self.uid, (self.isGlobal, self.paramGroup, self.matched_info, self.active))

    def update(self, basic_info):
        self.isGlobal, self.paramGroup, self.matched_info, self.active = basic_info






