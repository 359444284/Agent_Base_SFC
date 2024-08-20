import random
from collections import defaultdict
from markets.BasicMarket import BasicMarket
import numpy as np
from typing import Tuple, List, Dict
from repast4py import core


class LaborMarket(BasicMarket):

    def __init__(self, uid: Tuple, model, isGlobal: bool, paramGroup: int,
                 nround: int):
        super().__init__(uid, isGlobal, paramGroup, nround)

        self.params = model.params

        self.nround = nround

        self.matchStrategy = 0

        # {agentUid: [totalLoanDemand]}
        self.globalDemanderInfos = {}
        # {agentUid: [totalLoanSupply]}
        self.globalSupplierInfos = {}

        self.localDemanderInfos = {}
        self.localSupplierInfos = {}

        # Demander vs Supplier : one to many
        #
        self.globalDemanderUids = []
        self.globalSupplierUids = []

        # list of uid
        self.localDemanderUids = []
        # list of uid
        self.localSupplierUids = []

        self.matched_info = None

        self.reporterGhostList = []

        self.varify = True

    def process_transactions(self, rank_id, demander_idx, alive_demanders):
        demanderUid = self.globalDemanderUids[rank_id][demander_idx[rank_id] - 1]

        supplierUid = self.match_suppliers(rank_id)
        if supplierUid is None:
            return
        supplierInfo = self.globalSupplierInfos[supplierUid]

        laborDemand = supplierInfo[0]

        if laborDemand > 0:
            supplierInfo[0] -= 1

            self.matched_info[rank_id][demanderUid].append((supplierUid, ()))

            alive_demanders.remove(demanderUid)

            if supplierInfo[0] == 0:
                self.globalSupplierUids[rank_id].remove(supplierUid)


        demander_idx[rank_id] -= 1


    def shuffle_demanders(self, alive_demanders):
        for i, demanders in enumerate(self.globalDemanderUids):
            self.globalDemanderUids[i] = [uid for uid in demanders if uid in alive_demanders]
            random.shuffle(self.globalDemanderUids[i])

    def match_suppliers(self, rank_id):
        supplierUid = random.choice(self.globalSupplierUids[rank_id])
        while self.globalSupplierInfos[supplierUid][0] == 0:
            self.globalSupplierUids[rank_id].remove(supplierUid)
            if len(self.globalSupplierUids[rank_id]) <= 0:
                return None
            supplierUid = random.choice(self.globalSupplierUids[rank_id])

        return supplierUid

    def checksum(self):
        for v in self.globalSupplierInfos.values():
            if v[0] < 0:
                raise ValueError

        for v in self.globalDemanderInfos.values():
            if v[0] < 0:
                raise ValueError






