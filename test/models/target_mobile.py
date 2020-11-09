from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class tbl_call_log(Base):
    __tablename__ = "tbl_call_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    round = Column(Integer)
    times = Column(BigInteger)
    phone = Column(String)

class tbl_log(Base):
    __tablename__ = "tbl_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    round = Column(Integer)
    arfcn = Column(Integer)
    bsic = Column(Integer)
    tmsi = Column(String)
    lac = Column(Integer)
    cid = Column(Integer)
    strength = Column(String)
    mnc = Column(String)
    mcc = Column(String)
    time = Column(BigInteger)
    ptime = Column(BigInteger)
    type = Column(String)

