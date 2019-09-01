# This file is Copyright (c) 2019 John Kelley <john@kelley.ca>
# Platform for Pano Logic G2 with Spartan6 LX100
# License: BSD

from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform
#from litex.build.xilinx.programmer import FpgaProg

# IOs ----------------------------------------------------------------------------------------------

_io = [
    ("user_led", 0, Pins("E12"), IOStandard("LVCMOS33")), # Red
    ("user_led", 1, Pins("H13"),  IOStandard("LVCMOS33")), # Blue
    ("user_led", 2, Pins("F13"),  IOStandard("LVCMOS33")), # Green

    ("user_sw", 0, Pins("H12"), IOStandard("LVCMOS33"), Misc("PULLUP")),

    ("clk25", 0, Pins("Y13"), IOStandard("LVCMOS33")),

    ("serial", 0,
        Subsignal("tx", Pins("C14"), IOStandard("LVCMOS33")),  # DVI DDC SCL
        Subsignal("rx", Pins("C17"), IOStandard("LVCMOS33"))   # DVI DDC SDA
    ),

    ("ddram_clock", 0,
        Subsignal("p", Pins("H20")),
        Subsignal("n", Pins("J19")),
        IOStandard("SSTL18_I")
    ),

    ("ddram", 0,
        Subsignal("a", Pins(
            "F21 F22 E22 G20 F20 K20 K19 E20",
            "C20 C22 G19 F19 D22"),
            IOStandard("SSTL18_I")),
        Subsignal("ba", Pins("J17 K17 H18"), IOStandard("SSTL18_I")),
        Subsignal("ras_n", Pins("H21"), IOStandard("SSTL18_I")),
        Subsignal("cas_n", Pins("H22"), IOStandard("SSTL18_I")),
        Subsignal("we_n", Pins("H19"), IOStandard("SSTL18_I")),
        Subsignal("dm", Pins("L19 M20"), IOStandard("SSTL18_I")),
        Subsignal("dq", Pins(
            "N20 N22 M21 M22 J20 J22 K21 K22",
            "P21 P22 R20 R22 U20 U22 V21 V22"),
            IOStandard("SSTL18_I")),
        Subsignal("dqs", Pins("L20 T21"), IOStandard("DIFF_SSTL18_I")),
        Subsignal("dqs_n", Pins("L22 T22"), IOStandard("DIFF_SSTL18_I")),
        Subsignal("cke", Pins("D21"), IOStandard("SSTL18_I")),
        Subsignal("odt", Pins("G22"), IOStandard("SSTL18_I")),
        Misc("SLEW=FAST")
    ),

    ("ddram_dual_rank", 0,
        Subsignal("a", Pins(
            "H2 H1 H5 K6 F3 K3 J4 H6",
            "E3 E1 G4 C1 D1"),
            IOStandard("SSTL18")),
        Subsignal("ba", Pins("G3 G1 F1"), IOStandard("SSTL18")),
        Subsignal("ras_n", Pins("K5"), IOStandard("SSTL18")),
        Subsignal("cas_n", Pins("K4"), IOStandard("SSTL18")),
        Subsignal("we_n", Pins("F2"), IOStandard("SSTL18")),
#        Subsignal("cs_n", Pins("U8"), IOStandard("SSTL135")),
        Subsignal("dm", Pins("L4 M3"), IOStandard("SSTL18")),
        Subsignal("dq", Pins(
            "N3 N1 M2 M1 J3 J1 K2 K1",
            "P2 P1 R3 R1 U3 U1 V2 V1"),
            IOStandard("SSTL18")),
#            Misc("IN_TERM=UNTUNED_SPLIT_40")),
        Subsignal("dqs_p", Pins("L3 T2"), IOStandard("DIFF_SSTL18")),
        Subsignal("dqs_n", Pins("L1 T1"), IOStandard("DIFF_SSTL18")),
        Subsignal("clk_p", Pins("H4"), IOStandard("DIFF_SSTL18")),
        Subsignal("clk_n", Pins("H3"), IOStandard("DIFF_SSTL18")),
        Subsignal("cke", Pins("D2"), IOStandard("SSTL18")),
        Subsignal("odt", Pins("J6"), IOStandard("SSTL18")),
#        Subsignal("reset_n", Pins("K6"), IOStandard("SSTL18")),
        Misc("SLEW=FAST")
     )
]

# Connectors ---------------------------------------------------------------------------------------

_connectors = [
]

# Platform -----------------------------------------------------------------------------------------

class Platform(XilinxPlatform):
    default_clk_name = "clk25"
    default_clk_period = 1e9/25e6

    def __init__(self, device="xc6slx100"):
        XilinxPlatform.__init__(self, device+"-2-fgg484", _io, _connectors, toolchain="ise")

    def create_programmer(self):
        return FpgaProg()
