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
from gnuradio.filter import pfb
from math import pi
from optparse import OptionParser
from app.modules_manager import sdr_source as source_module
from gnuradio import uhd
import grgsm
import numpy
import os
import logging
import pmt
import time
import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class receiver_with_decoder(grgsm.hier_block):
    def __init__(self, OSR=4, chan_num=0, fc=939.4e6, sample_offset=0, ppm=0, samp_rate=4e6):
        grgsm.hier_block.__init__(
            self, "Receiver With Decoder",
            gr.io_signature(1, 1, gr.sizeof_gr_complex * 1),
            gr.io_signature(0, 0, 0),
        )
        self.message_port_register_hier_out("bursts")
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
        self.msg_connect(self.gsm_bcch_ccch_demapper_0, 'bursts', self, 'bursts')
        self.msg_connect(self.gsm_bcch_ccch_demapper_0, 'bursts', self.gsm_control_channels_decoder_0, 'bursts')
        self.msg_connect(self.gsm_control_channels_decoder_0, 'msgs', self, 'msgs')
        self.msg_connect(self.gsm_receiver_0, 'C0', self.gsm_bcch_ccch_demapper_0, 'bursts')
        self.connect((self.gsm_input_0, 0), (self.gsm_receiver_0, 0))
        self.connect((self, 0), (self.gsm_input_0, 0))

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
        return self.offset

class wideband_receiver(grgsm.hier_block):
    def __init__(self, OSR=4, fc=939.4e6, samp_rate=4e6):
        grgsm.hier_block.__init__(
            self, "Wideband receiver",
            gr.io_signature(1, 1, gr.sizeof_gr_complex * 1),
            gr.io_signature(0, 0, 0),
        )
        self.message_port_register_hier_out("bursts")
        self.message_port_register_hier_out("msgs")
        self.__init(OSR, fc, samp_rate)

    def __init(self, OSR=4, fc=939.4e6, samp_rate=4e6):
        ##################################################
        # Parameters
        ##################################################
        self.OSR = OSR
        self.fc = fc
        self.samp_rate = samp_rate
        self.channels_num = int(samp_rate / 0.2e6)
        self.OSR_PFB = 1

        ##################################################
        # Blocks
        ##################################################
        self.pfb_channelizer_ccf_0 = pfb.channelizer_ccf(
            self.channels_num,
            (),
            self.OSR_PFB,
            100)
        self.pfb_channelizer_ccf_0.set_channel_map(([]))
        self.create_receivers()

        ##################################################
        # Connections
        ##################################################
        self.connect((self, 0), (self.pfb_channelizer_ccf_0, 0))
        for chan in xrange(0, self.channels_num):
            self.connect((self.pfb_channelizer_ccf_0, chan), (self.receivers_with_decoders[chan], 0))
            self.msg_connect(self.receivers_with_decoders[chan], 'bursts', self, 'bursts')
            self.msg_connect(self.receivers_with_decoders[chan], 'msgs', self, 'msgs')

    def create_receivers(self):
        self.receivers_with_decoders = {}
        arfcn = grgsm.arfcn.downlink2arfcn(self.fc)
        arfcn_offsets = numpy.fft.ifftshift(numpy.array(range(int(-numpy.floor(self.channels_num / 2)), 
                int(numpy.floor((self.channels_num + 1) / 2)))))

        for chan in xrange(0, self.channels_num):
            logger.info("Setup channel for arfcn {}".format(arfcn+arfcn_offsets[chan]))
            self.receivers_with_decoders[chan]=receiver_with_decoder(fc=self.fc, OSR=self.OSR, 
                    #chan_num=arfcn+arfcn_offsets[chan], samp_rate=self.OSR_PFB * 0.2e6)
                    chan_num=chan, samp_rate=self.OSR_PFB * 0.2e6)

    def get_OSR(self):
        return self.OSR

    def set_OSR(self, OSR):
        self.OSR = OSR
        self.create_receivers()

    def get_fc(self):
        return self.fc

    def set_fc(self, fc):
        self.fc = fc
        self.create_receivers()

    def get_samp_rate(self):
        return self.samp_rate

    def get_sample_rate_out(self):
        return self.receivers_with_decoders[0].get_sample_rate_out()

    def get_current_offset(self):
        return self.receivers_with_decoders[0].get_current_offset()

class wideband_scanner(gr.top_block):
    def __init__(self, rec_len=3, samp_rate=4e6, osr=4, carrier_frequency=939e6, gain=24, ppm=0, device="FILE_DEVICE", args="", offset=0):
        gr.top_block.__init__(self, "Wideband Scanner")

        self.rec_len = rec_len
        self.samp_rate = samp_rate
        self.osr = osr
        self.carrier_frequency = carrier_frequency
        self.ppm = ppm
        self.device = device
        # if no file name is given process data from rtl_sdr source
        self.head = blocks.head(gr.sizeof_gr_complex * 1, int(rec_len * samp_rate))
        self.wideband_receiver = wideband_receiver(OSR=osr, fc=carrier_frequency, samp_rate=samp_rate)
        self.gsm_extract_system_info = grgsm.extract_system_info()

        channels_num = int(samp_rate / 0.2e6)
        logger.info("Wideband scan with argument fc {}, samp_rate {} at file start offset {}"
                .format(carrier_frequency, samp_rate, offset))
        # even number of channel
        if channels_num % 2 == 0:
            # shift again by -0.1MHz in order to align channel center in 0Hz
            self.gsm_file_source_C0_0 = source_module(fc=carrier_frequency + 1e5, 
                    samp_rate=samp_rate, device=device, offset=offset)
            self.blocks_rotator_cc = blocks.rotator_cc(2 * pi * 0.1e6 / samp_rate)
            self.connect((self.head, 0), (self.blocks_rotator_cc, 0))
            self.connect((self.blocks_rotator_cc, 0), (self.wideband_receiver, 0))
        # odd number of channel
        #TODO fix odd number of channel does not allign
        elif channels_num % 2 == 1:
            #source_module = import_source(device=self.device)
            self.gsm_file_source_C0_0 = source_module(fc=carrier_frequency, samp_rate=samp_rate, 
                    device=device, offset=offset)
            self.connect((self.head, 0), (self.wideband_receiver, 0))

        self.connect((self.gsm_file_source_C0_0, 0), (self.head, 0))
        self.msg_connect(self.wideband_receiver, 'msgs', self.gsm_extract_system_info, 'msgs')

    def get_sample_rate_out(self):
        return self.wideband_receiver.get_sample_rate_out()

    def get_current_offset(self):
        return self.wideband_receiver.get_current_offset()

class channel_info(object):
    def __init__(self, arfcn, freq, cid, lac, mcc, mnc, ccch_conf, power, neighbours, cell_arfcns):
        self.arfcn = arfcn
        self.freq = freq
        self.cid = cid
        self.lac = lac
        self.mcc = mcc
        self.mnc = mnc
        self.ccch_conf = ccch_conf
        self.power = power
        self.neighbours = neighbours
        self.cell_arfcns = cell_arfcns

    def get_verbose_info(self):
        i = "  |---- Configuration: %s\n" % self.get_ccch_conf()
        i += "  |---- Cell ARFCNs: " + ", ".join(map(str, self.cell_arfcns)) + "\n"
        i += "  |---- Neighbour Cells: " + ", ".join(map(str, self.neighbours)) + "\n"
        return i

    def get_ccch_conf(self):
        if self.ccch_conf == 0:
            return "1 CCCH, not combined"
        elif self.ccch_conf == 1:
            return "1 CCCH, combined"
        elif self.ccch_conf == 2:
            return "2 CCCH, not combined"
        elif self.ccch_conf == 4:
            return "3 CCCH, not combined"
        elif self.ccch_conf == 6:
            return "4 CCCH, not combined"
        else:
            return "Unknown"

    def getKey(self):
        return self.arfcn

    def __cmp__(self, other):
        if hasattr(other, 'getKey'):
            return self.getKey().__cmp__(other.getKey())

    def __repr__(self):
        return "%s(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)" % (
            self.__class__, self.arfcn, self.freq, self.cid, self.lac,
            self.mcc, self.mnc, self.ccch_conf, self.power,
            self.neighbours, self.cell_arfcns)

    def __str__(self):
        return "ARFCN: %4u, Freq: %6.1fM, CID: %5u, LAC: %5u, MCC: %3u, MNC: %3u, Pwr: %3i" % (
            self.arfcn, self.freq / 1e6, self.cid, self.lac, self.mcc, self.mnc, self.power)

def do_scan(samp_rate, band, speed, ppm, gain, args, prn = None, debug = False, offset=0):
    signallist = []
    channels_num = int(samp_rate / 0.2e6)
    offset = offset
    for arfcn_range in grgsm.arfcn.get_arfcn_ranges(band):
        first_arfcn = arfcn_range[0]
        last_arfcn = arfcn_range[1]
        last_center_arfcn = last_arfcn - int((channels_num / 2) - 1)
        current_freq = None
        last_freq = None
        stop_freq = None
        if band == "DCS1800":
            current_freq = grgsm.arfcn.arfcn2downlink(first_arfcn + int(channels_num / 2 - 1))
            last_freq = grgsm.arfcn.arfcn2downlink(last_center_arfcn)
            stop_freq = last_freq + 0.2e6 * channels_num / 2

        if band == "GSM900":
            current_freq = 944.6e6
            last_freq = 950.6e6
            stop_freq = 951.8e6

        while current_freq < stop_freq:
            # instantiate scanner and processor
            scanner = None
            if band == "DCS1800":
                scanner = wideband_scanner(rec_len=6 - speed,
                                       samp_rate=samp_rate,
                                       carrier_frequency=current_freq,
                                       ppm=ppm, gain=gain, args=args, offset=offset)
            if band == "GSM900":
                scanner = wideband_scanner_gsm900(rec_len=6 - speed,
                                           samp_rate=samp_rate,
                                           carrier_frequency=current_freq,
                                           ppm=ppm, gain=gain, args=args, offset=offset)

            # start recording
            scanner.start()
            scanner.wait()
            scanner.stop()

            freq_offsets = numpy.fft.ifftshift(
                numpy.array(range(int(-numpy.floor(channels_num / 2)), int(numpy.floor((channels_num + 1) / 2)))) * 2e5)
            detected_c0_channels = scanner.gsm_extract_system_info.get_chans()

            found_list = []

            if detected_c0_channels:
                chans = numpy.array(scanner.gsm_extract_system_info.get_chans())
                found_freqs = current_freq + freq_offsets[(chans)]

                cell_ids = numpy.array(scanner.gsm_extract_system_info.get_cell_id())
                lacs = numpy.array(scanner.gsm_extract_system_info.get_lac())
                mccs = numpy.array(scanner.gsm_extract_system_info.get_mcc())
                mncs = numpy.array(scanner.gsm_extract_system_info.get_mnc())
                ccch_confs = numpy.array(scanner.gsm_extract_system_info.get_ccch_conf())
                powers = numpy.array(scanner.gsm_extract_system_info.get_pwrs())

                for i in range(0, len(chans)):
                    cell_arfcn_list = scanner.gsm_extract_system_info.get_cell_arfcns(chans[i])
                    neighbour_list = scanner.gsm_extract_system_info.get_neighbours(chans[i])

                    info = channel_info(grgsm.arfcn.downlink2arfcn(found_freqs[i]), found_freqs[i],
                                        cell_ids[i], lacs[i], mccs[i], mncs[i], ccch_confs[i], powers[i],
                                        neighbour_list, cell_arfcn_list)
                    found_list.append(info)

            scanner = None


            if not debug:
                # restore file descriptors so we can print the results
                os.dup2(save[0], 1)
                os.dup2(save[1], 2)
                # close the temporary fds
                os.close(null_fds[0])
                os.close(null_fds[1])
            if prn:
                prn(found_list)
            signallist.extend(found_list)

            current_freq += channels_num * 0.2e6
    return signallist

def argument_parser():
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    bands_list = ", ".join(grgsm.arfcn.get_bands())
    parser.add_option("-b", "--band", dest="band", default="GSM900",
                      help="Specify the GSM band for the frequency.\nAvailable bands are: " + bands_list)
    parser.add_option("-s", "--samp-rate", dest="samp_rate", type="float", default=2e6,
                      help="Set sample rate [default=%default] - allowed values even_number*0.2e6")
    parser.add_option("-p", "--ppm", dest="ppm", type="intx", default=0,
                      help="Set frequency correction in ppm [default=%default]")
    parser.add_option("-g", "--gain", dest="gain", type="eng_float", default=24.0,
                      help="Set gain [default=%default]")
    parser.add_option("", "--args", dest="args", type="string", default="",
                      help="Set device arguments [default=%default]."
                      " Use --list-devices the view the available devices")
    parser.add_option("-l", "--list-devices", action="store_true",
                      help="List available SDR devices, use --args to specify hints")
    parser.add_option("--speed", dest="speed", type="intx", default=4,
                      help="Scan speed [default=%default]. Value range 0-5.")
    parser.add_option("-v", "--verbose", action="store_true",
                      help="If set, verbose information output is printed: ccch configuration, cell ARFCN's, neighbour ARFCN's")
    parser.add_option("-d", "--debug", action="store_true",
                      help="Print additional debug messages")

    """
        Dont forget: sudo sysctl kernel.shmmni=32000
    """
    return parser

def main(options = None):
    if options is None:
        (options, args) = argument_parser().parse_args()

    if options.list_devices:
        grgsm.device.print_devices(options.args)
        sys.exit(0)

    if options.band not in grgsm.arfcn.get_bands():
        parser.error("Invalid GSM band\n")

    if options.speed < 0 or options.speed > 5:
        parser.error("Invalid scan speed.\n")

    def printfunc(found_list):
        for info in sorted(found_list):
            print info
            if options.verbose:
                print info.get_verbose_info()
    print ""
    do_scan(options.samp_rate, options.band, options.speed,
            options.ppm, options.gain, options.args, prn = printfunc, debug = options.debug)

if __name__ == '__main__':
    main()
