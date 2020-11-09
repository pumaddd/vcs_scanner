from test import session
from test.models.round_models import rounds_static 
import re
import sys
import os

START_CHANNEL_PATTERN = "[INFO]----round"
re_start_channel = re.compile("\[INFO\]----round (\d*) tuning  channel: (\d*) ---- ([\d\s\-\:\.]*) searching state \d")
re_channel_offset = re.compile("\[GSM BURST\]set to new cell allocation (\d*) and reset state at burst (\d*) -------- at time (\d*)")
re_resync_search = re.compile("\[GSM BURST\]resync trigger at (\d*) lost sch search -------- at sample (\d*)")
re_resync_sync = re.compile("\[GSM BURST\]resync trigger at (\d*) lost synchronize at time (\d*)")
re_sync = re.compile("\[GSM BURST\]synch to channel (\d*) -------- at time (\d*)")
re_miss_signal = re.compile("\[SIGNAL HANDLER\]handler signal not found message from receiver")
re_new_round = re.compile("\[GSM SCANNER\]Current neighbor list")
re_out_dsp = re.compile("\[SCANNER DEBUG\]out of signal processing block: (\d*)")
re_end_round = re.compile("\[SCANNER DEBUG\]end of scan round at sample offset: (\d*)")
re_debug_fcch_miss = re.compile("\[RECEIVER DEBUG\]not found fcch at burst (\d*) burst - (\d*) sample")
re_debug_fcch_found = re.compile("\[RECEIVER DEBUG\]found fcch burst at burst (\d*) - (\d*) sample")

def parse_log(file_log='log.file'):
    if os.path.exists(file_log):
        f = open(file_log)
    else:
        f = sys.stdin

    text = f.read()
    start_pos = text.find(START_CHANNEL_PATTERN)
    while True:
        text = text[start_pos:]
        start_pos = text.find(START_CHANNEL_PATTERN, 1)
        channel_context = text[:start_pos]
        process_context_channel(text=channel_context)
        if not len(channel_context):
            break

def process_context_channel(text=''):
    start_info = re.search(re_start_channel, text)
    offset_info = re.search(re_channel_offset, text)
    channel_signal = re.search(re_miss_signal, text)
    new_round = re.search(re_new_round, text)
    resync_searchs = re.findall(re_resync_search, text)
    resync_syncs = re.findall(re_resync_sync, text)
    resyncs = re.findall(re_sync, text)
    out_dsp = re.search(re_out_dsp, text)
    end_round = re.search(re_end_round, text)
    debug_fcch_miss = re.search(re_debug_fcch_miss, text)
    debug_fcch_found = re.findall(re_debug_fcch_found, text)

    print("[TEST PARSER]process text result: {}".format(len(text)))
    round_info = rounds_static() 

    if start_info:
        print("Start info: {}".format(start_info.groups()))
        round_info.arfcn = start_info.group(2)
        round_info.timestamp = start_info.group(3)[11:]

    if offset_info:
        print("Offset info: {}".format(offset_info.groups()))
        round_info.sample_offset = offset_info.group(3)

    if channel_signal:
        round_info.signal = "No"
    else:
        round_info.signal = "Yes"

    if out_dsp:
        round_info.end_dsp = out_dsp.group(1)

    if end_round:
        round_info.end_round = end_round.group(1)

    if debug_fcch_miss:
        round_info.fcch_miss = debug_fcch_miss.group(2)

    if resyncs:
        round_info.sync_time = resyncs[-1][1]

    if debug_fcch_found:
        round_info.found_time = debug_fcch_found[-1][1]
        round_info.burst_count = debug_fcch_found[-1][0]

    for search in resync_searchs:
        print("Resync lost sch seach: {}".format(search))
    for search in resync_syncs:
        print("Resync lost synchronize: {}".format(search))
    for search in resyncs:
        print("Resync channel: {}".format(search))
    
    session.add(round_info)
    session.commit()
    
    if new_round:
        print("-"*10 + "New round" + "-"*10)
        blank = rounds_static()
        blank.id = None
        session.add(blank)
        session.commit()


