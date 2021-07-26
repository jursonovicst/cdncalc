from cdn import Request, Cache
from typing import Tuple


class PoP:
    def __init__(self, cache: Cache):
        self._cache = cache
        self._numcache = 1
        self._storage1ec = 0.1
        self._replication = 1

    @property
    def replication(self) -> int:
        return self._replication

    @replication.setter
    def replication(self, val: int):
        assert isinstance(val,
                          int) and val > 0, f"non positive replication: {val}, (replication 1 --> object only one on the pop"
        self._replication = val

    @property
    def numcache(self):
        return self._numcache

    @numcache.setter
    def numcache(self, val: int):
        assert isinstance(val, int) and val > 0, f"non positive number of caches: {val}"
        self._numcache = val

    @property
    def maxmodules(self):
        return self._cache.maxmodules

    @property
    def minmodules(self):
        return self._cache.minmodules

    @property
    def nummodules(self) -> int:
        return self._cache.nummodules

    @nummodules.setter
    def nummodules(self, val: int):
        self._cache.nummodules = val

    @property
    def storage(self):
        return self._cache.storage

    @property
    def storage1ec(self) -> int:
        return int(self._storage1ec * self._cache.storage)

    @storage1ec.setter
    def storage1ec(self, percent: float):
        assert 0 <= percent <= 1, f"Wrong storage1: {percent}"
        self._storage1ec = percent

    def ingress(self, rps: int, egress: Request) -> Tuple[int, Request, float, float]:
        """

        :param rps: interpreted on the PoP
        :param egress:
        :return: tuple of (ingress number of requests, ingress Request profile, ec utilization, ec CHR)
        """
        # calculate the numrequests1 and ingress1 (after the first, dedicated storage1) total for all caches
        rps1, ingress1 = int(rps * (1 - egress.cdf(self.storage1ec))), egress.miss(self.storage1ec)

        # calculate rps2, ingress2 (considering consistent hashing and replication)
        rps2 = int(rps1 * (1 - ingress1.cdf(self._numcache * (self._cache.storage - self.storage1ec) / self._replication)))
        ingress2 = ingress1.miss(self._numcache * (self._cache.storage - self.storage1ec) / self._replication)

        # utilization is just throughput on it / capacity
        util_ec = (egress.rps2bps(rps / self._numcache) + ingress1.rps2bps(rps1) / self._numcache) / self._cache.capacity

        # chr is 1 - all miss / all requests
        chr_ec = 1 - (rps1 + rps2) / (rps + rps1)

        return rps2, ingress2, util_ec, chr_ec

    @property
    def cost(self):
        return self._numcache * self._cache.cost
