from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
import logging
import test_config
import app
import test

config = test_config
db = create_engine(config.SQLALCHEMY_TARGET_DATABASE, echo=False)

from test.models.target_mobile import *
Base.metadata.create_all(db)
Session = sessionmaker(bind=db)
session = Session()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
#formatter = logging.Formatter('[%(name)s - %(levelname)s]: %(message)s')
formatter = logging.Formatter('[%(levelname)s]: %(message)s')
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)
