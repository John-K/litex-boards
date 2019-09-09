#!/usr/bin/env python3

# This file is Copyright (c) 2013-2014 Sebastien Bourdeauducq <sb@m-labs.hk>
# This file is Copyright (c) 2014-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# This file is Copyright (c) 2014 Yann Sionneau <ys@m-labs.hk>
# License: BSD

import argparse
from fractions import Fraction

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer


from litex_boards.platforms import panologicg2

from litex.soc.cores.gpio import GPIOOut
from litex.soc.cores.clock import *
from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *
from litex.soc.integration.soc_core import csr_map_update

from litedram.modules import MT47H32M16
from litedram.phy import s6ddrphy

# CRG ----------------------------------------------------------------------------------------------

class _CRG(Module):
    def __init__(self, platform, clk_freq):
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_sys_ps = ClockDomain()
        self.clock_domains.cd_sdram_half = ClockDomain()
        self.clock_domains.cd_sdram_full_wr = ClockDomain()
        self.clock_domains.cd_sdram_full_rd = ClockDomain()

        # # #

        self.cd_sys.clk.attr.add("keep")
        self.cd_sys_ps.clk.attr.add("keep")

        self.submodules.pll = pll = S6PLL(speedgrade=-2)
        pll.register_clkin(platform.request("clk125"), 125e6)
        pll.create_clkout(self.cd_sys, clk_freq)
        pll.create_clkout(self.cd_sys_ps, clk_freq, phase=270)

        # DDR Config
#        clk = platform.request("ddram_clock")
#        self.specials += Instance("ODDR2",
#            p_DDR_ALIGNMENT="NONE",
#            p_INIT=0, p_SRTYPE="SYNC",
#            i_D0=1, i_D1=0, i_S=0, i_R=0, i_CE=1,
#            i_C0=self.cd_sys.clk, i_C1=~self.cd_sys.clk,
#            o_Q=clk.p)

#        self.specials += Instance("ODDR2",
#            p_DDR_ALIGNMENT="NONE",
#            p_INIT=0, p_SRTYPE="SYNC",
#            i_D0=0, i_D1=1, i_S=0, i_R=0, i_CE=1,
#            i_C0=self.cd_sys.clk, i_C1=~self.cd_sys.clk,
#            o_Q=clk.n)

# BaseSoC ------------------------------------------------------------------------------------------

class BaseSoC(SoCSDRAM):
    csr_peripherals = ["leds"]
    csr_map_update(SoCSDRAM.csr_map, csr_peripherals)


    def __init__(self, sys_clk_freq=int(100e6), **kwargs):
        assert sys_clk_freq == int(100e6)
        platform = panologicg2.Platform()
        SoCSDRAM.__init__(self, platform, clk_freq=sys_clk_freq,
                          ident="VexRiscv on Panologic G2", ident_version=True,
                          integrated_rom_size=0x8000,
                          integrated_main_ram_size=0x8000,
                          uart_baudrate=115200,
                          **kwargs)

        self.submodules.crg = _CRG(platform, sys_clk_freq)

        # LED support
        leds = Signal(3)
        self.submodules.leds = GPIOOut(leds)
        self.comb += [
                platform.request("user_led", 0).eq(leds[0]),
                platform.request("user_led", 1).eq(leds[1]),
                platform.request("user_led", 2).eq(leds[2])
        ]

        # enable 125MHz clock
        self.comb += [ platform.request("eth").rst_n.eq(1) ]

        # sdram
#        sdram_module = MT47H32M16(sys_clk_freq, "1:2")
#        self.submodules.ddrphy = s6ddrphy.S6HalfRateDDRPHY(platform.request("ddram"),
#                                                           sdram_module.memtype,
#                                                           rd_bitslip=1,
#                                                           wr_bitslip=3,
#                                                           dqs_ddr_alignment="")
#        self.add_csr("ddrphy")
#        self.register_sdram(self.ddrphy,
#                            sdram_module.geom_settings,
#                            sdram_module.timing_settings)

#        if not self.integrated_main_ram_size:
 #           self.submodules.sdrphy = GENSDRPHY(platform.request("sdram"))
 #           sdram_module = AS4C16M16(sys_clk_freq, "1:1")
 #           self.register_sdram(self.sdrphy,
 #                               sdram_module.geom_settings,
 #                               sdram_module.timing_settings)

# Build --------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="LiteX SoC on PanoLogic G2")
    builder_args(parser)
    soc_sdram_args(parser)
    args = parser.parse_args()

    soc = BaseSoC(**soc_sdram_argdict(args))
    builder = Builder(soc, **builder_argdict(args))
    builder.build()


if __name__ == "__main__":
    main()
