#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Gr-gsm Livemon
# Author: Piotr Krysik
# Description: Interactive monitor of a single C0 channel with analysis performed by Wireshark (command to run wireshark: sudo wireshark -k -f udp -Y gsmtap -i lo)
# Generated: Thu Oct  3 17:08:54 2019
##################################################

from app.modules_manager import sdr_source
from app.signal_handler import signal_block
from app import gsm_band
from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import qtgui
from gnuradio.eng_option import eng_option
from gnuradio.filter import pfb
from gnuradio.filter import firdes
from grgsm import arfcn
from math import pi
from optparse import OptionParser
import grgsm
import pmt
import sip
import sys


class grgsm_livemon_headless(gr.top_block):

    def __init__(self, args="", collector="localhost", collectorport="4929", fc=9466e5, sample_offset=0, gain=30, osr=4, ppm=0, samp_rate=3e6, serverport="4929", shiftoff=0, device="FILE_DEVICE", cb=None):

        gr.top_block.__init__(self, "Gr-gsm Livemon")
        ##################################################
        # Parameters
        ##################################################
        self.args = args
        self.collector = collector
        self.collectorport = collectorport
        self.fc = fc
        self.gain = gain
        self.osr = osr
        self.ppm = ppm
        self.serverport = serverport
        self.shiftoff = shiftoff
        self.device = device

        self.cb = cb

        ##################################################
        # Variables
        ##################################################
        self.ppm_slider = ppm_slider = ppm
        self.gain_slider = gain_slider = gain
        self.fc_slider = fc_slider = fc
        self.gsm_symb_rate = gsm_symb_rate = 1625000.0/6.0
        self.samp_rate_out = samp_rate_out = osr*gsm_symb_rate
        self.receiver_offset = sample_offset
        self.samp_rate = gsm_band.arfcn.get_fc_bandwidth(fc)
        self.file_offset = self.receiver_offset * self.samp_rate / (1625000.0 / 6.0 * self.osr)

        ##################################################
        # Blocks
        ##################################################
        self.sdr_source_0 = sdr_source(osr=osr, samp_rate=self.samp_rate, device=device, fc=fc) 
        self.pfb_decimator_ccf_0 = pfb.decimator_ccf(3,
        	  (firdes.low_pass(1, self.samp_rate,125e3,5e3,firdes.WIN_HAMMING,6.76)),
        	  0, 100, True, True)
        self.pfb_decimator_ccf_0.declare_sample_delay(0)
               
        self.pfb_arb_resampler_xxx_0 = pfb.arb_resampler_ccf(samp_rate_out/(self.samp_rate/3),
                taps=None, flt_size=10)
        self.pfb_arb_resampler_xxx_0.declare_sample_delay(0)

        self.gsm_receiver_0 = grgsm.receiver(osr=osr, cell_allocation=([arfcn.downlink2arfcn(fc_slider)]), seq_nums=([]), fc=fc, sample_offset=self.receiver_offset, process_uplink=False)
        self.gsm_control_channels_decoder_0 = grgsm.control_channels_decoder()
        self.gsm_bcch_ccch_demapper_0 = grgsm.gsm_bcch_ccch_demapper(
            timeslot_nr=0,
        )
        self.signal_handler_blk = signal_block(callback_found_fcch=self.cb)
        # self.blocks_socket_pdu_0_1 = blocks.socket_pdu("UDP_CLIENT", collector, collectorport, 1500, False)
        # self.blocks_socket_pdu_0_0 = blocks.socket_pdu("UDP_SERVER", "127.0.0.1", serverport, 10000, False)
        self.blocks_message_debug_0 = blocks.message_debug()
        self.gsm_extract_system_info = grgsm.extract_system_info()

        print("[LIVEMON HEADLESS]Initual channel scanner with start offset at {}".format(self.receiver_offset))

        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.gsm_bcch_ccch_demapper_0, 'bursts'),(self.gsm_control_channels_decoder_0, 'bursts'))    
        # self.msg_connect((self.gsm_control_channels_decoder_0, 'msgs'), (self.blocks_socket_pdu_0_1, 'pdus'))
        self.msg_connect((self.gsm_receiver_0, 'message'), (self.signal_handler_blk, 'msg_in'))    
        #self.msg_connect((self.gsm_receiver_0, 'message'), (self.blocks_message_debug_0, 'print'))
        self.msg_connect((self.gsm_receiver_0, 'C0'), (self.gsm_bcch_ccch_demapper_0, 'bursts'))    
        self.connect((self.sdr_source_0, 0), (self.pfb_decimator_ccf_0, 0))    
        self.connect((self.pfb_arb_resampler_xxx_0, 0), (self.gsm_receiver_0, 0))    
        self.connect((self.pfb_decimator_ccf_0, 0), (self.pfb_arb_resampler_xxx_0, 0))
        self.msg_connect((self.gsm_control_channels_decoder_0, 'msgs'), (self.gsm_extract_system_info, 'msgs'))
        # if self.device == "FILE_DEVICE":
        #     self.msg_connect((self.sdr_source_0 , 'message_out'), (self.signal_handler_blk, 'msg_in'))    

        ##################################################
        # Dependent Variables
        ##################################################
        self.FC_BANDWIDTH_1800 = self.sdr_source_0.FC_BANDWIDTH_1800
        self.FC_BANDWIDTH_900 = self.sdr_source_0.FC_BANDWIDTH_900

        self.LOWPASS_900 = firdes.low_pass(1, self.FC_BANDWIDTH_900,125e3,5e3,firdes.WIN_HAMMING,6.76)
        self.LOWPASS_1800 = firdes.low_pass(1, self.FC_BANDWIDTH_1800,125e3,5e3,firdes.WIN_HAMMING,6.76)
        self.current_taps = self.LOWPASS_900

    def set_fc(self, fc, offset=0):
        self.current_offset = self.gsm_receiver_0.get_sample()
        if self.device == "FILE_DEVICE":
            # change sample rate and  bandwidth size acrort band
            # jump from GSM900 to DCS1800
            if arfcn.downlink2arfcn(self.fc) < 512 and arfcn.downlink2arfcn(fc) > 512:
                self.current_taps = self.LOWPASS_1800 
                self.set_samp_rate(self.FC_BANDWIDTH_1800)

            # jump from DCS1800 to GSM900
            elif arfcn.downlink2arfcn(self.fc) > 512 and arfcn.downlink2arfcn(fc) < 512:
                self.current_taps = self.LOWPASS_900 
                self.set_samp_rate(self.FC_BANDWIDTH_900)
        
        self.fc = fc
        self.signal_handler_blk.sync_fail_counter = 0
        self.file_offset = self.samp_rate * self.current_offset / self.samp_rate_out
        self.sdr_source_0.set_fc(self.fc, offset=self.file_offset)
        self.gsm_receiver_0.set_cell_allocation(([arfcn.downlink2arfcn(self.fc)]))
        self.gsm_receiver_0.set_fc_capture(self.fc)
        print("[GSM-LIVEMON jump to frequency {} at offset {} fucking sample rate {}]".format(self.fc, self.current_offset, self.samp_rate))

    def get_ppm(self):
        return self.gsm_receiver_0.get_ppm()

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.sdr_source_0.set_samp_rate(samp_rate)
        self.pfb_decimator_ccf_0.set_taps(taps = (self.current_taps))
        self.pfb_arb_resampler_xxx_0.set_rate(self.samp_rate_out/(samp_rate/3))

    def get_search_status(self):
        return self.gsm_receiver_0.get_current_channel_state()

    def set_found_fcch_callback(self, callback=None):
        self.signal_handler_blk.callback_found_fcch = callback

    def set_search_fail_callback(self, callback=None):
        self.signal_handler_blk.callback_search_fail = callback

    def get_offset(self):
        current_offset = self.gsm_receiver_0.get_sample()
        return current_offset

    def set_gain(self, gain):
        self.gain = gain
        self.sdr_source_0.set_gain(gain)
