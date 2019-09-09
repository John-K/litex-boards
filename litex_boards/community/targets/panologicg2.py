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
    def __init0__(self, platform, clk_freq):
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
        # TODO: can this be 4*clk_freq?
        # per https://www.xilinx.com/support/documentation/user_guides/ug388.pdf ddr clk should be 2x desired
        # clock speed for DDR
        pll.create_clkout(self.cd_sdram_half, 2*clk_freq)
        pll.create_clkout(self.cd_sdram_full_wr, clk_freq)
        #pll.create_clkout(self.cd_sdram_full_rd)

        self.comb += [ self.cd_sdram_full_rd.clk.eq(self.cd_sdram_full_wr.clk) ]

        clk = platform.request("ddram_clock")
        self.specials += Instance("ODDR2",
            p_DDR_ALIGNMENT="NONE",
            p_INIT=0, p_SRTYPE="SYNC",
            i_D0=1, i_D1=0, i_S=0, i_R=0, i_CE=1,
            i_C0=self.cd_sdram_half.clk, i_C1=~self.cd_sdram_half.clk,
            o_Q=clk.p)

        self.specials += Instance("ODDR2",
            p_DDR_ALIGNMENT="NONE",
            p_INIT=0, p_SRTYPE="SYNC",
            i_D0=0, i_D1=1, i_S=0, i_R=0, i_CE=1,
            i_C0=self.cd_sdram_half.clk, i_C1=~self.cd_sdram_half.clk,
            o_Q=clk.n)

        # alternate method?
        # see https://github.com/Nancy-Chauhan/Crop/blob/d981b16753a2813c2fc80ad4e6b91568c45a44ce/targets/galatea/base.py
        #self.specials += Instance("OBUFDS", i_I=output_clk, o_O=clk.p, o_OB=clk.n)
    def __init__(self, platform, clk_freq):
        # Clock domains for the system (soft CPU and related components run at).
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_sys2x = ClockDomain()
        # Clock domains for the DDR interface.
        self.clock_domains.cd_sdram_half = ClockDomain()
        self.clock_domains.cd_sdram_full_wr = ClockDomain()
        self.clock_domains.cd_sdram_full_rd = ClockDomain()

        # Input 125MHz clock
        f0 = 125e6
        clk125 = platform.request("clk125")
        clk125a = Signal()
        # Input 125Mhz clock (buffered)
        self.specials += Instance("IBUFG", i_I=clk125, o_O=clk125a)
        clk125b = Signal()
        self.specials += Instance(
            "BUFIO2", p_DIVIDE=1,
            p_DIVIDE_BYPASS="TRUE", p_I_INVERT="FALSE",
            i_I=clk125a, o_DIVCLK=clk125b)

        f = Fraction(int(clk_freq), int(f0))
        n, m = f.denominator, f.numerator
        assert f0/n*m == clk_freq
        p = 8

    # Unbuffered output signals from the PLL. They need to be buffered
        # before feeding into the fabric.
        unbuf_sdram_full = Signal()
        unbuf_sdram_half_a = Signal()
        unbuf_sdram_half_b = Signal()
        unbuf_encoder = Signal()
        unbuf_sys = Signal()
        unbuf_sys_unused = Signal()

    # PLL signals
        pll_lckd = Signal()
        pll_fb = Signal()
        self.specials.pll = Instance(
            "PLL_ADV",
            name="crg_pll_adv",
            p_SIM_DEVICE="SPARTAN6", p_BANDWIDTH="OPTIMIZED", p_COMPENSATION="INTERNAL",
            p_REF_JITTER=.01,
            i_DADDR=0, i_DCLK=0, i_DEN=0, i_DI=0, i_DWE=0, i_RST=0, i_REL=0,
            p_DIVCLK_DIVIDE=1,
            # Input Clocks (125MHz)
            i_CLKIN1=clk125b,
            p_CLKIN1_PERIOD=1e9/f0,
            i_CLKIN2=0,
            p_CLKIN2_PERIOD=0.,
            i_CLKINSEL=1,
            # Feedback
            i_CLKFBIN=pll_fb, o_CLKFBOUT=pll_fb, o_LOCKED=pll_lckd,
            p_CLK_FEEDBACK="CLKFBOUT",
            p_CLKFBOUT_MULT=m*p//n, p_CLKFBOUT_PHASE=0.,
            # (400MHz) ddr3 wr/rd full clock
            o_CLKOUT0=unbuf_sdram_full, p_CLKOUT0_DUTY_CYCLE=.5,
            p_CLKOUT0_PHASE=0., p_CLKOUT0_DIVIDE=p//8,
            # ( 66MHz) encoder
            o_CLKOUT1=unbuf_encoder, p_CLKOUT1_DUTY_CYCLE=.5,
            p_CLKOUT1_PHASE=0., p_CLKOUT1_DIVIDE=6,
            # (200MHz) sdram_half - ddr3 dqs adr ctrl off-chip
            o_CLKOUT2=unbuf_sdram_half_a, p_CLKOUT2_DUTY_CYCLE=.5,
            p_CLKOUT2_PHASE=230., p_CLKOUT2_DIVIDE=p//4,
            # (200MHz) off-chip ddr - ddr3 half clock
            o_CLKOUT3=unbuf_sdram_half_b, p_CLKOUT3_DUTY_CYCLE=.5,
            p_CLKOUT3_PHASE=210., p_CLKOUT3_DIVIDE=p//4,
            # (100MHz) sys2x - 2x system clock
            o_CLKOUT4=unbuf_sys, p_CLKOUT4_DUTY_CYCLE=.5,
            p_CLKOUT4_PHASE=0., p_CLKOUT4_DIVIDE=p//2,
            # ( 50MHz) periph / sys - system clock
            o_CLKOUT5=unbuf_sys_unused, p_CLKOUT5_DUTY_CYCLE=.5,
            p_CLKOUT5_PHASE=0., p_CLKOUT5_DIVIDE=p//1,
        )

    # SDRAM clocks
        # ------------------------------------------------------------------------------
        self.clk4x_wr_strb = Signal()
        self.clk4x_rd_strb = Signal()

        # sdram_full
        self.specials += Instance("BUFPLL", name="sdram_full_bufpll",
                                  p_DIVIDE=2, # maybe 4?
                                  i_PLLIN=unbuf_sdram_full, i_GCLK=self.cd_sys.clk,
                                  i_LOCKED=pll_lckd,
                                  o_IOCLK=self.cd_sdram_full_wr.clk,
                                  o_SERDESSTROBE=self.clk4x_wr_strb)
        self.comb += [
            self.cd_sdram_full_rd.clk.eq(self.cd_sdram_full_wr.clk),
            self.clk4x_rd_strb.eq(self.clk4x_wr_strb),
        ]
        # sdram_half
        self.specials += Instance("BUFG", name="sdram_half_a_bufpll", i_I=unbuf_sdram_half_a, o_O=self.cd_sdram_half.clk)
        clk_sdram_half_shifted = Signal()
        self.specials += Instance("BUFG", name="sdram_half_b_bufpll", i_I=unbuf_sdram_half_b, o_O=clk_sdram_half_shifted)

        output_clk = Signal()
        clk = platform.request("ddram_clock")
        self.specials += Instance("ODDR2", p_DDR_ALIGNMENT="NONE",
                                  p_INIT=0, p_SRTYPE="SYNC",
                                  i_D0=1, i_D1=0, i_S=0, i_R=0, i_CE=1,
                                  i_C0=clk_sdram_half_shifted,
                                  i_C1=~clk_sdram_half_shifted,
                                  o_Q=output_clk)
        self.specials += Instance("OBUFDS", i_I=output_clk, o_O=clk.p, o_OB=clk.n)
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
        #                  integrated_main_ram_size=0x8000,
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
        #if (False):
        if (True):
            sdram_module = MT47H32M16(sys_clk_freq, "1:2")
            self.submodules.ddrphy = s6ddrphy.S6HalfRateDDRPHY(platform.request("ddram"),
                                                           sdram_module.memtype,
                                                           rd_bitslip=1,
                                                           wr_bitslip=3,
                                                           dqs_ddr_alignment="")
            self.add_csr("ddrphy")
            self.register_sdram(self.ddrphy,
                            sdram_module.geom_settings,
                            sdram_module.timing_settings)


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
