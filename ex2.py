#!/usr/bin/env python3

from matplotlib import pyplot as plt

from simulation import Simulation, ARQMode


def main() -> None:
    fig1, (ax1) = plt.subplots(1)
    fig2, (ax2) = plt.subplots(1)

    for w in [1, 7, 127]:
        xa = []
        y1_delay_gbn = []
        y1_delay_sr = []
        y2_delay_gbn = []
        y2_delay_sr = []

        for a in [0.1, 1, 10, 100]:
            delay_gbn_1, _ = Simulation(
                mode=ARQMode.GO_BACK_N,
                window=w,
                prop_ratio=a,
            ).run()
            delay_gbn_2, _ = Simulation(
                mode=ARQMode.GO_BACK_N,
                window=w,
                prop_ratio=a,
                fwd_err_rate=0.5, bwd_err_rate=0.5,
            ).run()
            delay_sr_1, _ = Simulation(
                mode=ARQMode.SELECTIVE_REPEAT,
                window=w,
                prop_ratio=a,
            ).run()
            delay_sr_2, _ = Simulation(
                mode=ARQMode.SELECTIVE_REPEAT,
                window=w,
                prop_ratio=a,
                fwd_err_rate=0.5, bwd_err_rate=0.5,
            ).run()

            xa.append(a)

            y1_delay_gbn.append(delay_gbn_1)
            y1_delay_sr.append(delay_sr_1)

            y2_delay_gbn.append(delay_gbn_2)
            y2_delay_sr.append(delay_sr_2)

        ax1.plot(xa, y1_delay_gbn, label=f'W={w} GBN')
        ax1.plot(xa, y1_delay_sr, label=f'W={w} SR')

        ax2.plot(xa, y2_delay_gbn, label=f'W={w} GBN')
        ax2.plot(xa, y2_delay_sr, label=f'W={w} SR')

    ax1.set_xlabel('Delay ratio')
    ax1.set_ylabel('Packet delay')
    ax1.set_xscale('log')
    ax1.set_yscale('log')
    ax1.set_title('No errors')
    ax1.legend()

    ax2.set_xlabel('Delay ratio')
    ax2.set_ylabel('Packet delay')
    ax2.set_xscale('log')
    ax2.set_yscale('log')
    ax2.set_title('50% errors')
    ax2.legend()

    fig1.savefig('figs/ex2_1.png')
    fig2.savefig('figs/ex2_2.png')


if __name__ == '__main__':
    main()
