# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: File Source
# Generated: Mon Nov 25 17:09:19 2019
##################################################

from gnuradio import blocks
from gnuradio import gr
from gnuradio.filter import firdes
from math import pi
from grgsm import arfcn
from grgsm import grd_config
from app import gsm_band
import grgsm
import math
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class BaseSource(gr.hier_block2):
    system_config = grd_config()

    FC_BANDWIDTH_1800 = system_config.get_sampout_dcs()
    FC_BANDWIDTH_900 = system_config.get_sampout_gsm()
    FC_START_900 = system_config.get_fcapture_gsm()

    logger.info("Loaded config DCS bandwidth {}, GSM bandwidth {}".format(FC_BANDWIDTH_1800, FC_BANDWIDTH_900))
    def __init__(self, fc=FC_START_900, osr=4, samp_rate=FC_BANDWIDTH_900, gain=40, offset=0, device="FILE_DEVICE"):
        ##################################################
        # Parameters
        ##################################################
        self.fc = fc
        self.osr = osr
        self.samp_rate = samp_rate
        self.gain = 0
        self.device = device
        self.offset = offset
        ##################################################
        # Variables
        ##################################################
        self.fc0 = fc0 = 0

    def get_fc(self):
        return self.fc

    def set_fc(self, fc, offset=0):
        self.fc = fc

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate

    def set_gain(self, gain):
        self.gain = gain
    
    def get_gain(self):
        return self.gain
    
    @staticmethod
    def get_source_info():
        logger.info("Not implement get source info function")
        return None

    @staticmethod
    def probe():
        logger.info("Implement probe function for source module")
        return False

