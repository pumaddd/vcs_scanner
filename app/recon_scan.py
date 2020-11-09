from app.modules.scanners.multichannelizer_recon import wideband_scanner as wideband_scanner
from app.modules.sources.file_source import source
from app.modules_manager import sdr_source
from app import helper
from app import gsm_band
from gnuradio import gr
from datetime import datetime
import app
import logging
import grgsm
import re
import numpy
import os, gc

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class recon_scan():
    MAX_SCAN_ROUND = 100
    def __init__(self, bands=["DCS"], gain=24, provider="VIETTEL", bandwidth_window = 20e6, osr=2, device="FILE_DEVICE", greedy=False, start_offset=0, scan_length=1):
        self.offset = start_offset
        self.osr = osr
        self.gain = gain
        self.device = device
        self.bands = bands
        self.provider = provider
        self.greedy = greedy
        self.gsm_symb_rate = 1625000.0/6.0
        self.end_of_file = False
        self.scan_length = scan_length
        self.round_time = self.scan_length
        
        self.scan_ranges = gsm_band.arfcn.get_arfcn_ranges(bands=bands, network=provider)
        # Scan bandwidth is band width of channelizer output or number of channels scan
        self.bandwidth_window = bandwidth_window

        # Initualize file source to check if database have enough information
        self.SCAN_BANDS = source.probe_database_info(round_index=app.config.capture_round)
        self.start_time = datetime.now()
        logger.info("Recon initualize start at {} scan bands {}".format(self.start_time, self.SCAN_BANDS))

    def do_scan(self):
        neighbor_list = []
        scan_arfcns = [] 
        scan_round = 0
        arfcn_num = int(self.bandwidth_window / 0.2e6)
        #TODO wideband scanner run until found signal arfcn
        while not neighbor_list:
            logger.info("Wideband start scan {}".format(scan_round))
            scan_arfcns = []
            for scan_range in self.scan_ranges:
                # Force bandwidth with file  source
                _start_arfcn = scan_range[0]
                _stop_arfcn = scan_range[1]
                scan_arfcns.extend(range(_start_arfcn, _stop_arfcn))

            logger.info("Initualize {} scanner with scan bandwidth {} with arfcn range {} provider {}"
                    .format(self.device, self.bandwidth_window, scan_arfcns, self.provider))
            scan_arfcns.sort()
            _scan_pointer = 0
            while _scan_pointer < len(scan_arfcns):
                arfcns = scan_arfcns[_scan_pointer:_scan_pointer + arfcn_num]
                arfcn_list = self.grgsm_scan(arfcns=arfcns)
                neighbor_list.extend([arfcn for arfcn in arfcn_list if not arfcn in neighbor_list])
                _scan_pointer += len(arfcns)

                if neighbor_list and self.greedy == False:
                    return neighbor_list
                
                if app.config.state != "RUNNING":
                    return neighbor_list

                if scan_round > recon_scan.MAX_SCAN_ROUND:
                    app.config.state = "LOST_SIGNAL"
                    return neighbor_list

                if self.end_of_file and app.config.state == "RUNNING":
                    app.config.state = "STOPPED"
                    return neighbor_list

            # Finish scan round add offset amount of round time
            self.offset += int(self.round_time * self.gsm_symb_rate)
            # Increment round counter
            scan_round += 1

        return neighbor_list

    def kalibrate_scan(band='DCS', gain='40', provider='VIETTEL'):
        support_band = ['GSM850', 'GSM-R', 'GSM900', 'EGSM', 'DCS', 'PCS']
        network_provider = ['VINAPHONE', 'MOBIFONE', 'VIETTEL', 'GMOBILE', 'VIETNAMOBILE'] 
        if not band in support_band:
            return None
        if provider in network_provider:
            logger.info("Run kalibrate with network provider {}".format(provider))
            out = helper.run_extern('kal -v -s {} -g {} -n {}'.format(band, gain, provider))
        else:
            logger.info("Run kalibrate with all network {}")
            out = helper.run_extern('kal -v -s {} -g {}'.format(band, gain))

        kal_regex = "chan: (\d*) \(([0-9\.]*)MHz \+ (.*)Hz\)\s*power:\s*([0-9\.]*)"
        channel_infos = re.findall(kal_regex, out)
        bcch_channels = []
        for channel in channel_infos:
            bcch_channels.append(int(channel[0]))

        logger.info('Kalibrate terminated return {}'.format(bcch_channels))
        return bcch_channels

    def grgsm_scan(self, arfcns=[]):
        self.last_offset = 0
        scan_arfcns = arfcns
        filter_list = []
        
        #TODO DEBUG
        import datetime
        logger.info("[RECON SCAN]arfcn scan in list {} ---- at time {}".format(scan_arfcns, datetime.datetime.now()))
        # instantiate scanner and processor
        scanner = wideband_scanner(
                arfcns_list=scan_arfcns,
                gain=self.gain, 
                scan_bandwidth=self.bandwidth_window,
                rec_len=self.scan_length,
                osr=self.osr, device=self.device, offset=self.offset)

        # start recording
        scanner.start()
        scanner.wait()
        scanner.stop()
        # Set end of file state if scanner doesnt process any items
        if scanner.get_process_items() == 0:
            self.end_of_file = True
        # save offsets from last scan
        self.last_offset = scanner.get_current_offset()
        detected_c0_channels = scanner.gsm_extract_system_info.get_chans()
        found_list = []
        arfcn_list = []
        signal_arfcn = []

        if detected_c0_channels:
            chans = numpy.array(scanner.gsm_extract_system_info.get_chans())
            cell_ids = numpy.array(scanner.gsm_extract_system_info.get_cell_id())
            lacs = numpy.array(scanner.gsm_extract_system_info.get_lac())
            mccs = numpy.array(scanner.gsm_extract_system_info.get_mcc())
            mncs = numpy.array(scanner.gsm_extract_system_info.get_mnc())
            ccch_confs = numpy.array(scanner.gsm_extract_system_info.get_ccch_conf())
            powers = numpy.array(scanner.gsm_extract_system_info.get_pwrs())

            for i in range(0, len(chans)):
                cell_arfcn_list = scanner.gsm_extract_system_info.get_cell_arfcns(chans[i])
                neighbour_list = scanner.gsm_extract_system_info.get_neighbours(chans[i])

                info = channel_info(chans[i], grgsm.arfcn.arfcn2downlink(chans[i]),
                                    cell_ids[i], lacs[i], mccs[i], mncs[i], ccch_confs[i], powers[i],
                                    neighbour_list, cell_arfcn_list)
                logger.info(info.get_verbose_info())
                found_list.append(info)
                arfcn_list = [cell.arfcn for cell in found_list if not cell.arfcn in signal_arfcn]
            signal_arfcn.extend(arfcn_list)
            for signal_cell in found_list:
                signal_arfcn.extend([arfcn for arfcn in signal_cell.neighbours if not arfcn in signal_arfcn])
            logger.info("Recon scan found channels {}".format(signal_arfcn))
            filter_list.extend([channel for channel in signal_arfcn if gsm_band.arfcn.check_arfcn_in_band(
                arfcn=channel, network=self.provider, bands=self.bands)])
        
        scanner.destroy()
        scanner = None
        logger.info("buffer_ncurrently_allocated before collect {}".format(gr.buffer_ncurrently_allocated()))
        gc.collect()

        return filter_list

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
        i =  "  |---- ARFCN:    {}\n".format( self.arfcn )
        i += "  |---- Configuration: %s\n" % self.get_ccch_conf()
        i += "  |---- Cell ARFCNs: " + ", ".join(map(str, self.cell_arfcns)) + "\n"
        i += "  |---- Neighbour Cells: " + ", ".join(map(str, self.neighbours)) + "\n"
        i += "  |---- Cell ID: {},  Lac : {}\n".format(self.cid, self.lac)
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


