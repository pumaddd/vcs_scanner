import logging 

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

VIETNAM_GSM900_UP = {"VIETNAMOBILE": (880, 890), "VINAPHONE": (890, 898.5), 
        "VIETTEL": (898.5, 906.7), "MOBIFONE": (906.7, 914.9)}
VIETNAM_GSM900_DOWN = {"VIETNAMOBILE": (925, 935), "VINAPHONE": (935, 943.5), 
        "VIETTEL": (943.5, 951.7), "MOBIFONE": (951.7, 959.9)}

VIETNAM_DCS_UP = {"VINAPHONE": (1710, 1730), "MOBIFONE": (1730, 1750), 
        "VIETTEL": (1750, 1770), "GMOBILE": (1770, 1785)}
VIETNAM_DCS_DOWN = {"VINAPHONE": (1805, 1825), "MOBIFONE": (1825, 1845), 
        "VIETTEL": (1845, 1865), "GMOBILE": (1865, 1880)}

VIETNAM_GSM900 = {"VINAPHONE": (1, 42), "VIETTEL": (43, 83), "MOBIFONE": (84, 124)}
VIETNAM_DCS1800 = {"VINAPHONE": (512, 611), "MOBIFONE": (612, 711), 
            "VIETTEL": (712, 811), "GMOBILE": (812, 885)}

class arfcn():

    @staticmethod
    def get_neighbor_arfcn_sysinfo(sysinfo):
        arfcns = []
        
        if sysinfo.si2_msg:
            arfcns.extend([int(channel) for channel in sysinfo.si2_msg['neighbor_arfcn'] if not int(channel) in arfcns])
            # for channel in sysinfo.si2_msg['neighbor_arfcn']:
            #     if not channel in arfcns:
            #         arfcns.append(int(channel))
        
        if sysinfo.si2ter_msg:
            arfcns.extend([int(channel) for channel in sysinfo.si2ter_msg['neighbor_arfcn'] if not int(channel) in arfcns])
            # for channel in sysinfo.si2ter_msg['neighbor_arfcn']:
            #     if not channel in arfcns:
            #         arfcns.append(int(channel))

        return arfcns
    
    @staticmethod
    def get_scan_arfcn(arfcns_list, bands=["DCS"], network="VIETTEL"):
        arfcns = []
        if type(arfcns_list) != list:
            return arfcns

        if "DCS" in bands and VIETNAM_DCS1800.get(network):
            arfcn_range = VIETNAM_DCS1800.get(network)
            for channel in arfcns_list:
                if channel >= arfcn_range[0] and channel <= arfcn_range[1]:
                    arfcns.append(channel) 
        if "GSM900" in bands and VIETNAM_GSM900.get(network):
            arfcn_range = VIETNAM_GSM900.get(network)
            for channel in arfcns_list:
                if channel >= arfcn_range[0] and channel <= arfcn_range[1]:
                    arfcns.append(channel) 
        logger.info("Arfcn range {} channel list {} band {}".format(arfcns, arfcns_list, bands)) 
        return arfcns


    @staticmethod
    def get_arfcn_ranges(bands=["DCS"], network="VIETTEL"):
        """return tuple of start and end arfcn in provider network band"""
        arfcns = []
        for band in bands:
            if band == "DCS" and VIETNAM_DCS1800.get(network):
                arfcns.append(VIETNAM_DCS1800.get(network))
            if band == "GSM900" and VIETNAM_GSM900.get(network):
                arfcns.append(VIETNAM_GSM900.get(network))

        return arfcns

    @staticmethod
    def check_arfcn_in_band(arfcn, bands=["DCS"], network="VIETTEL"):
        band_range = []
        for band in bands:
            if band == "DCS":
                band_range = VIETNAM_DCS1800.get(network)
            elif band == "GSM900":
                band_range = VIETNAM_GSM900.get(network)

            if arfcn >= band_range[0] and arfcn <= band_range[1]:
                return True
        return False

    @staticmethod
    def get_fc_bandwidth(fc):
        from app.modules.sources.file_source import source

        bandwidth = 0
        for network_900 in VIETNAM_GSM900_DOWN:
            arfcn_range = VIETNAM_GSM900_DOWN.get(network_900)
            if fc / 1e6 >= arfcn_range[0] and fc / 1e6  <= arfcn_range[1]:
                bandwidth =  source.FC_BANDWIDTH_900
                break

        for network_1800 in VIETNAM_DCS_DOWN:
            arfcn_range = VIETNAM_DCS_DOWN.get(network_1800)
            if fc / 1e6 >= arfcn_range[0] and fc / 1e6  <= arfcn_range[1]:
                bandwidth = source.FC_BANDWIDTH_1800
                break
        
        logger.info("Frequency {} in band {}".format(fc, bandwidth))
        return bandwidth
