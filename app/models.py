from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()
class cell_info(Base):
    __tablename__ = "cell_info"

    cell_select_info = Column(Integer, primary_key=True, autoincrement=False)
    cell_arfcn = Column(Integer)
    cell_id = Column(Integer)
    mcc = Column(Integer)
    mnc = Column(Integer)
    lac = Column(Integer)
    start_time = Column(BigInteger)
    stop_time = Column(BigInteger, default=-1)
    index_round = Column(Integer)

class neighbor_arfcn(Base):
    __tablename__ = "neighbor_arfcn"

    id = Column(Integer, primary_key=True, autoincrement=True)
    #cell_id = Column(Integer, ForeignKey("cell_info.cell_id"))
    cell_id = Column(String(32))
    current_arfcn = Column(Integer)
    neighbor_arfcn = Column(Integer)
    frame_number = Column(Integer)
    signal_dbm = Column(Integer)
    timestamp = Column(DateTime, default=datetime.datetime.now)
    sample_offset = Column(BigInteger)

class tranx_arfcn(Base):
    __tablename__ = "tranx_arfcn"

    id = Column(Integer, primary_key=True, autoincrement=True)
    current_arfcn = Column(Integer)
    tranx_arfcn = Column(Integer)
    timestamp = Column(DateTime, default=datetime.datetime.now)
    sample_offset = Column(BigInteger)
    #cell_select_info = Column(Integer, ForeignKey(cell_info.cell_select_info))
    cell_select_info = Column(Integer)

class scan_arfcn(Base):
    __tablename__ = "scan_arfcn"

    id = Column(Integer, primary_key=True, autoincrement=True)
    arfcn = Column(Integer)
    rank = Column(Integer)
    scan_level = Column(Integer)
    round = Column(Integer)
    average_pwr = Column(Integer)
    pkt_number = Column(Integer)
    timestamp = Column(DateTime, default=datetime.datetime.now)
    sample_offset = Column(BigInteger)
    sniff_time = Column(BigInteger)
    round_counter = Column(Integer)
    snr_avg_level = Column(Integer)
    rxlev_debug_criteria = Column(Integer)
    snr_debug_criteria = Column(Integer)
    #cell_select_info = Column(Integer, ForeignKey(cell_info.cell_select_info))
    cell_select_info = Column(Integer)
    index_round = Column(Integer)

class scan_activity(Base):
    __tablename__ = "scan_activity"

    id = Column(Integer, primary_key=True, autoincrement=True)
    activity = Column(String(32))
    timestamp = Column(DateTime, default=datetime.datetime.now)
    last_round = Column(Integer)
    sample_offset = Column(BigInteger)
    continues = Column(Boolean)
    index_round = Column(Integer)

class decode_ranking(Base):
    __tablename__ = "decode_ranking"

    id = Column(Integer, primary_key=True, autoincrement=True)
    arfcn = Column(Integer)
    rank = Column(Integer)
    round = Column(Integer)
    timestamp = Column(DateTime, default=datetime.datetime.now)
    rxlev_debug_criteria = Column(Integer)
    ber_debug_criteria = Column(Integer)
    snr_debug_criteria = Column(Integer)
    #cell_select_info = Column(Integer, ForeignKey(cell_info.cell_select_info))
    cell_select_info = Column(Integer)
    index_round = Column(Integer)

class decode_info(Base):
    __tablename__ = "decode_info"

    id = Column(Integer, primary_key=True, autoincrement=True)
    arfcn = Column(Integer)
    ber_ratio = Column(Float)
    frame_number = Column(Integer)
    sample_offset = Column(BigInteger)
    cell_id = Column(Integer)
    lac = Column(Integer)

class debug_static(Base):
    __tablename__ = "debug_static"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.datetime.now)
    round = Column(Integer)
    sample_offset = Column(BigInteger)
    capture_offset = Column(BigInteger)


