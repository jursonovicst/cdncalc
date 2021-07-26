from cdn import System, LiveTV, DellR750
import argparse
import numpy as np
import pandas as pd
from tqdm.auto import tqdm
import datetime

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='CDN designer.')
    parser.add_argument('--channels', type=int, help='number of liveTV channels', required=True)
    parser.add_argument('--zipf', metavar='s', nargs=1,
                        help='Use zipf distribution to model channel popularity, s parameter', required=True)
    parser.add_argument('--timeshift', type=float, nargs=3, metavar=('LEN', 'MEAN', 'STDDEV'),
                        help='timeshift parameters (h)', required=True)
    parser.add_argument('--fragmentlen', type=float, help='length of a streaming fragment (s)', required=True)
    parser.add_argument('--profiles', type=float, nargs='+', help='Weights of profiles', required=True)
    parser.add_argument('--bandwidths', type=float, nargs='+', help='List of profile bandwidths (Mbps)', required=True)
    #    parser.add_argument('--formats', type=int, nargs='+', help='weights of streaming formats (HLS, DASH, etc...)',
    #                        required=True)
    parser.add_argument('--peak', type=float, help='maximum peak load (Tbps)', required=True)
    parser.add_argument('--pops', type=int, help='number of PoPs', required=True)
    parser.add_argument('--iterations', type=int, help='number of Monte Carlo iterations', required=True)

    args = parser.parse_args()

    pd.set_option('display.max_columns', None)  # or 1000
    pd.set_option('display.max_rows', None)  # or 1000
    pd.set_option('display.max_colwidth', None)  # or 199
    pd.set_option('display.width', None)

    channels = args.channels
    tslen = args.timeshift[0] * 60 * 60
    tsmean = args.timeshift[1] * 60 * 60
    tsstddev = args.timeshift[2] * 60 * 60
    fragmentlen = args.fragmentlen
    fragmentnum = round(tslen / fragmentlen)
    profiles = args.profiles
    bandwidths = np.array(args.bandwidths) * 1000 * 1000
    #    formats = args.formats
    peak = args.peak * 1000 * 1000 * 1000 * 1000
    pops = args.pops

    # create request model
    request = LiveTV(channels, fragmentnum, profiles, bandwidths / 8 * fragmentlen, 1.56, tsmean / fragmentlen,
                     tsstddev / fragmentlen)
    #    request.plot()
    #    request.plotstats()
    print(request.describe(fragmentlen))
    request.plot()

    # create CDN model
    ec = DellR750()
    mc = DellR750()
    cdn = System(pops, request, ec, mc)

    # determine number of request from throughput
    numrequests = request.bps2rps(peak)
    print(f"Total CDN throughput: {peak / 1000 / 1000 / 1000 / 1000:.2f} Tbps\n"
          f"Expected requests: {numrequests:.0f} 1/s\n"
          f"Number of PoPs: {pops}\n")

    # monte carlo
    iterations = args.iterations
    results = pd.DataFrame(columns=['egress_pop_Gbps', 'numecpop', 'storageec_GB', 'storage1ec_GB', 'replication','chr_ec','util_ec','ingress_pop_Gbps',
                                    'egress_mc_Gbps', 'nummc', 'storagemc_GB', 'chr_mc', 'util_mc',
                                    'valid', 'cost'])
    with tqdm(total=iterations) as pbar:
        try:
            for i in range(iterations):

                # play with various edge cache number and sizes
                cdn.replication = np.random.randint(1, 10+1)
                cdn.storage1ec = np.random.random()  # ratio
                cdn.nummodulesec = np.random.randint(ec.minmodules, ec.maxmodules + 1)
                cdn.numecpop = np.random.randint(1, 40 + 1)

                # play with various master cache memory config, but keep the overall storage at content base
                cdn.nummodulesmc = np.random.randint(mc.minmodules, mc.maxmodules + 1)
                cdn.nummc = int(np.ceil(request.contentbase / cdn.storagemc))

                # determine origin load
                rps2, ingress2, util_ec, chr_ec, rps3, ingress3, util_mc, chr_mc = cdn.ingress(numrequests, request)

                valid = True
                if util_ec > 1 or util_mc > 1:
                    valid = False
                results = results.append({'egress_pop_Gbps': np.round(peak / pops / 1000 / 1000 / 1000),
                                          'numecpop': cdn.numecpop,
                                          'storageec_GB': cdn.storageec / 1000 / 1000 / 1000,
                                          'storage1ec_GB': np.round(cdn.storage1ec / 1000 / 1000 / 1000),
                                          'replication': cdn.replication,
                                          'chr_ec': np.round(chr_ec * 100,2),
                                          'util_ec': np.round(util_ec * 100,2),
                                          'ingress_pop_Gbps': np.round(ingress2.rps2bps(rps2) / 1000 / 1000 / 1000, 2),
                                          'egress_mc_Gbps': np.round (ingress2.rps2bps(rps2) * pops / cdn.nummc / 1000 / 1000 / 1000, 2),
                                          'nummc': cdn.nummc,
                                          'storagemc_GB': cdn.storagemc / 1000 / 1000 / 1000,
                                          'chr_mc': np.round(chr_mc * 100,2),
                                          'util_mc': np.round(util_mc * 100,2),
                                          'valid': valid, 'cost': cdn.cost}, ignore_index=True)
                pbar.update(1)
        except KeyboardInterrupt:
            pass

    results.sort_values(by=['valid', 'cost'], ascending=False, inplace=True)
    now = datetime.datetime.now()
    with open(f"/data/cdn{now}.csv", 'at') as f:
        for line in request.describe(fragmentlen).splitlines():
            f.write(f"# {line}\n")

        f.write(f"#\n"
                f"# Total CDN throughput: {peak / 1000 / 1000 / 1000 / 1000:.2f} Tbps\n"
                f"# Expected requests: {numrequests:.0f} 1/s\n"
                f"# Number of PoPs: {pops}\n"
                f"#\n")

        results.to_csv(f)
    request.save(f"/data/requests_{now}.png")
    print(results)


    # print(f"Total origin throughput: {egress_o.rps2bps(numrequests_o) / 1000 / 1000 / 1000:.2f} Gbps\n"
    #       f"Expected requests: {numrequests_o:.0f} 1/s\n"
    #       f"EC Utilization: {util_ec*100:.0f} %\n"
    #       f"MC Utilization: {util_mc*100:.0f} %\n"
    #       f"CDN Cost: {cdn.cost():.0f} €")
