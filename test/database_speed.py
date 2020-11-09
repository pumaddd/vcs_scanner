from app.models import neighbor_arfcn, tranx_arfcn, cell_info, scan_arfcn
from app import session
from datetime import datetime

def sql_test_speed(round=100000):
    time_start = datetime.now()
    for i in range(round):
        scan_commit = scan_arfcn(
                   arfcn = -1,
                   scan_level = -1,
                   rank = -1,
                   round = i, 
                   average_pwr = 0,
                   pkt_number = 0,
                   sample_offset = 0,
                )
        session.add(scan_commit)

    session.commit()
    time_finish = datetime.now()
    print("benchmark time insert database {}".format(time_finish - time_start))
