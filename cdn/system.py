import numpy as np

from cdn import PoP, Cache, Request
from typing import Tuple


class System:
    def __init__(self, numpops: int, request: Request, ec: Cache, mc: Cache):
        self._numpops = numpops
        self._request = request
        self._pop = PoP(ec)
        self._mc = mc
        self._nummc = 1

    @property
    def nummc(self) -> int:
        return self._nummc

    @nummc.setter
    def nummc(self, val: int):
        assert isinstance(val, int) and val > 0, f"invalid number of mcs: {val}"
        self._nummc = val

    @property
    def numecpop(self) -> int:
        return self._pop.numcache

    @numecpop.setter
    def numecpop(self, val: int):
        self._pop.numcache = val

    @property
    def replication(self) -> int:
        return self._pop.replication

    @replication.setter
    def replication(self, val: int):
        self._pop.replication = val

    @property
    def nummodulesec(self) -> int:
        return self._pop.nummodules

    @nummodulesec.setter
    def nummodulesec(self, val: int):
        self._pop.nummodules = val

    @property
    def nummodulesmc(self) -> int:
        return self._mc.nummodules

    @nummodulesmc.setter
    def nummodulesmc(self, val: int):
        self._mc.nummodules = val

    @property
    def storageec(self) -> int:
        return self._pop.storage

    @property
    def storage1ec(self) -> int:
        return self._pop.storage1ec

    @storage1ec.setter
    def storage1ec(self, percent: float):
        self._pop.storage1ec = percent

    @property
    def storagemc(self) -> int:
        return self._mc.storage

    @property
    def isvalid(self)-> bool:
        return self._pop.isvalid

    @property
    def cost(self)-> float:
        return self._numpops * self._pop.cost + self._nummc * self._mc.cost

    def ingress(self, numrequests: int, egress: Request) -> Tuple[int, Request, float, float, int, Request, float, float]:
        """

        :param numrequests:
        :param egress:
        :return: tuple ()
        """
        # get ingress after one PoP:
        rps2, ingress2, util_ec, chr_ec = self._pop.ingress(int(numrequests / self._numpops), egress)

        # get ingress after mastercache cluster:
        rps3 = int(rps2 * self._numpops * (1 - ingress2.cdf(self._nummc * self._mc.storage)))
        ingress3 = ingress2.miss(self._nummc * self._mc.storage)
        util_mc = ingress2.rps2bps(rps2 * self._numpops / self._nummc) / self._mc.capacity
        chr_mc = 1-(rps3/rps2) if rps2 != 0 else np.nan

        return rps2, ingress2, util_ec, chr_ec,\
               rps3, ingress3, util_mc, chr_mc