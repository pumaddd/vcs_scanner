#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @file
# @author (C) 2015 by Piotr Krysik <ptrkrysik@gmail.com>
# @author (C) 2015 by Roman Khassraf <rkhassraf@gmail.com>
# @section LICENSE
#
# Gr-gsm is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# Gr-gsm is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with gr-gsm; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#
#
from gnuradio import blocks
from gnuradio import gr
from gnuradio import eng_notation
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from math import pi
from optparse import OptionParser
from app import config
from app.modules_manager import sdr_source 
from app.modules.sources.file_source import source
from grgsm.multichannel_file_source import multi_channelize_layer as channelizer_ccf
import grgsm
import numpy
import os
from gnuradio import uhd
import pmt
import time
import sys
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class receiver_with_decoder(grgsm.hier_block):
    def __init__(self, OSR=4, chan_num=0, fc=939.4e6, sample_offset=0, ppm=0, samp_rate=4e6):
        gr.hier_block2.__init__(
            self, "Receiver With Decoder",
            gr.io_signature(1, 1, gr.sizeof_gr_complex * 1),
            gr.io_signature(0, 0, 0),
        )
        #self.message_port_register_hier_out("bursts")
        self.message_port_register_hier_out("msgs")

        ##################################################
        # Parameters
        ##################################################
        self.OSR = OSR
        self.chan_num = chan_num
        self.fc = fc
        self.ppm = ppm
        self.samp_rate = samp_rate
        self.sample_offset = sample_offset

        ##################################################
        # Variables
        ##################################################
        self.samp_rate_out = samp_rate_out = 1625000.0 / 6.0 * OSR

        ##################################################
        # Blocks
        ##################################################
        self.gsm_receiver_0 = grgsm.receiver(OSR, ([chan_num]), ([]), fc, sample_offset)
        self.gsm_input_0 = grgsm.gsm_input(
            ppm=ppm,
            osr=OSR,
            fc=fc,
            samp_rate_in=samp_rate,
        )
        self.gsm_control_channels_decoder_0 = grgsm.control_channels_decoder()
        self.gsm_bcch_ccch_demapper_0 = grgsm.gsm_bcch_ccch_demapper(0)

        ##################################################
        # Connections
        ##################################################
        #self.msg_connect(self.gsm_bcch_ccch_demapper_0, 'bursts', self, 'bursts')
        self.msg_connect(self.gsm_bcch_ccch_demapper_0, 'bursts', self.gsm_control_channels_decoder_0, 'bursts')
        self.msg_connect(self.gsm_control_channels_decoder_0, 'msgs', self, 'msgs')
        self.msg_connect(self.gsm_receiver_0, 'C0', self.gsm_bcch_ccch_demapper_0, 'bursts')
        self.connect((self.gsm_input_0, 0), (self.gsm_receiver_0, 0))
        self.connect((self, 0), (self.gsm_input_0, 0))
        
        #self.connect((self, 0), (self.gsm_receiver_0, 0))

    def get_OSR(self):
        return self.OSR

    def set_OSR(self, OSR):
        self.OSR = OSR
        self.set_samp_rate_out(1625000.0 / 6.0 * self.OSR)
        self.gsm_input_0.set_osr(self.OSR)

    def get_chan_num(self):
        return self.chan_num

    def set_chan_num(self, chan_num):
        self.chan_num = chan_num

    def get_fc(self):
        return self.fc

    def set_fc(self, fc):
        self.fc = fc
        self.gsm_input_0.set_rf_freq(self.fc)

    def get_ppm(self):
        return self.ppm

    def set_ppm(self, ppm):
        self.ppm = ppm
        self.gsm_input_0.set_freq_corr(self.ppm, 0)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.gsm_input_0.set_samp_rate(self.samp_rate)

    def get_sample_rate_out(self):
        return self.samp_rate_out

    def set_samp_rate_out(self, samp_rate_out):
        self.samp_rate_out = samp_rate_out

    def get_current_offset(self):
        self.offset = self.gsm_receiver_0.get_sample() 
        return int(self.offset)

    def destroy(self):
        self.msg_disconnect(self.gsm_receiver_0, 'C0', self.gsm_bcch_ccch_demapper_0, 'bursts')
        self.disconnect_all() 
        del self.gsm_bcch_ccch_demapper_0
        del self.gsm_control_channels_decoder_0
        del self.gsm_receiver_0
        del self.gsm_input_0
        pass

class wideband_scanner(gr.top_block):
    def __init__(self, rec_len=1, scan_bandwidth=4e6, osr=4, carrier_frequency=939e6, gain=24, ppm=0, device="FILE_DEVICE", args="", offset=0, arfcns_list=[]):
        gr.top_block.__init__(self, "Wideband Scanner")
        
        ##################################################
        # Parameters
        ##################################################
        self.OSR_PFB = 1
        self.rec_len = rec_len
        self.scan_bandwidth = scan_bandwidth
        self.osr = osr
        self.ppm = ppm
        self.start_offset = offset
        self.device = device
        #self.arfcns = self.get_scan_arfcns(fc=carrier_frequency, bandwidth=scan_bandwidth)
        arfcns_list.sort()
        self.arfcns = arfcns_list
        #self.source_module = sdr_source.get_source_module(device=device)
        self.source_module = source
        self._source = self.source_module()
        ##################################################
        # Blocks
        ##################################################
        self.source_info = self._source.get_source_info()
        self.heads = []
        self.gsm_extract_system_info = grgsm.extract_system_info()
        self.channel_sources = self.create_sources()
        self.receivers_with_decoders = self.create_receivers()
        _fc_list = [info["fc"] for info in self.channel_sources]
        _sampl_rate_list = [info["samp_rate"] for info in self.channel_sources]
        self.channelizer = channelizer_ccf(arfcns=self.arfcns, 
                input_fc_info=_fc_list, input_bandwidth_info=_sampl_rate_list)
        logger.info("channelizers {} with scan list {} start at offset {}"\
                .format(self.channelizer, self.arfcns, self.start_offset))
        logger.info("[DEBUG MEMLEAK SCANNER]-------------buffer_ncurrently_allocated {}".format(gr.buffer_ncurrently_allocated()))
        ##################################################
        # Connections
        ##################################################
        # connect sources to multi-channelizer
        for index in range(len(self.channel_sources)):
            head = blocks.head(gr.sizeof_gr_complex * 1, int(rec_len*self.channel_sources[index]["samp_rate"]))
            self.heads.append(head)
            self.connect((self.channel_sources[index]["source"], 0), (head, 0))
            self.connect((head, 0), (self.channel_sources[index]["rotator"], 0))
            self.connect((self.channel_sources[index]["rotator"], 0), (self.channelizer, index))
        
        # connect channelizer output to receiver decoders
        for index in range(self.channelizer.noutput):
            #print("[MULTICHANNELIZER]connect port index {}".format(index))
            self.connect((self.channelizer, index), (self.receivers_with_decoders[index], 0))
            self.msg_connect(self.receivers_with_decoders[index], 'msgs', self.gsm_extract_system_info, 'msgs')
    @staticmethod
    def get_scan_arfcns(fc=939e6, bandwidth=4e6):
        numchans = int(bandwidth / 0.2e6)
        arfcn = grgsm.arfcn.downlink2arfcn(fc)
        arfcn_range = range(arfcn - numchans/2, arfcn + numchans/2)
        return arfcn_range
    
    def create_receivers(self):
        receivers_with_decoders = {}
        #print("[MULTICHANNELIZER] channel source {}".format(self.channel_sources))
        _index_offset = 0
        for source in self.channel_sources:
            logger.info("setup channel for arfcn {} in channel frequency {}"
                    .format(source["arfcns"], source["fc"]))
            for arfcn in source["arfcns"]:
                receivers_with_decoders[_index_offset] = receiver_with_decoder(fc=source["fc"], 
                        OSR=self.osr, chan_num=arfcn, samp_rate=self.OSR_PFB * 0.2e6)
                _receiver = {arfcn: receivers_with_decoders[_index_offset]}
                source.update(_receiver)
                _index_offset += 1

        # return receivers list
        return receivers_with_decoders

    def create_sources(self):
 
        _start_fc = grgsm.arfcn.arfcn2downlink(self.arfcns[0])
        _stop_fc = grgsm.arfcn.arfcn2downlink(self.arfcns[-1])
        logger.info("set frequency range {} - {}".format(_start_fc, _stop_fc))
        channel_sources = []
        for channel_info in self.source_info:
            #_start_channel = channel_info[0] - channel_info[1] / 2
            _start_channel_arfcn = grgsm.arfcn.downlink2arfcn(channel_info[0]) - int(channel_info[1] / 2 /0.2e6)
            #print("start channel arfcn {} center {}"\
            #        .format(_start_channel_arfcn, grgsm.arfcn.downlink2arfcn(channel_info[0])))
            if grgsm.arfcn.downlink2arfcn(channel_info[0]) >= 512:
                _start_channel_arfcn = _start_channel_arfcn if _start_channel_arfcn > 0 else 512
            if grgsm.arfcn.downlink2arfcn(channel_info[0]) < 512:
                _start_channel_arfcn = _start_channel_arfcn if _start_channel_arfcn > 0 else 0
            _stop_channel_arfcn = grgsm.arfcn.downlink2arfcn(channel_info[0]) + int((channel_info[1]/0.2e6+1)/ 2)
            _chan_num = int(channel_info[1] / 0.2e6)
            #print("[MULTICHANNELIZER]channel center frequency {} samp_rate {} receiver offset {}"
            #            .format(channel_info[0], channel_info[1], self.start_offset))
            _channel_arfcns = range(_start_channel_arfcn, _stop_channel_arfcn)
            # add center frequency into fc list if scan range in band range of channel
            _arfcns_list = list(set(_channel_arfcns) & set(self.arfcns))
            _arfcns_list.sort()

            if _arfcns_list:
                logger.info("Check source info list {} have arfcns {}".format(_channel_arfcns, _arfcns_list))
                info = {"fc":   channel_info[0],
                        "samp_rate":    channel_info[1],
                        "arfcns":   _arfcns_list,
                        }
                _file_offset = int(self.start_offset * info["samp_rate"] / (1625000.0 / 6.0 * self.osr))
                # Set rotator value for source module
                if _chan_num % 2 == 0:
                    rotate_value = -2 * pi * 0.1e6 / channel_info[1]
                elif _chan_num % 2 == 1:
                    rotate_value = 0
                _rotator = blocks.rotator_cc(rotate_value)
                _gsm_source = self.source_module(fc=info["fc"], samp_rate=info["samp_rate"], 
                        device=self.device, offset=_file_offset)
                _gsm_source.source_init()
                info.update({"source":  _gsm_source})
                info.update({"rotator": _rotator})
                channel_sources.append(info)

        # return created channel source
        # sort channel source increment
        def sort_source_fc(e):
            return e["fc"]
        channel_sources.sort(key=sort_source_fc)
        return channel_sources
    
    def get_OSR(self):
        return self.osr

    def set_OSR(self, osr):
        self.osr = osr
        self.create_receivers()

    def get_fc(self):
        return self.carrier_frequency 

    def set_fc(self, fc):
        self.carrier_frequency = fc
        #self.create_receivers()

    def get_sample_rate_out(self):
        return self.receivers_with_decoders[0].get_sample_rate_out()

    def get_current_offset(self):
        # return tuple of offset sample rate of the first channel
        return self.receivers_with_decoders[0].get_current_offset()

    def get_process_items(self):
        sample = self.channel_sources[0]["source"].get_process_items()
        logger.info("source get item number {}".format(sample))
        return sample
    
    def scanner_handler_eof(self):
        logger.error("receive end of file stop scanner")
        config.state = "STOPPED"
        self.stop()
        return
 
    def destroy(self):
        logger.info("source destroy")
        self.disconnect_all() 
        for index in self.receivers_with_decoders:
            self.receivers_with_decoders[index].destroy()
            self.msg_disconnect((self.receivers_with_decoders[index], 'msgs'),(self.gsm_extract_system_info, 'msgs'))
        
        for source_info in self.channel_sources:
            del source_info["source"]
            del source_info["rotator"]

        self.channelizer.destroy()
        del self.channelizer
        pass
