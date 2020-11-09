from test import config
from os import listdir
import os
import imp

class unit_test(object):
    modules_path = os.path.join(config.basedir, "test/unit_tests")
    file_modules = [f[:-3] for f in listdir(modules_path) if f.endswith(".py")]

    modules_imported = []
    for file_module in file_modules:
        if file_module == "__init__":
            continue
        module = imp.load_source(file_module,  os.path.join(modules_path, file_module + '.py'))
        modules_imported.append(module)

    def __init__(self, module_name="ranking_module", **kw):

        print("[MODULE MANAGER]List unit test module aviable {}".format(self.modules_imported))
        module = None
        for module in self.modules_imported:
            if module.__info__['name'] == module_name:
                #TODO found module to export
                print("[MODULE MANAGER]Select test module {}".format(module.__info__['name']))
                break

        if module == None:
            print("[MODULE MANAGER]Module not found")
            return None

        else:
            self.__class__ = module.TestModule
            print("[MODULE MANAGER]Found module {}".format(module))
        self.__init__(**kw)

