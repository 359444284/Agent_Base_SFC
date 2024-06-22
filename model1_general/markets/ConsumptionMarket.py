import math
import random
from collections import defaultdict
from markets.BasicMarket import BasicMarket
import numpy as np
from typing import Tuple, List, Dict
from repast4py import core

class ComsumptionMarket(BasicMarket):

    def __init__(self, uid: Tuple, params: Dict, isGlobal: bool, paramGroup: int,
                 nround:int):
        super().__init__(uid, isGlobal, paramGroup, nround)

        self.params = params

        self.nround = nround

        self.matchStrategy = 0


        # {agentUid: [totalLoanDemand]}
        self.globalDemanderInfos = {}
        # {agentUid: [totalLoanSupply]}
        self.globalSupplierInfos = {}

        self.localDemanderInfos = {}
        self.localSupplierInfos = {}

        # Demander vs Supplier : one to many
        # market participants in each rank
        self.globalDemanderUids = []
        self.globalSupplierUids = []

        # list of uid
        self.localDemanderUids = []
        # list of uid
        self.localSupplierUids = []

        self.matched_info = None

        self.varify = True

    def process_transactions(self, rank_id, demander_idx, remind_supplier, alive_demander):
        demanderUid = self.globalDemanderUids[rank_id][demander_idx[rank_id] - 1]
        demanderInfo = self.globalDemanderInfos[demanderUid]

        demandQuantity = demanderInfo[0]
        demandAsset = demanderInfo[1]

        if demandQuantity <= 0 or demandAsset <= 0:
            alive_demander.remove(demanderUid)
            demander_idx[rank_id] -= 1
            return

        supplierUid = self.match_suppliers(rank_id, remind_supplier)
        if supplierUid is None:
            return

        supplierInfo = self.globalSupplierInfos[supplierUid]

        price = supplierInfo[0]  # currently price is 1
        offeredQuantity = supplierInfo[1]
        offerValue = offeredQuantity * price

        quantity = min(offeredQuantity, demandQuantity)
        totalValue = offerValue

        if offerValue > demandAsset:
            # quantity = math.floor(demandAsset/price)
            quantity = demandAsset / price
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
                self.globalSupplierUids[rank_id].remove(supplierUid)
                remind_supplier[rank_id] -= 1

        demander_idx[rank_id] -= 1

    def shuffle_demanders(self, alive_demanders):
        for i, demanders in enumerate(self.globalDemanderUids):
            self.globalDemanderUids[i] = [uid for uid in demanders if uid in alive_demanders]
            random.shuffle(self.globalDemanderUids[i])

    def match_suppliers(self, rank_id, remind_suppliers):
        supplierUid = random.choice(self.globalSupplierUids[rank_id])
        while self.globalSupplierInfos[supplierUid][0] == 0:
            self.globalSupplierUids[rank_id].remove(supplierUid)
            remind_suppliers[rank_id] -= 1
            if remind_suppliers[rank_id] <= 0:
                remind_suppliers[rank_id] = 0
                return None
            supplierUid = random.choice(self.globalSupplierUids[rank_id])
        return supplierUid

    def checksum(self):
        for v in self.globalSupplierInfos.values():
            if v[0] < 0:
                raise ValueError

        for v in self.globalDemanderInfos.values():
            if v[0] < 0 or v[1] < 0:
                raise ValueError






