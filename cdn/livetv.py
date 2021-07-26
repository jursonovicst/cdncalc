import numpy as np
from scipy.stats import zipfian, norm
import matplotlib.pyplot as plt
from cdn import Request


class LiveTV(Request):
    def __init__(self, channels: int, fragments: int, profiles: np.array, profilesizes: np.ndarray,
                 s: float, tsmu: float, tssigma: float):
        self._channels = channels
        self._fragments = fragments
        self._profiles = profiles
        self._profilesizes = profilesizes
        self._s = s
        self._tsmu = tsmu
        self._tssigma = tssigma

        # generate pmf for all dimensions

        # use zipf distribution for channel popularity
        self.channelpmf = zipfian.pmf(np.arange(1, channels + 1), s, channels)
        assert np.sum(self.channelpmf).round(3) == 1, f"channel PMF is invalid, {np.sum(self.channelpmf)}"
        assert len(self.channelpmf) == channels, f'channel PMF wrong length: {len(self.channelpmf)}'

        # use normal distribution for fragment popularity (with mean timeshift)
        self.fragmentpmf = norm.pdf(np.arange(1, fragments + 1), tsmu, tssigma)
        self.fragmentpmf = self.fragmentpmf / sum(self.fragmentpmf)
        assert np.sum(self.fragmentpmf).round(3) == 1, f"fragmentpmf PMF is invalid, {np.sum(self.fragmentpmf)}"
        assert len(self.fragmentpmf) == fragments, f'fragmentpmf PMF wrong length: {len(self.fragmentpmf)}'

        # use linear for profiles
        self.profilempf = profiles / np.sum(profiles)
        assert np.sum(self.profilempf).round(3) == 1, f"profilempf PMF is invalid, {np.sum(self.profilempf)}"
        assert len(self.profilempf) == len(profiles), f'profilempf PMF wrong length: {len(self.profilempf)}'

        # create pmf matrix
        pmf = np.prod((self.channelpmf.reshape((len(self.channelpmf), 1, 1)),
                       self.fragmentpmf.reshape((1, len(self.fragmentpmf), 1)),
                       self.profilempf.reshape((1, 1, len(self.profilempf)))))
        assert np.sum(pmf).round(3) == 1, f"final PMF is invalid, {np.sum(pmf)}"
        assert pmf.shape == (
            len(self.channelpmf), len(self.fragmentpmf), len(self.profilempf)), f"Wrong shape: {pmf.shape}"
        for ch, fr, p in zip(np.random.randint(len(self.channelpmf), size=100),
                             np.random.randint(len(self.fragmentpmf), size=100),
                             np.random.randint(len(self.profilempf), size=100)):
            assert pmf[ch, fr, p] == self.channelpmf[ch] * self.fragmentpmf[fr] * self.profilempf[p]

        # create size matrix
        size = np.prod((np.ones((len(self.channelpmf), 1, 1)),
                        np.ones((1, len(self.fragmentpmf), 1)),
                        profilesizes.reshape((1, 1, len(profilesizes)))))

        super().__init__(size=size.flatten(), probability=pmf.flatten())

    def plot(self, axs=None, **kwargs):
        if axs is None:
            fig, axs = plt.subplots(3, 2)

#        fig.suptitle(self.__class__.__name__)
        plt.subplots_adjust(hspace=0.5, wspace=0.3)

        axs[1, 0].title.set_text('channel pmf')
        axs[1, 0].set_ylabel("probability")
        axs[1, 0].set_xlabel("channel")
        axs[1, 0].plot(np.arange(self.channelpmf.size), self.channelpmf, **kwargs)

        axs[1, 1].title.set_text('fragment pmf')
        axs[1, 1].set_ylabel("probability")
        axs[1, 1].set_xlabel("fragment")
        axs[1, 1].plot(self.fragmentpmf, **kwargs)

        axs[2, 0].title.set_text('profile pmf')
        axs[2, 0].set_ylabel("probability")
        axs[2, 0].bar(np.arange(self._profilesizes.size), self.profilempf, tick_label=self._profilesizes, **kwargs)
        axs[2, 0].tick_params(labelrotation=45)

        super().plot(axs=axs, **kwargs)

        if axs is None:
            plt.show()

    def save(self, filename: str, axs=None, **kwargs):
        if axs is None:
            fig, axs = plt.subplots(3, 2)

        fig.set_size_inches(18.5, 10.5)
        super().save(filename, axs, **kwargs)

    def describe(self, fragmentlen: float):
        return f"{super().describe()}" \
               f"Number of channels: {self._channels}\n" \
               f"Number of fragments: {self._fragments}\n" \
               f"Zipf parameter: {self._s:.2f}\n" \
               f"Timeshift mean {self._tsmu * fragmentlen/60/60:.1f} h ({self._tsmu:.0f} fragment)\n" \
               f"Timeshift stddev {self._tssigma * fragmentlen/60/60:.1f} ({self._tssigma:.0f} fragment)\n" \
               f"Profiles: {self._profilesizes / fragmentlen * 8 / 1000 / 1000} Mbps\n"

#               f"Profiles: {[x for x in self._profiles]}\n"s
