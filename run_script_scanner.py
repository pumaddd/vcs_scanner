import os
import time
import logging
import signal
import json
from app import signal_handler
from app import helper
from app.database import API

signal.signal(signal.SIGINT, signal_handler.daemon_signal_handler)
signal.signal(signal.SIGRTMIN + 12, signal_handler.daemon_signal_handler)
signal.signal(signal.SIGRTMIN + 14, signal_handler.daemon_signal_handler)
signal.signal(signal.SIGTERM, signal_handler.daemon_signal_handler)

while not os.path.isfile("/tmp/setting"):
    time.sleep(1)
    logging.error("wait for setting file")

with open("/tmp/setting", "r") as f:
    setting = json.load(f)
    if setting["clear_before_run"]:
        logging.error("Claer database !!!")
        API.empty_database()

while True:
    # TODO Fix hard path
    helper.clean_scanner_running()
    os.system("python run.py --device FILE_DEVICE --bands GSM900 DCS")
    logging.error("[DAEMON] restart scanner service ----------------")
    while True:
        logging.error("[DAEMON] monitor sleep")
        pids = os.popen("ps aux | grep run.py | grep -v grep | awk \'{print $2}\'").read().split()
        print("GSMSCANNER pid {}".format(pids))
        time.sleep(1)
        if len(pids) < 2:
            time.sleep(2)
            break
