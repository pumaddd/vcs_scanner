"""
Embedded Python Blocks:

Each this file is saved, GRC will instantiate the first class it finds to get
ports and parameters of your block. The arguments to __init__  will be the
parameters. All of them are required to have default values!
"""
import numpy as np
from gnuradio import gr
import pmt
import os, signal
import logging
import json
import app

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class signal_block(gr.sync_block):

    def __init__(self, round_done_handler=None, end_file_handler=None):  # only default arguments here
        gr.sync_block.__init__(
            self,
            name='Embedded Python Block',
            in_sig=None,
            out_sig=None
        )
        self.round_done_handler = round_done_handler
        self.end_file_handler = end_file_handler
        self.message_port_register_in(pmt.intern('msg_in'))
        self.set_msg_handler(pmt.intern('msg_in'), self.handle_msg)
        logger.info("Initualized signal block")

    def work(self, input_items, output_items):
        pass

    def handle_msg(self, msg):
        signal_msg = pmt.pmt_to_python.pmt_to_tuple(msg)
        logging.error("handle callback with message: {}".format(signal_msg))
        if signal_msg[0] == 'end_of_scan':
            logger.info("Receive signal scan done")
            self.round_done_handler()
        if signal_msg[0] == 'end_of_file':
            logger.info("Receive end of file signal")
            self.end_file_handler()

def terminate_handler(signalNumber, frame):
    logger.warning("GSM SCANNER terminated !!!")
    pid = os.getpid()
    os.kill(pid, signal.SIGTERM)

def send_terminate():
    logger.warning("GSM SCANNER terminated !!!")
    pid = os.getpid()
    gpid = os.getpgid(pid)
    os.kill(pid, signal.SIGTERM)

def update_setting():
    with open("/tmp/setting", "r") as f:
        setting = json.load(f)
        if app.config.network is None:
            # First time set network
            app.config.network = str(setting['operator_name']).upper()
        elif app.config.network != str(setting['operator_name']).upper():
            logger.warning("Change network to {}".format(setting['operator_name']))
            # Stop gsm_scanner
            app.config.state = "NETWORK_CHANGE"
        else:
            logging.warning("Keep network setting")
        
        if str(setting['mode']) == '2':
            app.config.state = "STOPPED"
        elif str(setting['mode']) == '1' and app.config.state == "STOPPED":
            app.config.state = "NETWORK_CHANGE"

        return setting

def signal_handler(signum, frame):
    logger.warning("Signal {} receive".format(signum))
    if signum is signal.SIGINT:
        logger.warning("GSM SCANNER terminated !!!")
        pid = os.getpid()
        gpid = os.getpgid(pid)
        #os.killpg(gpid, signal.SIGINT)
        app.config.state = "STOPPED"
        send_terminate()

    if signum is signal.SIGRTMIN + 12:
        logger.warning("Receive new setting !!! Updating ...")
        update_setting()

    if signum is signal.SIGRTMIN + 14:
        # This signal notice prepare poweroff, need to clear tables
        logger.error("Power off ???")
        # Receive signal POWEROFF, stop scanner
        app.config.state = "STOPPED"

def daemon_signal_handler(signum, frame):
    logger.error("Deamnon receiver signal {} ".format(signum))
    if signum is signal.SIGINT:
        #pass
        send_terminate()
        exit()
    if signum is signal.SIGRTMIN + 12:
        pass
    if signum is signal.SIGRTMIN + 14:
        pass
    if signum is signal.SIGTERM:
        pass

