#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Gr-gsm Livemon
# Author: Piotr Krysik
# Description: Interactive monitor of a single C0 channel with analysis performed by Wireshark (command to run wireshark: sudo wireshark -k -f udp -Y gsmtap -i lo)
# Generated: Thu Oct  3 17:08:54 2019
##################################################

#from app.modules.sources.file_source import source as sdr_source
from app.modules_manager import sdr_source
from app.signal_handler import signal_block
from PyQt4 import Qt
from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import qtgui
from gnuradio.eng_option import eng_option
from gnuradio.filter import pfb
from gnuradio.filter import firdes
from gnuradio.qtgui import Range, RangeWidget
from grgsm import arfcn
from math import pi
from optparse import OptionParser
import grgsm
import pmt
import sip
import sys


class grgsm_livemon(gr.top_block, Qt.QWidget):

    def __init__(self, args="", collector="localhost", collectorport="4929", fc=9466e5, sample_offset=0, gain=30, osr=4, ppm=0, samp_rate=3e6, serverport="4929", shiftoff=0, device="FILE_DEVICE"):
        gr.top_block.__init__(self, "Gr-gsm Livemon")
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Gr-gsm Livemon")
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except:
            pass
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "grgsm_livemon")
        self.restoreGeometry(self.settings.value("geometry").toByteArray())

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
        self.samp_rate = samp_rate
        self.serverport = serverport
        self.shiftoff = shiftoff
        self.device = device 

        ##################################################
        # Variables
        ##################################################
        self.ppm_slider = ppm_slider = ppm
        self.gain_slider = gain_slider = gain
        self.fc_slider = fc_slider = fc
        self.gsm_symb_rate = gsm_symb_rate = 1625000.0/6.0
        self.samp_rate_out = samp_rate_out = osr*gsm_symb_rate
        self.current_offset = sample_offset

        ##################################################
        # Blocks
        ##################################################
        self._fc_slider_range = Range(800e6, 1990e6, 1e5, fc, 100)
        self.sdr_source_0 = sdr_source(device=device, fc=fc, osr=osr, samp_rate=samp_rate)
        self.qtgui_sink_x_0 = qtgui.sink_c(
        	1024, #fftsize
        	firdes.WIN_BLACKMAN_hARRIS, #wintype
        	0, #fc
        	samp_rate, #bw
        	"", #name
        	True, #plotfreq
        	True, #plotwaterfall
        	True, #plottime
        	True, #plotconst
        )
        self.qtgui_sink_x_0.set_update_time(1.0/10)
        self._qtgui_sink_x_0_win = sip.wrapinstance(self.qtgui_sink_x_0.pyqwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_sink_x_0_win)
        
        self.qtgui_sink_x_0.enable_rf_freq(False)
        self._ppm_slider_range = Range(-150, 150, 0.1, ppm, 100)
        self._ppm_slider_win = RangeWidget(self._ppm_slider_range, self.set_ppm_slider, "PPM Offset", "counter", float)

        self.pfb_decimator_ccf_0 = pfb.decimator_ccf(3,
        	  (firdes.low_pass(1, samp_rate,125e3,5e3,firdes.WIN_HAMMING,6.76)),
        	  0, 100, True, True)

        self.pfb_decimator_ccf_0.declare_sample_delay(0)
               
        self.pfb_arb_resampler_xxx_0 = pfb.arb_resampler_ccf(samp_rate_out/(samp_rate/3),
                taps=None, flt_size=10, atten=100)
        self.pfb_arb_resampler_xxx_0.declare_sample_delay(0)

        self.top_layout.addWidget(self._ppm_slider_win)
        self.gsm_receiver_0 = grgsm.receiver(osr=osr, cell_allocation=([arfcn.downlink2arfcn(fc_slider)]), seq_nums=([]), fc=fc, sample_offset=self.current_offset, process_uplink=False)
        self.gsm_control_channels_decoder_0 = grgsm.control_channels_decoder()
        self.gsm_bcch_ccch_demapper_0 = grgsm.gsm_bcch_ccch_demapper(
            timeslot_nr=0,
        )
        self._gain_slider_range = Range(0, 100, 0.5, gain, 100)
        self._gain_slider_win = RangeWidget(self._gain_slider_range, self.set_gain_slider, "Gain", "counter", float)
        self.top_layout.addWidget(self._gain_slider_win)
        self.signal_handler_blk = signal_block()
        self.blocks_socket_pdu_0_1 = blocks.socket_pdu("UDP_CLIENT", collector, collectorport, 1500, False)
        self.blocks_socket_pdu_0_0 = blocks.socket_pdu("UDP_SERVER", "127.0.0.1", serverport, 10000, False)
        self.blocks_message_debug_0 = blocks.message_debug()

        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.gsm_bcch_ccch_demapper_0, 'bursts'), (self.gsm_control_channels_decoder_0, 'bursts'))    
        self.msg_connect((self.gsm_control_channels_decoder_0, 'msgs'), (self.blocks_socket_pdu_0_1, 'pdus')) 
        self.msg_connect((self.gsm_receiver_0, 'message'), (self.signal_handler_blk, 'msg_in'))    
        self.msg_connect((self.gsm_receiver_0, 'C0'), (self.gsm_bcch_ccch_demapper_0, 'bursts'))    
        self.connect((self.sdr_source_0, 0), (self.pfb_decimator_ccf_0, 0))    
        self.connect((self.pfb_arb_resampler_xxx_0, 0), (self.qtgui_sink_x_0 , 0))    
        self.connect((self.pfb_arb_resampler_xxx_0, 0), (self.gsm_receiver_0, 0))    
        self.connect((self.pfb_decimator_ccf_0, 0), (self.pfb_arb_resampler_xxx_0, 0))    

        ##################################################
        # Dependent Variables
        ##################################################
        self.FC_BANDWIDTH_1800 = self.sdr_source_0.FC_BANDWIDTH_1800
        self.FC_BANDWIDTH_900 = self.sdr_source_0.FC_BANDWIDTH_900

        self.LOWPASS_900 = firdes.low_pass(1, self.FC_BANDWIDTH_900,125e3,5e3,firdes.WIN_HAMMING,6.76)
        self.LOWPASS_1800 = firdes.low_pass(1, self.FC_BANDWIDTH_1800,125e3,5e3,firdes.WIN_HAMMING,6.76)
        self.current_taps = self.LOWPASS_900

    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "grgsm_livemon")
        self.settings.setValue("geometry", self.saveGeometry())
        event.accept()

    def get_fc(self):
        return self.fc

    def set_fc(self, fc, offset=0):
        self.current_offset = self.gsm_receiver_0.get_sample()
        # change sample rate and  bandwidth size acrort band
        if self.device == "FILE_DEVICE":
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
        print("[GSM-LIVEMON] jump to frequency {} at offset {} fucking ppm {} with sample rate {}"
            .format(self.fc, self.current_offset, self.gsm_receiver_0.get_ppm(), self.samp_rate))
 
    def get_gain(self):
        return self.gain

    def set_gain(self, gain):
        self.gain = gain
        self.set_gain_slider(self.gain)

    def get_ppm(self):
        return self.gsm_receiver_0.get_ppm()

    def set_ppm(self, ppm):
        self.ppm = ppm
        self.set_ppm_slider(self.ppm)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.sdr_source_0.set_samp_rate(samp_rate)
        self.pfb_decimator_ccf_0.set_taps(taps = (self.current_taps))
        self.pfb_arb_resampler_xxx_0.set_rate(self.samp_rate_out/(samp_rate/3))
        self.qtgui_sink_x_0.set_frequency_range(0, self.samp_rate)

    def get_offset(self):
        current_offset = self.gsm_receiver_0.get_sample()
        return current_offset

    def set_ppm_slider(self, ppm_slider):
        self.ppm_slider = ppm_slider

    def set_gain_slider(self, gain_slider):
        self.gain_slider = gain_slider
        self.sdr_source_0.set_gain(self.gain_slider)

    def get_search_status(self):
        return self.gsm_receiver_0.get_current_channel_state()

    def set_found_fcch_callback(self, callback=None):
        self.signal_handler_blk.callback_found_fcch = callback

    def set_search_fail_callback(self, callback=None):
        self.signal_handler_blk.callback_search_fail = callback



