from app.models import neighbor_arfcn, tranx_arfcn, cell_info, scan_arfcn, scan_activity, decode_info, debug_static, decode_ranking
from app import session
from app import config
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

def get_tranx_arfcn_from_cell(cell_id):
    """cell_id:string -> entries:records"""
    entries = session.query(tranx_arfcn).join(cell_info).filter(tranx_arfcn.frame_number == \
            session.query(tranx_arfcn).filter(tranx_arfcn.cell_id == \
            cell_id).order_by(tranx_arfcn.timestamp.desc()).first().frame_number).all()
    return entries

def get_neighbor_arfcn_from_cell(cell_id):
    """cell_id:string -> entries:records"""
    entries = session.query(neighbor_arfcn).join(cell_info).filter(neighbor_arfcn.frame_number == \
            session.query(neighbor_arfcn).filter(neighbor_arfcn.cell_id == \
            cell_id).order_by(neighbor_arfcn.timestamp.desc()).first().frame_number).all()
    return entries   

def get_tranx_arfcn_from_mnc(mnc):
    entries = session.query(tranx_arfcn).join(cell_info).filter(cell_info.mnc == \
            mnc).filter(tranx_arfcn.frame_number == session.query(tranx_arfcn)\
            .order_by(neighbor_arfcn.timestamp.desc()).first().frame_number).all()
    return entries

def get_lastest_record_arfcn(arfcn):
    entry = session.query(scan_arfcn).filter(scan_arfcn.arfcn == arfcn).order_by(scan_arfcn.id.desc()).first()
    return entry

def get_last_scan_round():
    entry = session.query(scan_activity).order_by(scan_activity.id.desc()).first()
    if entry != None:
        return entry.last_round
    return 1

def get_last_scan_offset():
    entry = session.query(scan_activity).order_by(scan_activity.id.desc()).first()
    if entry != None and entry.continues == True:
        return entry.sample_offset
    return 0

def get_round_lastest():
    round = session.query(scan_arfcn).order_by(scan_arfcn.round.desc()).first()
    return round.round

def get_round_entries(round, timevalid=60, index_round=0):
    time_window = timevalid * (1625000 * 2 / 6)
    time = -1
    entries = []
    try:
        round_time = session.query(scan_arfcn.sample_offset).filter(scan_arfcn.round <= round)\
                .filter(scan_arfcn.index_round==index_round).order_by(scan_arfcn.round.desc()).first()
        query = session.query(cell_info).filter((cell_info.stop_time > round_time[0]-time_window) | (cell_info.stop_time == -1)).filter(cell_info.index_round==index_round)
        entries = query.all()
        logger.info("[DATABASE]get arfcns {} from round {}".format([entry.cell_arfcn for entry in entries], round))
        time = round_time[0]

    except Exception as e:
        session.rollback()
        logger.error("[Error]Catch exception: {} roll back".format(e))

    return {"round_time": time, "entries": entries}

def get_neighbor_arfcn_from_arfcn(arfcn):
    entries = []
    try:
        arfcn_tables = session.query(neighbor_arfcn).filter(neighbor_arfcn.current_arfcn == arfcn)
        entries = arfcn_tables.filter(neighbor_arfcn.frame_number == arfcn_tables.order_by(neighbor_arfcn.timestamp.desc()).first().frame_number).all()
    except Exception as e:
        session.rollback()
        logger.error("[Error]Catch exception: {} roll back".format(e))
    return entries

def get_round_from_sample(sample=0, index_round=0):
    entry = session.query(scan_arfcn).filter(scan_arfcn.index_round == index_round)\
            .filter(scan_arfcn.sample_offset <= sample).order_by(scan_arfcn.timestamp.desc()).first()
    if entry is None:
        entry = session.query(scan_arfcn).filter(scan_arfcn.index_round == index_round)\
                .order_by(scan_arfcn.timestamp.asc()).first()
    return entry.round

def get_round_from_time(time=0):
    entry = session.query(scan_arfcn).filter(scan_arfcn.timestamp < time).order_by(scan_arfcn.timestamp.desc()).first()
    if entry is None:
        entry = session.query(scan_arfcn).order_by(scan_arfcn.timestamp.asc()).first()
    return entry.round

def get_start_offset():
    start = 0
    if config.offset:
        start = config.offset[0]
    if start < 0:
        raise ValueError('Terminated !!! Invalid input')
    return start

def get_stop_offset():
    stop = 0
    if config.offset:
        stop = config.offset[1]
    if stop < 0:
        raise ValueError('Terminated !!! Invalid input')
    return stop

def get_scanning_mode():
    if config.mode:
        return config.mode
    return None

def get_rounds_info(arfcn=None, start_offset=0, stop_offset=-1, attr="rxlev"):
    entries = []
    if arfcn is None:
        return entries
    try: 
        if stop_offset == -1:
            entries = session.query(scan_arfcn).filter(scan_arfcn.arfcn == arfcn)\
                    .order_by(scan_arfcn.sample_offset.asc()).all()
        elif start_offset < stop_offset: 
            entries = session.query(scan_arfcn).filter(scan_arfcn.sample_offset > start_offset)\
                    .filter(scan_arfcn.sample_offset < stop_offset).filter(scan_arfcn.arfcn == arfcn)\
                    .order_by(scan_arfcn.sample_offset.asc()).all()
    except Exception as e:
        session.rollback()
        logger.error("[Error]Catch exception: {} roll back".format(e))

    if attr == "rxlev":
        return [tuple((entry.average_pwr, entry.sample_offset, entry.round)) for entry in entries]
    elif attr == "snr":
        return [tuple((entry.snr_avg_level, entry.sample_offset, entry.round)) for entry in entries]
    elif attr == "ber":
        return [tuple((entry.ber_avg_level, entry.sample_offset, entry.round)) for entry in entries]
    else:
        return []

def get_rounds_rxlev_info(arfcn=None, start_offset=0, stop_offset=-1, nlimit=-1, index_round=0):
    entries = []
    if arfcn is None:
        return entries
    try:
        query = session.query(scan_arfcn).filter(scan_arfcn.arfcn == arfcn)\
                .filter(scan_arfcn.index_round == index_round)\
                .order_by(scan_arfcn.sample_offset.asc())
        if stop_offset == -1:
            query = query
        if start_offset < stop_offset: 
            query = query.filter(scan_arfcn.sample_offset <= stop_offset)\
                    .filter(scan_arfcn.sample_offset > start_offset) 
        if nlimit > 0:
            query = query.limit(nlimit)
        entries = query.all()

    except Exception as e:
        session.rollback()
        logger.error("Catch exception: {} roll back".format(e))
        entries = []

    return [tuple((entry.average_pwr, entry.sample_offset, entry.round)) for entry in entries]

def get_rounds_snr_info(arfcn=None, start_offset=0, stop_offset=-1, nlimit=-1, index_round=0):
    entries = []
    if arfcn is None:
        return entries
    try:
        query = session.query(scan_arfcn).filter(scan_arfcn.arfcn == arfcn)\
                .filter(scan_arfcn.index_round == index_round)\
                .order_by(scan_arfcn.sample_offset.asc())
        if stop_offset == -1:
            query = query
        if start_offset < stop_offset: 
            query = query.filter(scan_arfcn.sample_offset <= stop_offset)\
                    .filter(scan_arfcn.sample_offset > start_offset) 
        if nlimit > 0:
            query = query.limit(nlimit)
        entries = query.all()

    except Exception as e:
        session.rollback()
        logger.error("[Error]Catch exception: {} roll back".format(e))

    return [tuple((entry.snr_avg_level, entry.sample_offset, entry.round)) for entry in entries]

def get_rounds_ber_info(arfcn=None, start_offset=0, stop_offset=-1, nlimit=-1, index_round=0):
    entries = []
    if arfcn is None:
        return entries
    try:
        query = session.query(decode_info).filter(decode_info.arfcn == arfcn)\
                .order_by(decode_info.sample_offset.asc())
        if stop_offset == -1:
            query = query
        if start_offset < stop_offset: 
            query = query.filter(decode_info.sample_offset <= stop_offset)\
                    .filter(decode_info.sample_offset > start_offset) 
        if nlimit > 0:
            query = query.limit(nlimit)
        entries = query.all()

    except Exception as e:
        session.rollback()
        logger.error("[Error]Catch exception: {} roll back".format(e))

    return [tuple((entry.ber_ratio, entry.sample_offset)) for entry in entries]

def get_rounds_sample(start_offset=0, stop_offset=-1, index_round=0):
    entries = []
    query = session.query(scan_arfcn.round, scan_arfcn.sample_offset, scan_arfcn.index_round)\
            .filter(scan_arfcn.index_round == index_round)\
            .distinct(scan_arfcn.round, scan_arfcn.index_round)\
            #.order_by(scan_arfcn.id.asc())
    if start_offset < stop_offset: 
        query = query.filter(scan_arfcn.sample_offset > start_offset)\
                .filter(scan_arfcn.sample_offset <= stop_offset)\
    
    entries = query.all()
    return [tuple((entry.sample_offset, entry.round, entry.index_round)) for entry in entries]

def get_last_scan_state():
    state = {}
    scanner_info = session.query(scan_arfcn).order_by(scan_arfcn.id.desc()).first()

    if scanner_info:
        state.update({"last_scan_offset": scanner_info.sample_offset, 
            "last_scan_time": scanner_info.timestamp})

        query = session.query(scan_activity).order_by(scan_activity.id.desc())
        entry = query.first()
        if entry:
            logger.error("entry.activity {}, config.state {} setting {}"
                    .format(entry.activity, config.state, config.server_setting))

        if entry and entry.activity == "STOPPED" and str(config.server_setting["mode"]) == '1':
            logger.error("scanner restart after stopped")
            state.update({"activity": "NETWORK_CHANGE", "last_round": entry.last_round, "sample_offset_stop": entry.sample_offset, "capture_round": entry.index_round, "timestamp": entry.timestamp,})
        elif entry and entry.last_round >= scanner_info.round and entry.index_round == scanner_info.index_round:
            logger.error("apply state get from scan activity")
            state.update({"activity": entry.activity, "last_round": entry.last_round, "sample_offset_stop": entry.sample_offset, "capture_round": entry.index_round, "timestamp": entry.timestamp,})
        elif entry and (entry.last_round < scanner_info.round or entry.index_round != scanner_info.index_round):
            logger.error("apply state get from scan arfcn because current round not match last state of scan activity")
            # Scanner have running before but restart and doesnt push state entry to database, power outrage ??
            state.update({"activity": "POWER_OFF", "last_round": scanner_info.round, "sample_offset_stop": scanner_info.sample_offset, "capture_round": scanner_info.index_round, "timestamp": scanner_info.timestamp,})
        elif not entry:
            # Scanner have running before but restart and doesnt push state entry to database, power outrage ??
            # Restart at next round index 
            logger.error("scan activity is empty apply state get from scan arfcn ")
            state.update({"activity": "POWER_OFF", "last_round": scanner_info.round, "sample_offset_stop": scanner_info.sample_offset, "capture_round": scanner_info.index_round, "timestamp": scanner_info.timestamp,})

    elif not scanner_info:
        state = {"capture_round": -1}

    logger.debug("get scan arfcn state {}".format(state))
    return state

def get_last_cell_index():
    query = session.query(cell_info).order_by(cell_info.cell_select_info.desc())

    entry = query.first()
    if entry:
        return entry.cell_select_info
    return 0

def get_scanner_activity(activity=None):
    query = session.query(scan_activity)
    if activity:
        query = query.filter(scan_activity.activity == activity)
    results = query.all()
    activities = []
    for result in results:
        _activity = {
                "activity":    result.activity,
                "timestamp":    result.timestamp,
                "last_round":   result.last_round,
                "sample_offset":    result.sample_offset,
                "index_round":  result.index_round,
                }
        activities.append(_activity)

    return activities

def get_cells_info(index_round=0):
    try:
        query = session.query(cell_info.cell_arfcn, cell_info.cell_id, cell_info.lac)\
                .filter(cell_info.index_round==index_round)\
                .distinct(cell_info.cell_arfcn, cell_info.cell_id, cell_info.lac)
        entries = query.all()
        logger.info("Get arfcns {} from round {}".format([entry.cell_arfcn for entry in entries], round))

    except Exception as e:
        session.rollback()
        logger.error("Catch exception: {} roll back".format(e))
    return [{"arfcn": entry.cell_arfcn, "cell_id": entry.cell_id, "lac": entry.lac,} for entry in entries]

def get_round_arfcns(round, index_round=0):
    try:
        query = session.query(scan_arfcn).filter(scan_arfcn.index_round==index_round)\
                .filter(scan_arfcn.round==round)
        entries = query.all()
        time = entries[0].sample_offset

    except Exception as e:
        session.rollback()
        logger.error("Catch exception: {} roll back".format(e))

    return {"round_time": time, "entries": entries}

def empty_database():
    session.query(neighbor_arfcn).delete()
    session.query(tranx_arfcn).delete()
    session.query(cell_info).delete()
    session.query(scan_arfcn).delete()
    session.query(scan_activity).delete()
    session.query(decode_info).delete()
    session.query(debug_static).delete()
    session.query(decode_ranking).delete()
    session.commit()
