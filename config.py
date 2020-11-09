import os
basedir = os.path.abspath(os.path.dirname(__file__))
config_path = '/etc/data'

SQLALCHEMY_TRACK_MODIFICATIONS = False

SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    'sqlite:///{}?check_same_thread=False'.format(os.path.join(basedir, 'app.db'))

SQLALCHEMY_TEST_DATABASE_URI = 'sqlite:///{}?check_same_thread=False'\
        .format(os.path.join(basedir, 'test/data/app.db'))

LISTEN_PORT = {'SDRPLAY': "4729", 'USRP': "4829", 'FILE_DEVICE': "4929"}

MYSQL_CONFIG = {
    'user': 'netsharing',
    'password': '12345678',
    #'host': '127.0.0.1',
    'host': '172.17.0.1',
    'port': '3306',
    'raise_on_warnings': True
}

MYSQL_DATABASE_URI =  os.environ.get('DATABASE_URL') or \
        'mysql://{}:{}@{}:{}/{}'.format(MYSQL_CONFIG["user"], MYSQL_CONFIG["password"], MYSQL_CONFIG["host"], MYSQL_CONFIG["port"], 'app.db', echo=True)

