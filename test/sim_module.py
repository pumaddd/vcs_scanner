import datetime
import re
import time
import serial
import os

def get_serial_interface():
    device_path = "/dev"
    full_path = os.path.abspath(device_path)
    files_name = os.listdir(full_path)
    interfaces = []
    for f in files_name:
        if f.find("ttyUSB") != -1:
            interfaces.append(os.path.join(full_path, f))

    return interfaces

def interactive_print():
    TTL = 5
    devices = get_serial_interface()
    if len(devices) != 0:
        device = devices[0]

    watchdog_counter = TTL
    f = serial.Serial(device, baudrate=115200, dsrdtr=True, rtscts=True)
    f.write('at+ceng=2, 1\r\n')
    _regex_pattern = re.compile("\+CENG: (\d),\"(\d*),(\d*),(\d*),(\w*),(\w*),(\w*),(\w*).*?\"\r\n")
    while True:
        time.sleep(5)
        watchdog_counter -= 1
        print("[DEBUG]counter at {}".format(watchdog_counter))
        if watchdog_counter < 0:
            print("[DEBUG]resend control signal")
            f.write('at+ceng=2, 1\r\n')

        #text = f.read_until("\r\n\r\n")
        text = f.read_all()
        if text:
            print("[+]get text {}".format(text))
            watchdog_counter = TTL
        entries = re.findall(_regex_pattern, text)
        for entry in entries:
            if entry[0] == "0": 
                print("\n[New round] at {}---------------------------".format(datetime.datetime.now()))
                print("[MAIN] arfcn: {} receive level: {} lac {}-{}-{}".format(entry[1], entry[2], entry[4], entry[5], entry[6]))

            print("({} {} --)".format(entry[1], entry[2])),

if __name__ == "__main__":
    print_interactive()

