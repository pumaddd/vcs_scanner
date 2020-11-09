import os

basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_TARGET_DATABASE = 'sqlite:///{}?check_same_thread=False'\
        .format(os.path.join(basedir, 'test/data/target_mobile.db'))
