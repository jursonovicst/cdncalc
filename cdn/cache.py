from cdn import Request
from typing import Tuple


class Cache:
    def __init__(self, capacity: float, modulesize: int, moduleprice: float, maxmodules: int, baseprice: float):
        self._capacity = capacity
        self._modulesize = modulesize
        self._moduleprice = moduleprice
        self._maxmodules = maxmodules
        self._nummodules = self.minmodules
        self._baseprice = baseprice

    @property
    def capacity(self):
        return self._capacity

    @property
    def modulesize(self):
        return self._modulesize

    @property
    def maxmodules(self) -> int:
        return self._maxmodules

    @property
    def minmodules(self) -> int:
        return 1

    @property
    def nummodules(self) -> int:
        return self._nummodules

    @nummodules.setter
    def nummodules(self, val: int):
        assert isinstance(val, int ) and self.minmodules <= val <= self.maxmodules, f"Invalid nummodules: {val}"
        self._nummodules = val

    @property
    def storage(self):
        return self._nummodules * self._modulesize

    @property
    def cost(self):
        return self._baseprice + self._nummodules * self._moduleprice

    def ingress(self, rps: int, egress: Request) -> Tuple[int, Request, float]:
        """
        Returns the
         - expected number of requests
         - ingress Request profile after caching
         - cache utilization
        :param rps: interpreted on the cache
        :param egress:
        :return:
        """
        return int(rps * (1 - egress.cdf(self.storage))), \
               egress.miss(self.storage), \
               egress.rps2bps(rps) / self._capacity

class DellR750(Cache):
    def __init__(self):
        #  16GB, 32GBm 64GB, 128GB; 16 DIMMS, 32DIMMs
        #
        #  16GB:  256GB,  512GB
        #  32GB:  512GB, 1024GB
        #  64GB: 1024GB, 2048GB
        # 128GB: 2024GB, 4096GB
        #
        # modulsize: 256GB, maxmodules: 16
        super().__init__(160 * 1000 * 1000 * 1000, 256 * 1000 * 1000 * 1000, 256*28, 16, 10000)
