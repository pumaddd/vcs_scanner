from subprocess import Popen, PIPE
import os, signal
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def run_extern(cmd):
    if cmd == None:
        return ''
    args = cmd.split(' ')
    process = Popen(args, stdout=PIPE)
    (output, err) = process.communicate()
    exit_code = process.wait()
    return output

def arfcn_to_freq(n, bi=None):
    freq = None
    n = int(n)
    if 128 <= n and n <= 251: 
        freq = 824.2e6 + 0.2e6 * (n - 128) + 45.0e6
    

    elif 1 <= n and n <= 124:
        freq = 890.0e6 + 0.2e6 * n + 45.0e6

    elif n == 0:
        freq = 935e6;
    
    elif 955 <= n and n <= 1023:
        freq = 890.0e6 + 0.2e6 * (n - 1024) + 45.0e6

    elif 512 <= n and n <= 810:
        if bi == 'DCS':
            freq = 1710.2e6 + 0.2e6 * (n - 512) + 95.0e6

        if bi == 'PCS1900':
            freq = 1850.2e6 + 0.2e6 * (n - 512) + 80.0e6

        logger.info('scanning band: {}'.format(bi))

    elif 811 <= n and n <= 885:
        freq =  1710.2e6 + 0.2e6 * (n - 512) + 95.0e6

    logger.info('convert channel: {} to frequency {} on band {}'.format(n, freq, bi))
    return freq

def arfcn_from_freq(freq,region):
    freq = freq / 1e6
    # GSM 450
    if freq <= 450.6 + 0.2*(293 - 259) + 10:
        arfcn = ((freq - (450.6 + 10)) / 0.2) + 259
    # GSM 480
    elif freq <= 479 + 0.2*(340 - 306) + 10:
        arfcn = ((freq - (479 + 10)) / 0.2) + 306
    # GSM 850
    elif freq <= 824.2 + 0.2*(251 - 128) + 45:
        arfcn = ((freq - (824.2 + 45)) / 0.2) + 128
    #E/R-GSM 900
    elif freq <= 890 + 0.2*(1023 - 1024) + 45:
        arfcn = ((freq - (890 + 45)) / -0.2) + 955
    # GSM 900
    elif freq <= 890 + 0.2*124 + 45:
        arfcn = (freq - (890 + 45)) / 0.2
    else:
        if region is "u":
            if freq > 1850.2 + 0.2*(810 - 512) + 80:
                arfcn = 0;
            else:
                arfcn = (freq - (1850.2 + 80) / 0.2) + 512
        elif region is "e":
            if freq > 1710.2 + 0.2*(885 - 512) + 95:
                arfcn = 0;
            else:
                arfcn = (freq - (1710.2 + 95) / 0.2) + 512
        else:
            arfcn = 0

    if arfcn<0:
        return 255
    else:
        return round(arfcn)

def scale(val, src, dst):
    if val < src[0]:
        return dst[0]
    elif val > src[1]:
        return dst[1]

    return (float(val - src[0]) / float(src[1]-src[0])) * float(dst[1]-dst[0]) + dst[0]

def my_join(thread):
    while thread.is_alive():
        thread.join(timeout=1)
            
def clean_scanner_running():
    out = os.popen("ps aux | grep run.py | grep -v grep | awk \'{print $2}\'").read()
    logger.info("list scanner process is running {}".format(out))
    pids = out.split()
    for pid in pids:
        os.kill(int(pid), signal.SIGTERM)
