import app
from app import helper
from app import signal_handler
from app import gsm_scanner
from app.modules_manager import sdr_source
from app.database import API
from app.signal_handler import terminate_handler
from app import ch
import argparse
import signal
import os
import time
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(ch)


modules = sdr_source.probe_connected_devices()

parser = argparse.ArgumentParser(description='Parser input')
parser.add_argument("--channel-debug", nargs='+', help="run scanner in debug channel", dest="channels")
parser.add_argument("--graphic", action="store_true", help="run program with graphic channel monitor")
parser.add_argument("--network", help="specify network provider to scan")
parser.add_argument("--device", help="specify sdr device to use in one of {}".format(modules))
parser.add_argument("--database", help="name of database to use, default database is app.db")
parser.add_argument("--bands", nargs='+', help="gsm band to scan include ['GSM850', 'GSM-R', 'GSM900', 'EGSM', 'DCS', 'PCS']")
parser.add_argument("--save-log", help="save stardard output to log file", dest="log")
parser.add_argument("--offset-limit", nargs='+', type=int, help="run scanner in prior of time offset", dest="duration")
args = parser.parse_args()

if args.channels:
    app.config.channels = args.channels
else:
    app.config.channels = None

if args.graphic:
    app.config.graphic = True
else:
    app.config.graphic = False

# if args.network:
#     app.config.network = args.network
# else:
#     app.config.network = None

app.config.network = None
app.config.state = "RUNNING"
app.config.capture_round = 0

if args.bands:
    app.config.bands = args.bands
else:
    app.config.bands = ["DCS"]

if args.device in modules:
    app.config.device = args.device
else:
    app.config.device = modules[0]

if args.database:
    app.config.database = args.database
else:
    app.config.datase = "app.db"

if args.log:
    app.config.log = args.log
else:
    app.config.log = None

if args.duration:
    app.config.offset = tuple((args.duration[0], args.duration[1]))
    app.config.mode = "OFFLINE"
else:
    app.config.offset = None
    app.config.mode = "ONLINE"

signal.signal(signal.SIGINT, signal_handler.signal_handler)
signal.signal(signal.SIGRTMIN + 12, signal_handler.signal_handler)
signal.signal(signal.SIGRTMIN + 14, signal_handler.signal_handler)

# Write PID to file
pid = os.getpid()
pgid = os.getpgid(pid)

print("PID = {}".format(pid))
with open('/tmp/scanner_pid', 'w+') as f:
    # Read last process id and send signal term to terminate all linger
    _old_gpid = f.read()
    print("terminate last process: {}".format(_old_gpid))
    try:
        print("send signal terminate process: {}")
        os.kill(int(_old_gpid), signal.SIGTERM)
    except Exception as e:
        import logging
        logging.error("ERROR {}".format(e))
        pass
    f.write(str(pid))

# Loop until /tmp/setting exist
while not os.path.isfile('/tmp/setting'):
    logging.error("not found /tmp/setting waitting !!!")
    time.sleep(1)

app.config.server_setting = signal_handler.update_setting()

scanner = gsm_scanner.GSMscanner()
scanner.run()
