from app.modules.source import BaseSource
from app import config
from app import gsm_band
from app.database import MySQL_external
from gnuradio import gr
from gnuradio import blocks
from gnuradio.filter import firdes
from grgsm import grd_config
from grgsm import arfcn
from math import pi
import numpy
import grgsm
import os, time, logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class source(BaseSource):
    
    __info__ = {
    'name': 'File source',
    'device': 'FILE_DEVICE',
    'description': 'source run with received offline data read from database in /etc/data'
    }

    def __init__(self, offset=0, **kw):
        system_config = grd_config()
        SOURCE_DATABASE = "/etc/data"
        self.FC_START_1800 = system_config.get_fcapture_dcs()
        self.FC_BANDWIDTH_1800 = system_config.get_sampout_dcs()
        self.FC_CAPTURE_1800 = system_config.get_sampcap_dcs()
        self.NUMBER_CHANNEL_1800 = int(self.FC_CAPTURE_1800 / self.FC_BANDWIDTH_1800)
        self.FC_START_900 = system_config.get_fcapture_gsm()
        self.FC_BANDWIDTH_900 = system_config.get_sampout_gsm()
        self.FC_CAPTURE_900 = system_config.get_sampcap_gsm()
        self.NUMBER_CHANNEL_900 = int(self.FC_CAPTURE_900 / self.FC_BANDWIDTH_900)

        self.SCAN_BANDS = source.probe_database_info(round_index=config.capture_round)
        self.FC_INFO_900 = MySQL_external.get_file_info_gsm(capture_round=config.capture_round)
        self.FC_INFO_1800 = MySQL_external.get_file_info_dcs(capture_round=config.capture_round)
        
        ##################################################
        # Parameter for device
        ##################################################
        self.offset_byte = int(offset)
        logger.info("Initualize source with module parameter {} at offset {}".format(kw, offset))
        super(source, self).__init__(**kw)
        
    def source_init(self):
        gr.hier_block2.__init__(
            self, "FILE Source",
            gr.io_signature(0, 0, 0),
            gr.io_signature(1, 1, gr.sizeof_gr_complex*1),
        )

        ##################################################
        # Variables
        ##################################################
        self.fc0 = self.get_fc_file(self.fc)

        ##################################################
        # Blocks
        ##################################################
        logger.info("Initualize file source fc0: {}".format(self.fc0))
        self.gsm_file_source_C0_0 = grgsm.file_source_C0(gr.sizeof_gr_complex*1, 
            self.offset_byte, str(self.fc0), False, index=config.capture_round)
        self.blocks_throttle_0 = blocks.throttle(gr.sizeof_gr_complex*1, self.samp_rate,True)
        self.blocks_rotator_cc_0 = blocks.rotator_cc(-2*pi*(self.fc-self.fc0)/self.samp_rate)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_rotator_cc_0, 0), (self, 0))    
        self.connect((self.blocks_throttle_0, 0), (self.blocks_rotator_cc_0, 0))    
        self.connect((self.gsm_file_source_C0_0, 0), (self.blocks_throttle_0, 0))    

        ##################################################
        # Initualize Block
        ##################################################
        self.set_fc(self.fc)
        self.set_samp_rate(self.samp_rate)
        self.set_gain(self.gain)

    def get_fc(self):
        return self.fc

    def set_fc(self, fc, offset=0):
        logger.info("Set to frequency {} in file {} offset {} with sample rate {}".format(self.fc, self.fc0, offset, self.samp_rate)) 
        
        # get file frequency fc0 which have fc frequency record
        fc0 = self.get_fc_file(fc)
        
        # not find file have frequency
        if fc0 == None:
            logger.info("Not found file have frequency: {} stay in {}".format(fc, self.fc0))
            fc0 = self.fc0
        
        # frequency setting not in current file, open new file
        if fc0 != self.fc0:
            self.fc0 = fc0
            # TODO set approciate offset
            self.gsm_file_source_C0_0.set_file_info(str(self.fc0), int(offset))
        
        self.fc = fc
        self.blocks_rotator_cc_0.set_phase_inc(-2*pi*(self.fc-self.fc0)/self.samp_rate)

    def get_offset_byte(self):
        return self.offset_byte

    def set_offset_byte(self, offset_byte):
        self.offset_byte = offset_byte

    def get_osr(self):
        return self.osr

    def set_osr(self, osr):
        self.osr = osr
        self.set_samp_rate_out(self.osr*self.gsm_symb_rate)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.blocks_rotator_cc_0.set_phase_inc(-2*pi*(self.fc-self.fc0)/self.samp_rate)
        self.blocks_throttle_0.set_sample_rate(self.samp_rate)

    def get_fc0(self):
        return self.fc0
   
    def get_fc_file(self, fc):
        fc0 = None
        if arfcn.downlink2arfcn(fc) >= 512:
            for info in self.FC_INFO_1800:
                if fc > info[0] - info[1]/2 and fc <= info[0] + info[1]/2:
                    fc0 = info[0]
                    break
        elif arfcn.downlink2arfcn(fc) < 512:
            for info in self.FC_INFO_900:
                if fc > info[0] - info[1]/2 and fc <= info[0] + info[1]/2:
                    fc0 = info[0]
                    break
        logger.info("Tunning to file center frequency {}".format(fc0))
        if fc0 == None:
            logger.error("Not found frequency {} in database".format(fc))

        return int(fc0)
    
    def get_source_info(self):
        offsets_1800 = numpy.fft.ifftshift(numpy.array(range(int(-numpy.floor(self.NUMBER_CHANNEL_1800 / 2)), int(numpy.floor((self.NUMBER_CHANNEL_1800 + 1) / 2)))) * self.FC_BANDWIDTH_1800)

        offsets_900 = numpy.fft.ifftshift(numpy.array(range(int(self.NUMBER_CHANNEL_900 / 2), int((self.NUMBER_CHANNEL_900 + 1) / 2))) * self.FC_BANDWIDTH_900)
        
        source_info = []
        source_info.extend(self.FC_INFO_1800)
        source_info.extend(self.FC_INFO_900)
        logger.info("Source info get from database {}".format(source_info))

        return source_info

#     @staticmethod 
#     def probe():
#         file_db = os.path.join(source.SOURCE_DATABASE, "file.db")
#         if not os.path.isfile(file_db):
#             logger.info("[FILE SOURCE]Not found databse file")
#             return False
#         # get downlink from querry database
#         paths = SQLite_external.get_file_source(uplink = False)
#         for path in paths:
#             if not os.path.isfile(path):
#                 logger.info("[FILE SOURCE]Not found entry file path {}".format(path))
#                 return False
#         
#         return True
  
    @staticmethod 
    def probe():
        return True
        # get downlink from querry database
        paths = MySQL_external.get_file_source(uplink = False)
        if not paths:
            return False

        for path in paths:
            if not os.path.isfile(path):
                logger.error("Not found entry file path {}".format(path))
                return False
        
        return True

    def update_file_config(self):
        self.system_config = grd_config()
        self.SOURCE_DATABASE = "/etc/data"
        self.FC_START_1800 = system_config.get_fcapture_dcs()
        self.FC_BANDWIDTH_1800 = system_config.get_sampout_dcs()
        self.FC_CAPTURE_1800 = system_config.get_sampcap_dcs()
        self.NUMBER_CHANNEL_1800 = int(self.FC_CAPTURE_1800 / self.FC_BANDWIDTH_1800)
        self.FC_START_900 = system_config.get_fcapture_gsm()
        self.FC_BANDWIDTH_900 = system_config.get_sampout_gsm()
        self.FC_CAPTURE_900 = system_config.get_sampcap_gsm()
        self.NUMBER_CHANNEL_900 = int(self.FC_CAPTURE_900 / self.FC_BANDWIDTH_900)

        self.FC_INFO_900 = MySQL_external.get_file_info_gsm()
        self.FC_INFO_1800 = MySQL_external.get_file_info_dcs()

    def get_process_items(self):
        sample = self.gsm_file_source_C0_0.nitems_written(0)
        return sample
    
    @staticmethod
    def probe_database_info(round_index=0):
        network = MySQL_external.get_network_from_capture_round(capture_round=round_index)
        network_ranges = gsm_band.arfcn.get_arfcn_ranges(network=network, bands=config.bands)
        arfcn_range = []
        _FC_INFO_1800 = None
        _FC_INFO_900 = None
        for network_range in network_ranges:
            arfcn_range.extend(range(network_range[0], network_range[1]))

        logger.info("Network range from config {}".format(arfcn_range))
        while True:
            database_arfcn = []
            _FC_INFO_1800 = MySQL_external.get_file_info_dcs(capture_round=round_index)
            for band in _FC_INFO_1800:
                _start_arfcn = grgsm.arfcn.downlink2arfcn(band[0]) - int(band[1] / 2 / 0.2e6)
                _stop_arfcn = grgsm.arfcn.downlink2arfcn(band[0]) + int((band[1] / 0.2e6+1)/ 2)
                database_arfcn.extend(range(_start_arfcn, _stop_arfcn))
            _FC_INFO_900 = MySQL_external.get_file_info_gsm(capture_round=round_index)
            for band in _FC_INFO_900:
                _start_arfcn = grgsm.arfcn.downlink2arfcn(band[0]) - int(band[1] / 2 / 0.2e6)
                _stop_arfcn = grgsm.arfcn.downlink2arfcn(band[0]) + int((band[1] / 0.2e6+1)/ 2)
                database_arfcn.extend(range(_start_arfcn, _stop_arfcn))

            if set(arfcn_range) & set(database_arfcn) == set(arfcn_range):
                logger.info("Database have enough file information")
                break

            logger.info("Database not enough information about arfcns: {} waiting !!!"
                    .format(set(arfcn_range) - set(database_arfcn)))
            time.sleep(1)

        bands_scan = []
        if _FC_INFO_1800:
            bands_scan.append("DCS")
            logger.info("Probe file source got DCS {} from database".format(_FC_INFO_1800))
        if _FC_INFO_900:
            bands_scan.append("GSM900")
            logger.info("Probe file source got GSM {} from database".format(_FC_INFO_900))
        logger.info("Probe file source got bands DCS {} GSM900 {} from database".format(_FC_INFO_1800, _FC_INFO_900))
        return bands_scan

