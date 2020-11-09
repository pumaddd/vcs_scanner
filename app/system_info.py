import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class system_info():
    def __init__(self, arfcn=None):
        self.arfcn = arfcn
        self.si1_msg = {}
        self.si2_msg = {}
        self.si2ter_msg = {}
        self.si3_msg = {}
        self.si4_msg = {}
        self.si_valid = False
        self.sp_valid = False
        self.sp_cbq = -1
        self.sp_cro = -1
        self.sp_pt = -1
        self.sp_to = -1
        self.mask = 0

    def si_reset(self, arfcn):
        self.arfcn = arfcn
        self.si1_msg = {}
        self.si2_msg = {}
        self.si2ter_msg = {}
        self.si3_msg = {}
        self.si4_msg = {}
        self.si_valid = False
        self.sp_valid = False
        self.sp_cbq = -1
        self.sp_cro = -1
        self.sp_pt = -1
        self.sp_to = -1
    
    def data_copy(self, si):
        if si.__class__.__name__ == 'system_info':
            self.arfcn = si.arfcn
            self.si1_msg = si.si1_msg
            self.si2_msg = si.si2_msg
            self.si2ter_msg = si.si2ter_msg
            self.si3_msg = si.si3_msg
            self.si4_msg = si.si4_msg
            self.si_valid = si.si_valid
            self.sp_valid = si.sp_valid
            self.mask = si.mask

            return self
        return None

    def pretty_print(self):
        logger.info("[DEBUG SYSTEM INFO]arfcn {} pretty print system information".format(self.arfcn))
        logger.info("SYSTEM INFORMATION 1 : {}".format(self.si1_msg))
        logger.info("SYSTEM INFORMATION 2 : {}".format(self.si2_msg))
        logger.info("SYSTEM INFORMATION 3 : {}".format(self.si3_msg))
        logger.info("SYSTEM INFORMATION 4 : {}".format(self.si4_msg))
        logger.info("SYSTEM INFORMATION 2 EXTEND: {}".format(self.si2ter_msg))

