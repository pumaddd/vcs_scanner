import sys
from app import session
from app.models import scan_arfcn
import time, datetime
from app.database import API
from app.database import SQLite_external
import sys

def pretty_print():
    entries = session.query(scan_arfcn).filter(scan_arfcn.scan_level == 1).order_by(scan_arfcn.round.asc())
    current_round = 0
    for entry in entries:
        if entry.round != current_round:
            current_round = entry.round
            print('\n[New round]: {} timestamp {}'.format(entry.round, entry.timestamp))
        print "({} {} {}), ".format(entry.arfcn, entry.average_pwr, entry.pkt_number),

def interactive_print():
    current_round = API.get_round_lastest()
    while True:
        time.sleep(2)
        next_round = API.get_round_lastest()
        if current_round != next_round:
            entries = API.get_round_entries(current_round)
            print("\n[Round {}] -- time: {}".format(entries[0].round, entries[0].timestamp))
            for entry in entries:
                print "({} {} {}), ".format(entry.arfcn, entry.average_pwr, entry.pkt_number),
            
            current_round = next_round

def camp_cell_extract_time():

    GSM_SYMB_RATE = 1625000.0/6.0
    OSR = 4
    MAX_BLOCK_DISPLAY = 12
    DEVICE_DELAY = 5 # time offset scanner faster than mobile refence

    round_count = 0
    found_signal = 0
    match_scan = 0
    
    # query to get first target round is the time start call
    target_round = SQLite_external.get_target_camp_arfcn()

    # query HoangAnh database to get call offset
    # query database to get monitor round 
    start_time = datetime.datetime.fromtimestamp(target_round["time"]/1000)
    r = API.get_round_from_time(start_time)
    scanner_rounds = API.get_round_entries(r) 
    #time_offset= scanner_rounds[0].timestamp
    time_offset= start_time

    print("-"*110)
    while True:
        print("|camping {:<4}\t{} + {}s (index {})|".format(target_round["arfcn"], 
                datetime.datetime.fromtimestamp(target_round["time"]/1000), DEVICE_DELAY, target_round["time"])),
        block = 0
        try:
            arfcns = [int(entry.arfcn) for entry in scanner_rounds]
        except:
            arfcns = []

        for arfcn in arfcns:
            block += 1
            print("{:>4},".format(arfcn)),

        for i in range (block, MAX_BLOCK_DISPLAY):
            print("{:>4} ".format("")),

        # end of round
        print("|round:{:>5}|time: {}".format(entry.round, entry.timestamp))
        #print("round: {}    found: {}   match: {}".format(round_count, found_signal, match_scan))
        print("-"*110)
        
        # static result update
        round_count += 1
        if target_round["arfcn"] in arfcns:
            found_signal += 1

        if len(arfcns) > 3 and target_round["arfcn"] in [arfcns[0], arfcns[1], arfcns[2]]:
            match_scan += 1
        elif len(arfcns) <= 3 and target_round["arfcn"] in arfcns:
            match_scan += 1

        # query next round from target log with time is key
        target_round_next = SQLite_external.get_target_camp_arfcn(time=target_round['time'])
        time_delta = (target_round_next['time'] - target_round['time'])
        time_offset += datetime.timedelta(milliseconds=time_delta)
        r = API.get_round_from_time(time_offset + datetime.timedelta(seconds=DEVICE_DELAY))
        scanner_rounds = API.get_round_entries(r)
        target_round = target_round_next
        if not scanner_round:
            break

    print("Number of round scan: {}".format(round_count))
    print("Number of signal found in scan list: {}".format(found_signal))
    print("Number of matching signal: {}".format(match_scan))
    #print("End of program with error: {}".format(e))
    #import traceback
    #traceback.print_exc()

def camp_cell_extract_sample():

    GSM_SYMB_RATE = 1625000.0/6.0
    OSR = 2
    MAX_BLOCK_DISPLAY = 12
    START_SAMPLE = 13793785 + 0 * GSM_SYMB_RATE * OSR
    INDEX_ROUND = 0
    START_TIME = 1593491665807 

    round_count = 0
    found_signal = 0
    match_scan = 0
    
    # query to get first target round is the time start call
    target_info = SQLite_external.get_target_info_round(time=START_TIME)
    current_target_round = target_info["round"]
    target_info = SQLite_external.get_round_info(round=current_target_round)
    target_round = target_info[0]

    # query HoangAnh database to get call offset
    # query database to get monitor round 
    r = API.get_round_from_sample(sample=START_SAMPLE, index_round=INDEX_ROUND)
    round_entries= API.get_round_arfcns(round=r, index_round=INDEX_ROUND) 
    sample_offset = round_entries["round_time"]

    print("-"*110)
    while True:
        scanner_rounds = round_entries["entries"]
        _neighbor_arfcns = [info["arfcn"] for info in target_info[1:] if info["arfcn"] < 1024]
        print("|camping {:<4}\t{:<30}{}|".format(target_round["arfcn"], _neighbor_arfcns,
                datetime.datetime.fromtimestamp(target_round["time"]/1000))),
        block = 0
        try:
            arfcns = [int(entry.arfcn) for entry in scanner_rounds]
        except:
            arfcns = []

        for arfcn in arfcns:
            block += 1
            print("{:>3},".format(arfcn)),

        for i in range (block, MAX_BLOCK_DISPLAY):
            print("{:>3} ".format("")),

        # end of round
        print("|round:{:>5}|time: {}|offset at: {}|".format(entry.round, entry.timestamp, entry.sample_offset)),
        print("round: {}    found: {}   match: {}".format(round_count, found_signal, match_scan))
        print("-"*110)
        
        # static result update
        round_count += 1
        if target_round["arfcn"] in arfcns:
            found_signal += 1

        if len(arfcns) > 3 and target_round["arfcn"] in [arfcns[0], arfcns[1], arfcns[2]]:
            match_scan += 1
        elif len(arfcns) <= 3 and target_round["arfcn"] in arfcns:
            match_scan += 1

        # query next round from target log with time is key
        current_target_round += 1
        target_info = SQLite_external.get_round_info(round=current_target_round)
        target_round_next = target_info[0]
        sample_offset += int((target_round_next['time'] - target_round['time']) * (GSM_SYMB_RATE * OSR / 1000))
        r = API.get_round_from_sample(sample_offset, index_round=INDEX_ROUND)
        round_entries = API.get_round_arfcns(round=r, index_round=INDEX_ROUND)
        target_round = target_round_next
        
        if not scanner_rounds :
            break

    print("Number of round scan: {}".format(round_count))
    print("Number of signal found in scan list: {}".format(found_signal))
    print("Number of matching signal: {}".format(match_scan))
    print("End of program with error: {}".format(e))
    import traceback
    traceback.print_exc()

if __name__ == "__main__":
    interactive_print()
