from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.pool import NullPool

import logging
import config
config = config
#db = create_engine(config.SQLALCHEMY_DATABASE_URI, echo=False, poolclass=NullPool)
db = create_engine(config.MYSQL_DATABASE_URI, echo=False, poolclass=NullPool)

from app.models import *
Base.metadata.create_all(db)
#Session = sessionmaker(bind=db)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=True, bind=db))
#session = Session()
session = db_session()

logger = logging.getLogger()
logger.setLevel(logging.ERROR)
formatter = logging.Formatter('[%(name)s - %(levelname)s]: %(message)s')
ch = logging.StreamHandler()
#ch.setLevel(logging.ERROR)
ch.setFormatter(formatter)
logger.addHandler(ch)
