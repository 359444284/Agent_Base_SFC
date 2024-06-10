import math
import random
from collections import defaultdict

import numpy as np
from typing import Tuple, List, Dict
from repast4py import core

class ComsumptionMarket(core.Agent):

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
        self.globalDemandersUid = []
        self.globalSuppliersUid = []

        # list of uid
        self.demandersUid = []
        # list of uid
        self.suppliersUid = []

        self.matched_info = None

        self.reporterGhostList = []

    def collectSupplyer(self, supplierList):
        self.suppliersUid = supplierList

    def collectDemander(self, demandList):
        self.demandersUid = demandList

    def collectSupplyInfo(self, uid, info):
        self.localSuppliersInfo[uid] = info

    def collectDemandInfo(self, uid, info):
        self.localDemandersInfo[uid] = info

    def getInformationTableData(self):

        aggrate_data = (
            self.localDemandersInfo.copy(),
            self.localSuppliersInfo.copy(),
            self.demandersUid.copy(),
            self.suppliersUid.copy(),
            )

        # -- reset the delta to 0
        self.localSuppliersInfo = {}
        self.localDemandersInfo = {}
        self.demandersUid = []
        self.suppliersUid = []

        return aggrate_data

    def mergeInformationTableData(self):
        self.globalDemandersInfo = {}
        self.globalSuppliersInfo = {}
        self.globalDemandersUid = []
        self.globalSuppliersUid = []

        self.globalSuppliersInfo |= self.localSuppliersInfo
        self.globalDemandersInfo |= self.localDemandersInfo

        self.globalDemandersUid.append(self.demandersUid)
        self.globalSuppliersUid.append(self.suppliersUid)

        for theReporterGhost in self.reporterGhostList:
            self.globalDemandersInfo |= theReporterGhost.demandersInfo
            self.globalSuppliersInfo |= theReporterGhost.suppliersInfo
            self.globalDemandersUid.append(theReporterGhost.demandersUid)
            self.globalSuppliersUid.append(theReporterGhost.suppliersUid)

        self.localSuppliersInfo = {}
        self.localDemandersInfo = {}
        self.demandersUid = []
        self.suppliersUid = []

    def excute(self):
        # {demainderUid, [supplyerUid, amount]} for each rank
        self.matched_info = [defaultdict(list) for _ in range(len(self.globalSuppliersUid))]

        alive_demander = set(self.globalDemandersInfo.keys())
        remind_supplier = [len(ls) for ls in self.globalSuppliersUid]

        for _ in range(self.nround):

            self.shuffle_demanders(alive_demander)

            demander_idx = [len(ls) for ls in self.globalDemandersUid]

            while any(d * s > 0 for d, s in zip(demander_idx, remind_supplier)):
                for rank_id in range(len(demander_idx)):
                    if demander_idx[rank_id] <= 0 or remind_supplier[rank_id] <= 0:
                        continue

                    demanderUid = self.globalDemandersUid[rank_id][demander_idx[rank_id] - 1]
                    demanderInfo = self.globalDemandersInfo[demanderUid]

                    demandQuantity = demanderInfo[0]
                    demandAsset = demanderInfo[1]

                    if demandQuantity <= 0 or demandAsset <= 0:
                        alive_demander.remove(demanderUid)
                        demander_idx[rank_id] -= 1
                        continue



                    supplierUid = self.match_suppliers(rank_id, remind_supplier)
                    if supplierUid is None:
                        break
                    supplierInfo = self.globalSuppliersInfo[supplierUid]

                    price = supplierInfo[0]  # currently price is 1
                    offeredQuantity = supplierInfo[1]
                    offerValue = offeredQuantity * price


                    quantity = min(offeredQuantity, demandQuantity)
                    totalValue = offerValue

                    if offerValue > demandAsset:
                        # quantity = math.floor(demandAsset/price)
                        quantity = demandAsset/price
                        totalValue = quantity * price
                        demander_idx[rank_id] -= 1

                    if quantity > 0:
                        demanderInfo[0] -= quantity
                        demanderInfo[1] -= totalValue

                        supplierInfo[1] -= quantity

                        self.matched_info[rank_id][demanderUid].append((supplierUid, (price, quantity)))

                        if demanderInfo[0] == 0 or demanderInfo[1] == 0:
                            alive_demander.remove(demanderUid)

                        if supplierInfo[1] == 0:
                            self.globalSuppliersUid[rank_id].remove(supplierUid)
                            remind_supplier[rank_id] -= 1
                            if remind_supplier[rank_id] <= 0:
                                demander_idx[rank_id] = 0

                    demander_idx[rank_id] -= 1
            # print(self.matched_info)
            if len(alive_demander) == 0 or sum(remind_supplier) == 0:
                break

    def shuffle_demanders(self, alive_demanders):
        for i, demanders in enumerate(self.globalDemandersUid):
            self.globalDemandersUid[i] = [uid for uid in demanders if uid in alive_demanders]
            random.shuffle(self.globalDemandersUid[i])

    def match_suppliers(self, rank_id, remind_suppliers):
        supplierUid = random.choice(self.globalSuppliersUid[rank_id])
        while self.globalSuppliersInfo[supplierUid][0] == 0:
            self.globalSuppliersUid[rank_id].remove(supplierUid)
            remind_suppliers[rank_id] -= 1
            if remind_suppliers[rank_id] <= 0:
                remind_suppliers[rank_id] = 0
                return None
            supplierUid = random.choice(self.globalSuppliersUid[rank_id])
        return supplierUid

    def save(self):
        return self.uid, (self.isGlobal, self.paramGroup, self.matched_info)

    def update(self, basic_info):
        self.isGlobal, self.paramGroup, self.matched_info = basic_info







