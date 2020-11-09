from app.models import neighbor_arfcn, tranx_arfcn, cell_info, scan_arfcn, scan_activity
from app import session
from app import config
from grgsm import grd_config

import sqlite3
import os
import MySQLdb
import logging

MYSQL_CONFIG = {
'user': config.MYSQL_CONFIG["user"],
'passwd': config.MYSQL_CONFIG["password"],
'db': 'file.db',
'host': config.MYSQL_CONFIG["host"],
'port': int(config.MYSQL_CONFIG["port"]),
}
import logging

config = grd_config()
TABLENAME = config.get_table_name()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_file_source(uplink=True):
    """return paths of files source from database with uplink flag set to control type receive"""

    #conn = mysql.connector.connect(**MYSQL_CONFIG)
    conn = MySQLdb.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    if uplink == True:
        file_query = "select filepath from {} where status = 'Up'".format(TABLENAME)
    if uplink == False:
        file_query = "select filepath from {} where status = 'Down'".format(TABLENAME)

    cursor.execute(file_query)

    paths = cursor.fetchall()
    conn.close()    

    return [str(path[0]) for path in paths]

def get_file_info_dcs(capture_round=0):
    """return frequency center and bandwidth from database """
    conn = MySQLdb.connect(**MYSQL_CONFIG)
    #conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    query = "SELECT DISTINCT fc, bwidth FROM {} WHERE fc > 1800000000 and index_round = {}".format(TABLENAME, capture_round)
    try:
        cursor.execute(query)
        info = cursor.fetchall()
    except:
        pass
    conn.close()    

    return info

def get_file_info_gsm(capture_round=0):
    """return frequency center and bandwidth from database """
    conn = MySQLdb.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    query = "SELECT DISTINCT fc, bwidth FROM {} WHERE fc > 900000000 and fc < 1000000000 and index_round = {}".format(TABLENAME, capture_round)
    try:
        cursor.execute(query)
        info = cursor.fetchall()
    except:
        pass
    conn.close()    

    return info

def check_network_info(capture_round=0):
    conn = MySQLdb.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    query = "SELECT DISTINCT fc, bwidth FROM {} WHERE index_round = {}".format(TABLENAME, capture_round)
    cursor.execute(query)
    info = cursor.fetchall()
    conn.close()    
    if len(info) > 0:
        return True

    return False

def get_capture_info():
    conn = MySQLdb.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    query = "SELECT index_round FROM {} where deleted = 0 order by ID desc limit 1".format(TABLENAME)
    try:
        cursor.execute(query)
        info = cursor.fetchone()
    except:
        pass
    conn.close()    
    if len(info) > 0:
        return {"capture_round": info[0]}

    return None

def get_network_from_capture_round(capture_round):
    conn = MySQLdb.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    query = "SELECT DISTINCT operator FROM {} WHERE index_round = {}".format(TABLENAME, capture_round)
    cursor.execute(query)
    info = cursor.fetchone()
    conn.close()    
    if info:
        return info[0]

    return None

def get_rounds_ber_info(arfcn=None, start_offset=0, stop_offset=-1, nlimit=-1, index_round=0):
    entries = []
    if arfcn is None:
        return entries

    DECODE_CONFIG = MYSQL_CONFIG.copy()
    DECODE_CONFIG["db"] = "app_state"

    conn = MySQLdb.connect(**DECODE_CONFIG)
    cursor = conn.cursor()
    if start_offset < stop_offset:
        query = "SELECT ber_ratio, sample_offset FROM `decode_info` WHERE arfcn = {} and sample_offset < {} and sample_offset > {} and index_round = {} order by sample_offset asc".format(arfcn, stop_offset, start_offset, index_round)
    else :
        query = "SELECT ber_ratio, sample_offset FROM `decode_info` where arfcn = {} and index_round = {} order by sample_offset asc ".format(arfcn, index_round)

    cursor.execute(query)
    info = cursor.fetchall()
    conn.close()
    for row in info:
        entries.append((row[0], row[1]))

    return entries[-nlimit:]

