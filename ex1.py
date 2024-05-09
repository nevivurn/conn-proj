#!/usr/bin/env python3

from matplotlib import pyplot as plt

from simulation import Simulation, ARQMode


def main() -> None:
    for w in [1, 7, 127]:
        xa = []
        y_util_gbn = []
        y_util_sr = []

        for a in [0.1, 1, 10, 100]:
            _, util_gbn = Simulation(
                mode=ARQMode.GO_BACK_N,
                window=w,
                prop_ratio=a,
            ).run()
            _, util_sr = Simulation(
                mode=ARQMode.SELECTIVE_REPEAT,
                window=w,
                prop_ratio=a,
            ).run()

            xa.append(a)
            y_util_gbn.append(util_gbn)
            y_util_sr.append(util_sr)

        plt.plot(xa, y_util_gbn, label=f'W={w} GBN')
        plt.plot(xa, y_util_sr, label=f'W={w} SR')

    plt.legend()

    plt.xlabel('Delay ratio')
    plt.ylabel('Utilization')
    plt.xscale('log')

    plt.savefig('figs/ex1.png')


if __name__ == '__main__':
    main()
