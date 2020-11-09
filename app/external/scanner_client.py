import xmlrpclib
from multiprocessing import pool

class ScannerHandler():
    HOST = "localhost"
    PORT = 8000
    RPC_URI = "http://{}:{}".format(HOST, PORT)

    def __init__(self):
        self.rpc_service = xmlrpclib.ServerProxy(self.RPC_URI)
        self.threadpool = pool.ThreadPool(processes=5)
        self.result_list = []
    
   
    def log_result(self, result):
        # This is called whenever foo_pool(i) returns a result.
        # result_list is modified only by the main process, not the pool workers.
        self.result_list.append(result)

    def async_request_round(self, round=0):
        #threadpool = pool.ThreadPool(processes=5)
        self.threadpool.apply_async(request_round, args = (round, ), callback = self.log_result)
        #self.threadpool.close()
        #self.threadpool.join()
        print(self.result_list)

def request_round(round=0):
    result = []
    print('DEBUG args ')
    rpc_service = xmlrpclib.ServerProxy(ScannerHandler.RPC_URI)
    try:
        result = rpc_service.trigger_ranking(round)
        print("[SCANNER CLIENT]request round {} from server".format(ScannerHandler.RPC_URI))
    except Exception as e:
        print("[SCANNER CLIENT]fail to request server")
        print(e)
        pass

    return result

