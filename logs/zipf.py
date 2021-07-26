from scipy.optimize import curve_fit
from scipy.special import zetac
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def H(n: int, s: float):
    assert n > 0, f"negative parameter, s: {s}, n:{n}"
    return np.sum(np.arange(1, n + 1, ) ** (-s))


# zipf
def pmf(k: int, s: float, N: int):
#    assert all(k > 0) and s >= 0 and N > 0, f"negative parameter, k:{k}, s:{s}, N:{N}"
    return k ** -float(s) / H(N, s)


if __name__ == '__main__':
    df = pd.read_csv('svc40.csv', names=['ch', 'f'])
    x = np.arange(df.shape[0]) + 1
    y = np.array(df.f)

    N = df.shape[0]

    def zipf(k: int, s: float):
        return pmf(k, s, N)

#    popt, pcov = curve_fit(zipf, x, y, bounds=([0], [np.inf]))
#    print(popt)

    def neg_zipf_likelihood(s):
        probas = x ** (-s) / np.sum(np.arange(1, N + 1 ) ** (-s))
        log_likelihood = sum(np.log(probas) * x)
        return -log_likelihood


    from scipy.optimize import minimize_scalar

    s_best = minimize_scalar(neg_zipf_likelihood, [0.0001, 30.0])
    print(s_best)

    y2 = zipf(x, s_best.x)
    plt.plot(x, y)
    plt.plot(x, y2)
    plt.loglog()
    plt.show()
