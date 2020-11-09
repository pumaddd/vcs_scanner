#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Gsm Scanner
# Generated: Fri Mar 13 15:57:15 2020
##################################################

from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from grgsm import arfcn
from math import pi
from optparse import OptionParser
from app import config
from app import signal_handler
import time
import grgsm
import math
import logging
import tabs

NUMBER_THREAD = 3


class auto_file_scanner(gr.top_block):

    def __init__(self, arfcn=[], offset=0, osr=2, flag=[]):
        gr.top_block.__init__(self, "Gsm Auto File Scanner")

        ##################################################
        # Parameters
        ##################################################
        self.offset = int(offset)
        self.osr = osr
        self.arfcn = []
        self.flag = []
        self.gsm_receiver = {}
        self.gsm_file_source = {}
        self.gsm_controlled_rotator_cc = {}
        self.gsm_control_decimator = {}
        self.gsm_control_channels_decoder = {}
        self.gsm_bcch_ccch_demapper = {}
        self.control_arb_resampler_ccf = {}
        self.blocks_throttle = {}
        self.burst_timeslot_filter = {}
        number_arfcn_per_list = int(len(arfcn) / NUMBER_THREAD)
        for i in range(NUMBER_THREAD):
            _arfcn = arfcn[number_arfcn_per_list * i:number_arfcn_per_list * (i + 1)]
            _flag = flag[number_arfcn_per_list * i:number_arfcn_per_list * (i + 1)]
            if i == (NUMBER_THREAD - 1):
                _arfcn = arfcn[number_arfcn_per_list * i:]
                _flag = flag[number_arfcn_per_list * i:]
            #_arfcn = arfcn
            #_flag = flag
            self.arfcn.append(_arfcn)
            self.flag.append(_flag)



        print("[INFO] list arfcn {}".format(self.arfcn))
        ##################################################
        # Blocks
        ##################################################
        self.gsm_extract_system_info = grgsm.extract_system_info()
        # self.exit_channel = grgsm.exit_channel(NUMBER_THREAD)
        for i in range(NUMBER_THREAD):
            print ("capture_round ----------------------------------------{}".format(config.capture_round))
            self.gsm_receiver[i] = grgsm.receiver(osr, ([0]), ([]), 0, 0, False)
            self.gsm_file_source[i] = grgsm.file_source(gr.sizeof_gr_complex * 1, self.offset, self.arfcn[i],
                                                        self.flag[i],
                                                        index=config.capture_round)
            self.gsm_controlled_rotator_cc[i] = grgsm.controlled_rotator_cc(0)
            self.gsm_control_decimator[i] = grgsm.control_decimator(
                1,
                (firdes.low_pass(1, 5e6, 100e3, 5e3, firdes.WIN_BLACKMAN_HARRIS, 6.76)),
                0,
                100,
                True,
                True)
            self.gsm_control_decimator[i].declare_sample_delay(0)
            self.gsm_control_channels_decoder[i] = grgsm.control_channels_decoder()
            self.gsm_bcch_ccch_demapper[i] = grgsm.gsm_bcch_ccch_demapper(timeslot_nr=0)
            self.control_arb_resampler_ccf[i] = grgsm.arb_resampler_ccf(0.5, taps=None, flt_size=32)
            self.control_arb_resampler_ccf[i].declare_sample_delay(0)
            self.blocks_throttle[i] = blocks.throttle(gr.sizeof_gr_complex * 1, 5e6, False)
            self.burst_timeslot_filter[i] = grgsm.burst_timeslot_filter(0)
            ##################################################
            # Connections
            ##################################################
            self.msg_connect((self.gsm_bcch_ccch_demapper[i], 'bursts'),
                             (self.gsm_control_channels_decoder[i], 'bursts'))
            self.msg_connect((self.gsm_control_channels_decoder[i], 'msgs'), (self.gsm_extract_system_info, 'msgs'))
            self.msg_connect((self.gsm_receiver[i], 'C0'), (self.gsm_bcch_ccch_demapper[i], 'bursts'))
            self.msg_connect((self.gsm_receiver[i], 'message'), (self.gsm_file_source[i], 'message_in'))
            # self.msg_connect((self.gsm_file_source[i], 'message_out'), (self.exit_channel, 'msg_in'))
            self.msg_connect((self.gsm_receiver[i], 'C0'), (self.burst_timeslot_filter[i], 'in'))
            self.msg_connect((self.burst_timeslot_filter[i], 'out'), (self.gsm_extract_system_info, 'bursts'))
            self.connect((self.blocks_throttle[i], 0), (self.gsm_controlled_rotator_cc[i], 0))
            self.connect((self.control_arb_resampler_ccf[i], 0), (self.gsm_receiver[i], 0))
            self.connect((self.gsm_control_decimator[i], 0), (self.control_arb_resampler_ccf[i], 0))
            self.connect((self.gsm_controlled_rotator_cc[i], 0), (self.gsm_control_decimator[i], 0))
            self.connect((self.gsm_file_source[i], 0), (self.blocks_throttle[i], 0))
        # self.blocks_null_source_0 = blocks.null_source(gr.sizeof_gr_complex * 1)
        # self.connect((self.blocks_null_source_0, 0), (self.exit_channel, 0))

    def get_offset(self):
        return self.offset

    def set_offset(self, offset):
        self.offset = offset

    def get_osr(self):
        return self.osr

    def set_osr(self, osr):
        self.osr = osr

    def set_search_fail_callback(self, callback):
        pass

    def set_gain(self, gain):
        pass

    def get_process_items(self):
        sample = self.gsm_file_source[0].nitems_written(0)
        # logging.error("[AUTO SOURCE]get process sample from receiver {}".format(sample))
        return sample

    def get_real_offset(self):
        offset = self.gsm_file_source[0].get_real_offset()
        return offset

    def set_max_burst(self, max_burst):
        for i in range(NUMBER_THREAD):
            self.gsm_receiver[i].set_max_burst(max_burst)

    def set_offset(self, sample_offset):
        for i in range(NUMBER_THREAD):
            self.gsm_file_source[i].reset_file_source(arfcn=self.arfcn[i], flag=self.flag[i],
                                                      sample_offset=int(sample_offset))

    def get_list_arfcn(self):
        list_arfcn = ()
        for i in range(NUMBER_THREAD):
            list_arfcn = list_arfcn + self.gsm_receiver[i].get_list_arfcn()
        return list_arfcn

    def get_stop_offset(self):
        stop_offset = []
        for i in range(NUMBER_THREAD):
            _stop_offset = self.gsm_file_source[i].get_sample_offset()
            stop_offset.append(_stop_offset)
        return max(stop_offset)

    def destroy(self):
        print("[AUTO SOURCE]call destroy auto filesource")
        self.disconnect_all()
        for i in range(NUMBER_THREAD):
            #del self.gsm_file_source[i]
            del self.gsm_control_decimator[i]
            del self.control_arb_resampler_ccf[i]
            del self.blocks_throttle[i]
