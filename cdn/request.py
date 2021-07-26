import numpy as np
import matplotlib.pyplot as plt


class Request:
    def __init__(self, size: np.array = np.array([]), probability: np.array = np.array([])):
        """
        This is just a profile holding probabilities (sum of requests normalized to 1)
        :param size: size of a request (Byte)
        :param probability: number of requests
        """
        assert size.shape == probability.shape, f"Shape mismatch: {size.shape}, {probability.shape}"

        if probability.size == 0:
            # it may be empty
            self._pmf = np.array([])
            self._cdf = np.array([])
            self._size = np.array([])
            self._volume = np.array([])
        else:
#            assert np.sum(probability).round(
#                3) == 1, f"Wrong sum on probabilities: {np.sum(probability)}, (elements: {probability.size})"
            assert np.sum(size) > 0, f"Wrong size sum: {np.sum(size)}"

            # determine ranking order
            order = np.argsort(probability)[::-1]

            # sort arrays and determine properties
            self._pmf = probability[order] / np.sum(probability)
            self._cdf = np.cumsum(self._pmf)

            self._size = size[order]
            self._volume = np.cumsum(self._size)
            assert self._pmf.shape == self._size.shape

    @property
    def sizes(self) -> np.ndarray:
        """
        Returns the size of each content in an array
        :return:
        """
        return self._size

    @property
    def volumes(self) -> np.ndarray:
        """
        Returns the cumulative sum of the size of each request according to a ranking order. It is useful for cdf
        plotting.
        :return:
        """
        return self._volume

    def pmf(self, volume) -> float:
        """
        Returns the probability of requests for volume. ~ the value of the pmf at point k, k measured as volume.
        :param volume:
        :return:
        """
        idx = (np.abs(self._volume - volume)).argmin()  # TODO: speed this up, list is already ordered...
        return self._pmf[idx]

    def cdf(self, volume) -> float:
        if self._pmf.size == 0:
            return 1
        idx = (np.abs(self._volume - volume)).argmin()
        return self._cdf[idx]

    def hit(self, volume: float):
        idx = (np.abs(self._volume - volume)).argmin()
        # tail the arrays and normalize them to get a real pdf.
        return Request(self._size[:idx], self._pmf[:idx] / np.sum(self._pmf[:idx]))

    def miss(self, volume: float):
        if self._pmf.size == 0:
            return Request()
        idx = (np.abs(self._volume - volume)).argmin()
        # tail the arrays and normalize them to get a real pdf.
        return Request(self._size[idx + 1:], self._pmf[idx + 1:] / np.sum(self._pmf[idx + 1:]))

    def consistenthashing(self, nodes: int, replication: int = 1):
        assert replication < nodes, f"replication {replication} is higher than nodes {nodes}!"

        # return [Request(self._size[n::nodes], self._pmf[n::nodes] / np.sum(self._pmf[n::nodes])) for n in range(nodes)]
        return [Request(np.concatenate([self._size[(n + r) % nodes::nodes] for r in range(replication)]),
                        np.concatenate([self._pmf[(n+r)%nodes::nodes] / np.sum(self._pmf[(n+r)%nodes::nodes]) for r in range(replication)])) for n in range(nodes)]

    def rps2bps(self, rps: float):
        """
        Determines the expected throughput from request pro sec (using meanrequestsize)
        :param rps:
        :return:
        """
        return rps * self.meanrequestsize * 8

    def bps2rps(self, bps: float):
        """
        Determines the expected requests pro sec from a throughput (usin meanrequestsize)
        :param bps:
        :return:
        """
        return bps / 8 / self.meanrequestsize

    @property
    def contentbase(self) -> int:
        return np.sum(self._size)

    @property
    def meanrequestsize(self):
        return np.sum(np.multiply(self._pmf, self._size))

    def describe(self):
        return f"*** {self.__class__.__name__} profile ***\n" \
               f"Number of contents: {self._pmf.size} ({self.contentbase / 1000 / 1000 / 1000 / 1000} TB)\n" \
               f"Mean request size: {self.meanrequestsize / 1000 / 1000:.2f} MB\n"

    def plot(self, axs, **kwargs):
        if axs is None:
            fig, axs = plt.subplots(1, 2)

        axs[0, 0].plot(self._volume / 1000 / 1000 / 1000, self._pmf, **kwargs)
        axs[0, 0].set_ylabel("probabbility")
        axs[0, 0].set_xlabel('volume (GB)')
        axs[0, 0].loglog()
        axs[0, 0].title.set_text('pmf')

        axs[0, 1].plot(self._volume / 1000 / 1000 / 1000, self._cdf, **kwargs)
        axs[0, 1].set_ylabel("probabbility")
        axs[0, 1].set_xlabel('volume (GB)')
        axs[0, 1].title.set_text('cdf')

        if axs is None:
            plt.show()

    def save(self, filename: str, axs=None, **kwargs):
        if axs is None:
            fig, axs = plt.subplots(1, 2)

        self.plot(axs)

        plt.savefig(filename)

    def plotstats(self, ax=None):
        if ax is None:
            fig, ax = plt.subplots()
            fig.suptitle(self.__class__.__name__)

        ax.loglog()
        ax.plot(self._volume, self._pmf)
        ax2 = ax.twinx()
        #        ax2.scatter(self._volume, self._cdf, **kwargs)
        ax.set_ylabel("probability")
        #        ax2.set_ylabel("probability")
        ax.set_xlabel('volume (Byte)')

        if ax is None:
            plt.show()
