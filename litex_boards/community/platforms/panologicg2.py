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

    # 125 MHz System Clock (25 MHz when GMII chip is in reset)
    # This net is driven by the GMII chip.
    ("clk125", 0, Pins("Y13"), IOStandard("LVCMOS33")),

    # Re-use DVI DDC pins for UART
    ("serial", 0,
        Subsignal("tx", Pins("C14"), IOStandard("LVCMOS33")),  # DVI DDC SCL
        Subsignal("rx", Pins("C17"), IOStandard("LVCMOS33"))   # DVI DDC SDA
    ),

    # Micron M25P128 SPI Serial Flash
    # 128Mbit / 32MiB @ 54MHz
    # Datasheet https://www.micron.com/~/media/documents/products/data-sheet/nor-flash/serial-nor/m25p/m25p_128.pdf
    # TODO: verify this!
    ("spi_flash", 0,
        Subsignal("cs_n", Pins("T5")),
        Subsignal("clk", Pins("Y21")),
        Subsignal("mosi", Pins("AB20")),
        Subsignal("miso", Pins("AA20")),
        IOStandard("LVCMOS33"),
    ),

    ("ddram_clock", 0,
        Subsignal("p", Pins("H20")),
        Subsignal("n", Pins("J19")),
        IOStandard("SSTL18_I")
    ),

    # Micron MT47H32M16HR-25E:G (D9LPX)
    # Datasheet https://www.micron.com/~/media/Documents/Products/Data%20Sheet/DRAM/DDR2/512MbDDR2.pdf
    # DDR2-800, CL 5
    # Density 512Mb
    # Width x16
    # Depth 32Mb
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
    ),

    # 10/100/1000 Ethernet PHY
    # Marvell 88E1119R-NNW2
    # GMII / MII
    # Uses e1000phy driver

    # unsure what ref_clk should be here
    #("eth_ref_clk", 0, Pins("AA12"), IOStandard("LVCMOS33")),
    ("eth_clocks", 0,
        Subsignal("tx", Pins("Y11")),
        Subsignal("gtx", Pins("AA12")),
        Subsignal("rx", Pins("AB11")),
        IOStandard("LVCMOS33"),
    ),
    ("eth", 0,
        Subsignal("rst_n", Pins("R11")),
        Subsignal("mdio", Pins("AA2")),
        Subsignal("mdc", Pins("AB6")),
        Subsignal("rx_dv", Pins("Y7")),
        Subsignal("rx_er", Pins("Y8")),
        Subsignal("rx_data", Pins("Y3 Y4 R9 R7 V9 R8 U9 Y9")),
        Subsignal("tx_en", Pins("AA8")),
        #Subsignal("tx_er", Pins("AB8")), # Per Pano.ucf, this is NC
        Subsignal("tx_data", Pins("AB2 AB3 AB4 AB7 AB9 AB10 T7 Y10")),
        Subsignal("col", Pins("V7")),
        Subsignal("crs", Pins("W4")),
        Subsignal("link_up_n", Pins("AA4")), # likely unused anywhere, not sure what it does
        IOStandard("LVCMOS33"),
    ),

    # Video Out
    # Two Chrontel CH7301C ICs
    # Datasheet:
    #    http://www.chrontel.com.cn/upFiles/images/US/By%20Product/CH7301C/Datasheets/CH7301C%20Datasheet%20rev2.1.pdf
    # Register App Note: AN41
    #    http://www.chrontel.com/upFiles/images/US/By%20Product/CH7301C/Application%20Notes/an41.pdf

    # micro HDMI OUT
    # I2C Address 0xEA (AS Pin = 1)
    ("dvi-shared", 0,
        Subsignal("scl", Pins("E8")),
        Subsignal("sda", Pins("D9")),
        IOStandard("LVCMOS33"),
    ),
    ("hdmi", 0,
        Subsignal("rst_n", Pins("W18")),
        Subsignal("clk_p", Pins("T17")),
        Subsignal("data", Pins("T18 U16 V17 V19 V18 W17 Y17 Y15 Y18 Y19 AB21 T17")),
        Subsignal("vsync", Pins("T16")),
        Subsignal("hsync", Pins("AB15")),
        Subsignal("data_en", Pins("AB16")),
        Subsignal("ddc_scl", Pins("AA21")),
        Subsignal("ddc_sda", Pins("AB19")),
        Subsignal("hotplug_n", Pins("AB18")),
        IOStandard("LVCMOS33"),
        Misc("SLEW=FAST DRIVE=24")
    ),

    # DVI OUT
    # I2C Address 0xEC (AS Pin = 0)
    ("dvi", 0,
        Subsignal("rst_n", Pins("C15")),
        Subsignal("clk_p", Pins("E14")),
        Subsignal("clk_n", Pins("F15")),
        Subsignal("data", Pins("D17 A14 A15 A16 A17 A18 D14 B14 B16 B18 E16 D15")),
        Subsignal("vsync", Pins("C16")),
        Subsignal("hsync", Pins("F12")),
        Subsignal("data_en", Pins("F14")),
        #Subsignal("ddc_scl", Pins("C14")), # commented out for use as UART
        #Subsignal("ddc_sda", Pins("C17")), # commented out for use as UART
        Subsignal("hotplug_n", Pins("D13")),
        IOStandard("LVCMOS33"),
        Misc("SLEW=FAST DRIVE=24")
    ),

]

# Connectors ---------------------------------------------------------------------------------------

_connectors = [
]

# Platform -----------------------------------------------------------------------------------------

class Platform(XilinxPlatform):
    default_clk_name = "clk125"
    default_clk_period = 1e9/125e6

    def __init__(self, device="xc6slx100"):
        XilinxPlatform.__init__(self, device+"-2-fgg484", _io, _connectors, toolchain="ise")

    def create_programmer(self):
        return FpgaProg()
