#!/usr/bin/env python

import argparse
from operator import itemgetter

from migen import *
from migen.build.platforms import ebaz4205
from migen.build.generic_platform import Pins, Subsignal, IOStandard, Misc
from migen_axi.integration.soc_core import SoCCore
from misoc.interconnect.csr import *

from artiq.gateware import rtio
from artiq.gateware.rtio.phy import (
    ttl_simple,
    dds,  # Need to create module for AD9834
)
from artiq.gateware.rtio.xilinx_clocking import fix_serdes_timing_path

import dma
import analyzer

from config import write_csr_file, write_mem_file, write_rustc_cfg_file


__all__ = ["Platform"]

_ps = [
    (
        "ps",
        0,
        Subsignal("clk", Pins("E7"), IOStandard("LVCMOS33"), Misc("SLEW=FAST")),
        Subsignal("por_b", Pins("C7"), IOStandard("LVCMOS33"), Misc("SLEW=FAST")),
        Subsignal("srst_b", Pins("B10"), IOStandard("LVCMOS18"), Misc("SLEW=FAST")),
    )
]

_ddr = [
    (
        "ddr",
        0,
        Subsignal(
            "a",
            Pins("N2 K2 M3 K3 M4 L1 L4 K4 K1 J4 F5 G4 E4 D4 F4"),
            IOStandard("SSTL15"),
        ),
        Subsignal("ba", Pins("L5 R4 J5"), IOStandard("SSTL15")),
        Subsignal("cas_n", Pins("P5"), IOStandard("SSTL15")),
        Subsignal("cke", Pins("N3"), IOStandard("SSTL15")),
        Subsignal("cs_n", Pins("N1"), IOStandard("SSTL15")),
        Subsignal("ck_n", Pins("M2"), IOStandard("DIFF_SSTL15"), Misc("SLEW=FAST")),
        Subsignal("ck_p", Pins("L2"), IOStandard("DIFF_SSTL15"), Misc("SLEW=FAST")),
        # Pins "T1 Y1" not connected
        Subsignal("dm", Pins("A1 F1"), IOStandard("SSTL15_T_DCI"), Misc("SLEW=FAST")),
        Subsignal(
            "dq",
            Pins("C3 B3 A2 A4 D3 D1 C1 E1 E2 E3 G3 H3 J3 H2 H1 J1"),
            # Pins "P1 P3 R3 R1 T4 U4 U2 U3 V1 Y3 W1 Y4 Y2 W3 V2 V3" not connected
            IOStandard("SSTL15_T_DCI"),
            Misc("SLEW=FAST"),
        ),
        Subsignal(
            "dqs_n",
            Pins("B2 F2"),  # Pins "T2 W4" not connected
            IOStandard("DIFF_SSTL15_T_DCI"),
            Misc("SLEW=FAST"),
        ),
        Subsignal(
            "dqs_p",
            Pins("C2 G2"),  # Pins "R2 W5" not connected
            IOStandard("DIFF_SSTL15_T_DCI"),
            Misc("SLEW=FAST"),
        ),
        Subsignal("vrn", Pins("G5"), IOStandard("SSTL15_T_DCI"), Misc("SLEW=FAST")),
        Subsignal("vrp", Pins("H5"), IOStandard("SSTL15_T_DCI"), Misc("SLEW=FAST")),
        Subsignal("drst_n", Pins("B4"), IOStandard("SSTL15"), Misc("SLEW=FAST")),
        Subsignal("odt", Pins("N5"), IOStandard("SSTL15")),
        Subsignal("ras_n", Pins("P4"), IOStandard("SSTL15")),
        Subsignal("we_n", Pins("M5"), IOStandard("SSTL15")),
    )
]


class EBAZ4205(SoCCore):
    def __init__(self, acpki=False):
        self.acpki = acpki

        platform = ebaz4205.Platform()
        platform.toolchain.bitstream_commands.extend(
            [
                "set_property BITSTREAM.GENERAL.COMPRESS True [current_design]",
            ]
        )
        platform.add_extension(_ps)
        platform.add_extension(_ddr)

        gmii = platform.request("gmii")
        platform.add_period_constraint(gmii.rx_clk, 10)
        platform.add_period_constraint(gmii.tx_clk, 10)

        gmii_txd = Signal(8)
        gmii_rxd = Signal(8)
        gmii_tx_er = Signal()
        gmii_rx_er = Signal()
        gmii_crs = Signal()
        gmii_col = Signal()

        self.comb += [
            gmii_tx_er.eq(0),
            gmii_rx_er.eq(0),
            gmii_crs.eq(0),
            gmii_col.eq(0),
            gmii_txd.eq(0),
            gmii_rxd.eq(0),
            gmii_txd.eq(Cat(gmii.txd, Signal(4, reset=0, name="gmii_txd0"))),
            gmii_rxd.eq(Cat(gmii.rxd, Signal(4, reset=0, name="gmii_rxd0"))),
        ]
        gmii_layout = gmii.layout[2:] + [
            (sig.backtrace[-1][0].split("_", 1)[-1], sig.nbits)
            for sig in [gmii_txd, gmii_rxd, gmii_tx_er, gmii_rx_er, gmii_crs, gmii_col]
        ]
        gmii_rec = Record(gmii_layout)
        ident = self.__class__.__name__
        if self.acpki:
            ident = "acpki_" + ident
        SoCCore.__init__(
            self, platform=platform, csr_data_width=32, ident=ident, enet0=gmii_rec
        )
        fix_serdes_timing_path(platform)
        # When using pd_cd_sys, the default clock coming from fclk.clk[0] is 100 MHz
        self.config["RTIO_FREQUENCY"] = "100"
        platform.add_period_constraint(self.ps7.cd_sys.clk, 10)

        mdio = platform.request("mdio")
        mdio_i = Signal(name_override="i")
        mdio_o = Signal(name_override="o")
        mdio_t_n = Signal(name_override="t_n")
        self.comb += [
            mdio_i.eq(self.ps7.enet0.enet.mdio.o),
            self.ps7.enet0.enet.mdio.i.eq(mdio_o),
            mdio_t_n.eq(self.ps7.enet0.enet.mdio.t_n),
            self.ps7.enet0.enet.mdio.mdc.eq(mdio.mdc),
        ]
        self.specials += [
            Instance("IOBUF", i_I=mdio_i, io_IO=mdio.mdio, o_O=mdio_o, i_T=mdio_t_n)
        ]

        self.rtio_channels = []
        for i in (0, 1):
            print("USER LED at RTIO channel 0x{:06x}".format(len(self.rtio_channels)))
            user_led = self.platform.request("user_led", i)
            phy = ttl_simple.Output(user_led)
            self.submodules += phy
            self.rtio_channels.append(rtio.Channel.from_phy(phy))
        self.config["RTIO_LOG_CHANNEL"] = len(self.rtio_channels)
        self.rtio_channels.append(rtio.LogChannel())

        self.submodules.rtio_tsc = rtio.TSC(glbl_fine_ts_width=3)
        self.submodules.rtio_core = rtio.Core(self.rtio_tsc, self.rtio_channels)
        self.csr_devices.append("rtio_core")
        if self.acpki:
            import acpki

            self.config["KI_IMPL"] = "acp"
            self.submodules.rtio = acpki.KernelInitiator(
                self.rtio_tsc,
                bus=self.ps7.s_axi_acp,
                user=self.ps7.s_axi_acp_user,
                evento=self.ps7.event.o,
            )
            self.csr_devices.append("rtio")
        else:
            self.config["KI_IMPL"] = "csr"
            self.submodules.rtio = rtio.KernelInitiator(self.rtio_tsc, now64=True)
            self.csr_devices.append("rtio")

        self.submodules.rtio_dma = dma.DMA(self.ps7.s_axi_hp0)
        self.csr_devices.append("rtio_dma")

        self.submodules.cri_con = rtio.CRIInterconnectShared(
            [self.rtio.cri, self.rtio_dma.cri], [self.rtio_core.cri]
        )
        self.csr_devices.append("cri_con")

        self.submodules.rtio_moninj = rtio.MonInj(self.rtio_channels)
        self.csr_devices.append("rtio_moninj")

        self.submodules.rtio_analyzer = analyzer.Analyzer(
            self.rtio_tsc, self.rtio_core.cri, self.ps7.s_axi_hp1
        )
        self.csr_devices.append("rtio_analyzer")


def main():
    parser = argparse.ArgumentParser(
        description="ARTIQ port to the EBAZ4205 control card of Ebit E9+ BTC miner"
    )
    parser.add_argument(
        "-r", default=None, help="build Rust interface into the specified file"
    )
    parser.add_argument(
        "-m", default=None, help="build Rust memory interface into the specified file"
    )
    parser.add_argument(
        "-c",
        default=None,
        help="build Rust compiler configuration into the specified file",
    )
    parser.add_argument(
        "-g", default=None, help="build gateware into the specified directory"
    )
    parser.add_argument(
        "--acpki", default=False, action="store_true", help="enable ACPKI"
    )
    args = parser.parse_args()

    soc = EBAZ4205(acpki=args.acpki)
    soc.finalize()

    if args.r is not None:
        write_csr_file(soc, args.r)
    if args.m is not None:
        write_mem_file(soc, args.m)
    if args.c is not None:
        write_rustc_cfg_file(soc, args.c)
    if args.g is not None:
        soc.build(build_dir=args.g)


if __name__ == "__main__":
    main()
