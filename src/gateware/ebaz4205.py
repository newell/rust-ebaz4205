#!/usr/bin/env python

import argparse
from operator import itemgetter
from toolz.curried import *  # noqa

from migen import *

# from migen.build.platforms import ebaz4205
from migen.build.generic_platform import Pins, Subsignal, IOStandard, Misc
from migen_axi.integration.soc_core import SoCCore
from misoc.interconnect.csr import *

# from migen.build.generic_platform import *
from migen.build.xilinx import XilinxPlatform


_io = [
    # Green and Red LEDs
    ("user_led", 0, Pins("W13"), IOStandard("LVCMOS33")),
    ("user_led", 1, Pins("W14"), IOStandard("LVCMOS33")),
    # Push Buttons
    ("user_btn", 0, Pins("A17"), IOStandard("LVCMOS33")),
    ("user_btn", 1, Pins("A14"), IOStandard("LVCMOS33")),
    # UART
    (
        "serial",
        0,
        Subsignal("tx", Pins("A16")),
        Subsignal("rx", Pins("F15")),
        IOStandard("LVCMOS33"),
    ),
    # SD Card
    (
        "sdcard",
        0,
        Subsignal("detect", Pins("A12"), Misc("PULLUP True")),
        Subsignal("data", Pins("E12 A9 F13 B15")),
        Subsignal("cmd", Pins("C17")),
        Subsignal("clk", Pins("D14")),
        Subsignal("cd", Pins("B15")),
        IOStandard("LVCMOS33"),
        Misc("SLEW=FAST"),
    ),
    # NAND Flash
    (
        "nandflash",
        0,
        Subsignal("nand_data", Pins("A6 A5 B7 E8 B5 E9 C6 D9")),
        Subsignal("nand_ce", Pins("E6")),
        Subsignal("nand_re", Pins("D5")),
        Subsignal("nand_we", Pins("D6")),
        Subsignal("nand_ale", Pins("B8")),
        Subsignal("nand_cle", Pins("D8")),
        Subsignal("nand_rb", Pins("C5")),
        IOStandard("LVCMOS33"),
    ),
    # ETH PHY
    (
        "gmii",
        0,
        Subsignal("rxd", Pins("Y16 V16 V17 Y17")),
        Subsignal("txd", Pins("W18 Y18 V18 Y19")),
        Subsignal("rx_clk", Pins("U14")),
        Subsignal("tx_clk", Pins("U15")),
        Subsignal("rx_dv", Pins("W16")),
        Subsignal("tx_en", Pins("W19")),
        IOStandard("LVCMOS33"),
    ),
    (
        "mdio",
        0,
        Subsignal("mdio", Pins("Y14")),
        Subsignal("mdc", Pins("W15")),
        IOStandard("LVCMOS33"),
    ),
]


# DATA1-3 2x10 2.0mm Pitch
# J3 and J5 1x4 2.54mm Pitch
_connectors = [
    (
        "DATA1",
        {
            "DATA1-5": "A20",
            "DATA1-6": "H16",
            "DATA1-7": "B19",
            "DATA1-8": "B20",
            "DATA1-9": "C20",
            "DATA1-11": "H17",
            "DATA1-13": "D20",
            "DATA1-14": "D18",
            "DATA1-15": "H18",
            "DATA1-16": "D19",
            "DATA1-17": "F20",
            "DATA1-18": "E19",
            "DATA1-19": "F19",
            "DATA1-20": "K17",
        },
    ),
    (
        "DATA2",
        {
            "DATA2-5": "G20",
            "DATA2-6": "J18",
            "DATA2-7": "G19",
            "DATA2-8": "H20",
            "DATA2-9": "J19",
            "DATA2-11": "K18",
            "DATA2-13": "K19",
            "DATA2-14": "J20",
            "DATA2-15": "L16",
            "DATA2-16": "L19",
            "DATA2-17": "M18",
            "DATA2-18": "L20",
            "DATA2-19": "M20",
            "DATA2-20": "L17",
        },
    ),
    (
        "DATA3",
        {
            "DATA3-5": "M19",
            "DATA3-6": "N20",
            "DATA3-7": "P18",
            "DATA3-8": "M17",
            "DATA3-9": "N17",
            "DATA3-11": "P20",
            "DATA3-13": "R18",
            "DATA3-14": "R19",
            "DATA3-15": "P19",
            "DATA3-16": "T20",
            "DATA3-17": "U20",
            "DATA3-18": "T19",
            "DATA3-19": "V20",
            "DATA3-20": "U19",
        },
    ),
    (
        "J3",
        {
            "J3-4-TX": "U12",
            "J3-3-RX": "V13",
        },
        "J5",
        {
            "J5-4-TX": "V12",
            "J5-3-RX": "V15",
        },
    ),
]


class Platform(XilinxPlatform):
    def __init__(self):
        XilinxPlatform.__init__(
            self, "xc7z010-clg400-1", _io, _connectors, toolchain="vivado"
        )


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

        # platform = ebaz4205.Platform()
        platform = Platform()
        platform.toolchain.bitstream_commands.extend(
            [
                "set_property BITSTREAM.GENERAL.COMPRESS True [current_design]",
            ]
        )
        platform.add_extension(_ps)
        platform.add_extension(_ddr)

        # FCLK is tied to pin U18
        platform.add_extension(
            [
                ("fclk", 0, Pins("U18"), IOStandard("LVCMOS33")),
            ]
        )

        gmii = platform.request("gmii")

        platform.add_period_constraint(gmii.rx_clk, 10)
        platform.add_period_constraint(gmii.tx_clk, 10)
        platform.add_platform_command(
            "set_property CLOCK_DEDICATED_ROUTE FALSE [get_nets gmii_tx_clk_IBUF]"
        )

        ident = self.__class__.__name__
        SoCCore.__init__(
            self,
            platform=platform,
            csr_data_width=32,
            ident=ident,
        )
        platform.add_period_constraint(self.ps7.cd_sys.clk, 10)

        self.comb += [
            # Inputs
            self.ps7.enet0.enet.gmii.tx_clk.eq(gmii.tx_clk),
            self.ps7.enet0.enet.gmii.rx_clk.eq(gmii.rx_clk),
            self.ps7.enet0.enet.gmii.rx_dv.eq(gmii.rx_dv),
            self.ps7.enet0.enet.gmii.rxd.eq(gmii.rxd),
            # Outputs
            gmii.tx_en.eq(self.ps7.enet0.enet.gmii.tx_en),
            gmii.txd.eq(self.ps7.enet0.enet.gmii.txd),
        ]

        # LEDs
        user_led_0 = platform.request("user_led", 0)
        user_led_1 = platform.request("user_led", 1)
        self.comb += [
            user_led_0.eq(self.ps7.gpio.o[0]),
            user_led_1.eq(self.ps7.gpio.o[1]),
        ]

        # FCLK
        fclk = platform.request("fclk")
        self.comb += fclk.eq(self.ps7.fclk.clk[0])

        # MDIO/MDC
        mdio = platform.request("mdio")
        self.comb += [
            mdio.mdc.eq(self.ps7.enet0.enet.mdio.mdc),
        ]
        self.specials += Instance(
            "IOBUF",
            i_I=self.ps7.enet0.enet.mdio.o,
            io_IO=mdio.mdio,
            o_O=self.ps7.enet0.enet.mdio.i,
            i_T=self.ps7.enet0.enet.mdio.t_n,
        )


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

    soc = EBAZ4205()  # acpki=args.acpki)
    soc.finalize()

    # if args.r is not None:
    #     write_csr_file(soc, args.r)
    # if args.m is not None:
    #     write_mem_file(soc, args.m)
    # if args.c is not None:
    #     write_rustc_cfg_file(soc, args.c)
    if args.g is not None:
        soc.build(build_dir=args.g)


if __name__ == "__main__":
    main()
