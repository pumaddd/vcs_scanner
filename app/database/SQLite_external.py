from app.models import neighbor_arfcn, tranx_arfcn, cell_info, scan_arfcn, scan_activity
from app import session
from app import config
import mysql.connector
import sqlite3
import os

def get_round_lastest():
    arfcns = []
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    c.execute("select arfcn from scan_arfcn where round = \
            (select round from scan_arfcn order by id desc limit 1)")
    rows = c.fetchall()
    print("main signal cell: "),
    for row in rows:
        print(row[0])
        arfcn = row[0]
        arfcns.append(arfcn)
        c.execute("select neighbor_arfcn from neighbor_arfcn where current_arfcn = {} and frame_number = \
                (select frame_number from neighbor_arfcn where current_arfcn = {} \
                order by id desc limit 1)".format(arfcn, arfcn))
        neighbors = c.fetchall()
        for neighbor in neighbors:
            if not neighbor[0] in arfcns:
                arfcns.append(neighbor[0])
    conn.close()
    print arfcns

def get_tranx_arfcn_from_cell(cell_id):
    arfcns = []
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    c.execute("select tranx_arfcn from tranx_arfcn where cell_id = {} and frame_number = \
            (select frame_number from tranx_arfcn where cell_id = {} \
            order by id desc limit 1)".format(cell_id, cell_id))
    tranxs = c.fetchall()
    conn.close()    

    return [tranx[0] for tranx in tranxs]

def get_tranx_arfcn_from_arfcn(arfcn):
    arfcns = []
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    c.execute("select tranx_arfcn from tranx_arfcn where current_arfcn = {} and frame_number = \
            (select frame_number from tranx_arfcn where current_arfcn = {} \
            order by id desc limit 1)".format(arfcn, arfcn))
    tranxs = c.fetchall()
    print(tranxs)
    conn.close()    

    return [tranx[0] for tranx in tranxs]

def get_file_source(uplink=True):
    """return paths of files source from database with uplink flag set to control type receive"""
    from app.modules.sources.file_source import source
    paths = []
    conn = sqlite3.connect(os.path.join(source.SOURCE_DATABASE, "file.db"))
    c = conn.cursor()
    if uplink == True:
        c.execute("select filepath from FileInfo where status = 'Up'")
    if uplink == False:
        c.execute("select filepath from FileInfo where status = 'Down'")

    paths = c.fetchall()
    conn.close()    

    return [str(path[0]) for path in paths]

def get_target_camp_arfcn(time=0):
    """return camping arfcn from logged database"""
    conn = sqlite3.connect("target_mobile.db")
    c = conn.cursor()
    c.execute("select * from tbl_log where time > {} order by time  asc limit 1".format(time))
    query = c.fetchone()
    conn.close()
    if query is None:
        return None
    
    channel = {
            'index':    query[0],
            'round':    query[1],
            'arfcn':    query[2],
            'bsic':     query[3],
            'tmsi':     query[4],
            'lac':      query[5],
            'cid':      query[6],
            'rssi':     int(query[7]),
            'mnc':      int(query[8]),
            'mcc':      int(query[9]),
            'time':     query[10],
            'type':     query[11]
            }

    return channel

def get_target_info_round(time=0):
    """return camping arfcn from logged database"""
    conn = sqlite3.connect("target_mobile.db")
    c = conn.cursor()
    _q = "select * from tbl_log where time >= {} and time <= {} and type = \'Cell\' limit 1"\
            .format(time - 1000, time + 1000)
    c.execute(_q)
    query = c.fetchone()
    conn.close()
    if query is None:
        return None
    
    channel = {
            'index':    query[0],
            'round':    query[1],
            'arfcn':    query[2],
            'bsic':     query[3],
            'tmsi':     query[4],
            'lac':      query[5],
            'cid':      query[6],
            'rssi':     int(query[7]),
            'mnc':      int(query[8]),
            'mcc':      int(query[9]),
            'time':     query[10],
            'type':     query[11]
            }

    return channel

def get_round_info(round):
    conn = sqlite3.connect("target_mobile.db")
    c = conn.cursor()
    _q = "select * from tbl_log where round = {}".format(round)
    c.execute(_q)
    results = c.fetchall()
    conn.close()
    if not results:
        return []
    round_arfcns = []
    for query in results:
        channel = {
                'index':    query[0],
                'round':    query[1],
                'arfcn':    query[2],
                'bsic':     query[3],
                'tmsi':     query[4],
                'lac':      query[5],
                'cid':      query[6],
                'rssi':     int(query[7]),
                'mnc':      int(query[8]) if query[8] else -1,
                'mcc':      int(query[9]) if query[9] else -1,
                'time':     query[10],
                'type':     query[12]
                }
        round_arfcns.append(channel)

    return round_arfcns

