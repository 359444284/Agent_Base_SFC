import math
import random
from abc import abstractmethod, ABC
from collections import defaultdict

import numpy as np
from typing import Tuple, List, Dict
from repast4py import core


class BasicMarket(core.Agent, ABC):

    def __init__(self, uid: Tuple, isGlobal: bool, paramGroup: int, nround: int):
        super().__init__(id=uid[0], type=uid[1], rank=uid[2])

        self.isGlobal = isGlobal
        self.paramGroup = paramGroup
        self.nround = nround

        self.matchStrategy = 0


        # {agentUid: [totalLoanDemand]}
        self.globalDemanderInfos = None
        # {agentUid: [totalLoanSupply]}
        self.globalSupplierInfos = None

        self.localDemanderInfos = None
        self.localSupplierInfos = None

        # Demander vs Supplier : one to many
        # market participants in each rank
        self.globalDemanderUids = None
        self.globalSupplierUids = None

        # list of uid
        self.localDemanderUids = None
        # list of uid
        self.localSupplierUids = None

        self.matched_info = None

        self.reporterGhostList = []
        self.verify = False

    def collectSupplyer(self, supplierList):
        self.localSupplierUids = supplierList

    def collectDemander(self, demandList):
        self.localDemanderUids = demandList

    def collectSupplyInfo(self, uid, info):
        self.localSupplierInfos[uid] = info

    def collectDemandInfo(self, uid, info):
        self.localDemanderInfos[uid] = info

    def getInformationTableData(self):

        aggrate_data = (
            self.localDemanderInfos.copy(),
            self.localSupplierInfos.copy(),
            self.localDemanderUids.copy(),
            self.localSupplierUids.copy(),
        )

        # -- reset the delta to 0
        self.localDemanderInfos = {}
        self.localSupplierInfos = {}
        self.localDemanderUids = []
        self.localSupplierUids = []

        return aggrate_data

    def mergeInformationTableData(self):
        self.globalDemanderInfos = {}
        self.globalSupplierInfos = {}
        self.globalDemanderUids = []
        self.globalSupplierUids = []

        self.globalSupplierInfos |= self.localSupplierInfos
        self.globalDemanderInfos |= self.localDemanderInfos

        self.globalDemanderUids.append(self.localDemanderUids)
        self.globalSupplierUids.append(self.localSupplierUids)

        for theReporterGhost in self.reporterGhostList:
            self.globalDemanderInfos |= theReporterGhost.demandersInfo
            self.globalSupplierInfos |= theReporterGhost.suppliersInfo
            self.globalDemanderUids.append(theReporterGhost.demandersUid)
            self.globalSupplierUids.append(theReporterGhost.suppliersUid)

        self.localSupplierInfos = {}
        self.localDemanderInfos = {}
        self.localDemanderUids = []
        self.localSupplierUids = []

    def getMatchResult(self, rank):
        if self.isGlobal:
            return self.matched_info[rank]
        else:
            return self.matched_info[0]

    # process each rank's market sequentially. Each rank has equal opportunity to interact with global agents
    def execute(self):
        self.matched_info = [defaultdict(list) for _ in range(len(self.globalDemanderUids))]

        alive_demander = set(self.globalDemanderInfos.keys())

        for i, localSupplierUids in enumerate(self.globalSupplierUids):
            self.globalSupplierUids[i] = [uid for uid in localSupplierUids if uid in self.globalSupplierInfos]

        for _ in range(self.nround):
            self.shuffle_demanders(alive_demander)
            demander_idx = [len(ls) for ls in self.globalDemanderUids]

            active_ranks = list(range(len(self.globalDemanderUids)))

            while active_ranks:
                for rank_id in active_ranks.copy():  # Copy to allow modification during iteration
                    if demander_idx[rank_id] <= 0 or len(self.globalSupplierUids[rank_id]) <= 0:
                        active_ranks.remove(rank_id)
                        continue

                    self.process_transactions(rank_id, demander_idx, alive_demander)

                    if not (demander_idx[rank_id] > 0 and len(self.globalSupplierUids[rank_id]) > 0):
                        active_ranks.remove(rank_id)

        if self.verify:
            self.checksum()

    def shuffle_demanders(self, alive_demanders):
        for i, demanders in enumerate(self.globalDemanderUids):
            self.globalDemanderUids[i] = [uid for uid in demanders if uid in alive_demanders]
            random.shuffle(self.globalDemanderUids[i])

    @abstractmethod
    def process_transactions(self, rank_id, demander_idx, alive_demander):
        pass

    @abstractmethod
    def match_suppliers(self, rank_id):
        supplierUid = random.choice(self.globalSupplierUids[rank_id])
        while self.globalSupplierInfos[supplierUid][0] == 0:
            self.globalSupplierUids[rank_id].remove(supplierUid)
            if len(self.globalSupplierUids[rank_id]) == 0:
                return None
            supplierUid = random.choice(self.globalSupplierUids[rank_id])

        return supplierUid

    # Checking Data Integrity
    @abstractmethod
    def checksum(self):
        pass

    def save(self):
        return self.uid, (self.isGlobal, self.paramGroup, self.matched_info)

    def update(self, basic_info):
        self.isGlobal, self.paramGroup, self.matched_info = basic_info







