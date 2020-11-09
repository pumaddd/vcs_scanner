from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class rounds_static(Base):
    __tablename__ = "rounds_static"

    id = Column(Integer, primary_key=True, autoincrement=True)
    arfcn = Column(Integer)
    timestamp = Column(String)
    sample_offset = Column(BigInteger)
    signal = Column(String)
    fcch_miss = Column(BigInteger)
    end_dsp = Column(BigInteger)
    end_round = Column(BigInteger)
    found_time = Column(BigInteger)
    burst_count = Column(Integer)
    sync_time = Column(BigInteger)

