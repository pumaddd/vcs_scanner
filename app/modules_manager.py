from gnuradio import gr
from app.modules.source import BaseSource
from app import config
from os import listdir
import os
import imp
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class sdr_source(gr.hier_block2):
    source_path = os.path.join(config.basedir, "app/modules/sources")
    python_path = source_path.replace("/", ".")
    
    file_modules = [f[:-3] for f in listdir(source_path) if f.endswith(".py")]

    modules_imported = []
    for file_module in file_modules:
        if file_module == "__init__":
            continue
        module = imp.load_source(file_module,  os.path.join(source_path, file_module + '.py'))
        modules_imported.append(module)

    def __init__(self, device="FILE_DEVICE", **kw):

        devices_enable = sdr_source.probe_connected_devices()
        logger.info("List device enable {}".format(devices_enable))
        module = None
        for module in self.modules_imported:
            if module.source.__info__['device'] == device and device in devices_enable:
                #TODO found module to export
                logger.info("Select device {}".format(module.source.__info__['device']))
                break

        if module == None:
            self.__class__ = BaseSource
            logger.error("Not found device")

        else:
            self.__class__ = module.source
        self.__init__(**kw)
        self.source_init()  
    
    @staticmethod
    def get_source_module(device="FILE_DEVICE"):
        module = None
        logger.info("Get device {}".format(device))
        for module in sdr_source.modules_imported:
            if module.source.__info__['device'] == device:
                module = module
                logger.info("Get info from module:\n{}".format(module.source.__info__))
                break

        return module.source

    @staticmethod
    def probe_connected_devices():
        connected_devices = []
        for module in sdr_source.modules_imported: 
            if module.source.probe():
                module_meta = module.source.__info__.copy()
                connected_devices.append(module_meta)

        return [device['device'] for device in connected_devices]

    @staticmethod
    def get_modules_info():
        modules_info = []
        for module in sdr_source.modules_imported:
            logger.info("Get source {} info".format(module.source.__info__['device']))
            info = module.source.get_source_info()
            if info:
                modules_info.extend(info)

        return modules_info
