from test.models.target_mobile import tbl_log
from test import session

from app.gsm_band import arfcn

def get_target_rounds_info(arfcn=None, round_limit=-1):
    entries = []
    if arfcn is None:
        return entries

    queries = session.query(tbl_log).filter(tbl_log.arfcn == arfcn)\
            .order_by(tbl_log.round.asc())
    
    if round_limit > 0:
        queries = queries.filter(tbl_log.round < round_limit)
    
    queries = queries.all()
    for round in queries:
        time = round.time if round.time > 0 else round.ptime 
        entries.append(tuple((round.strength, time, round.round)))

    return entries

def get_target_camping(round_limit=-1):
    queries = session.query(tbl_log).filter(tbl_log.type == "Cell")\
            .order_by(tbl_log.id.asc())
    
    if round_limit > 0:
        queries = queries.filter(tbl_log.round < round_limit)
    
    queries = queries.all()

    return [tuple((round.strength, round.time, round.arfcn)) for round in queries]

def get_database_mobile_arfcns(networks= ["VIETTEL"], bands=["GSM900", "DCS"]):
    queries = session.query(tbl_log.arfcn).distinct()
    _list_arfcns = [round[0] for round in queries.all()]
    arfcns = []
    for network in networks:
        _network_arfcn = arfcn.get_scan_arfcn(_list_arfcns, bands=bands, network=network)
        arfcns.extend(_network_arfcn)

    return arfcns
