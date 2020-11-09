import re
from app import session
from app.system_info import system_info
from datetime import datetime

class bcch_process():
    ARFCN_RE = re.compile('List of ARFCNs = (.*)')
    TEMP_OFF_RE = re.compile('Temporary Offset')
    SYSTEM_INFO_1 = 0x19
    SYSTEM_INFO_2 = 0x1a
    SYSTEM_INFO_3 = 0x1b
    SYSTEM_INFO_4 = 0x1c
    SYSTEM_INFO_2QUATER = 0x07
    SYSTEM_INFO_2TER = 0x03
    SYSTEM_INFO_13 = 0x00

    @staticmethod
    def parse_sysinfo_1(pkt):
        data = {}
        if not 'gsm_a.ccch' in pkt:
            return data

        #get arfcn list of tranxmit channel
        search = re.search(bcch_process.ARFCN_RE, pkt['gsm_a.ccch'].gsm_a_rr_arfcn_list.showname)
        channels = [int(arfcn) for arfcn in search.group(1).split(' ')]
       
        data.update({'arfcn': channels})
        data.update({'current_arfcn': pkt['gsmtap'].arfcn})
        data.update({'frame_number': pkt['gsmtap'].frame_nr})
        data.update({'signal_dbm': pkt['gsmtap'].signal_dbm})
        return data

    @staticmethod
    def parse_sysinfo_2(pkt):
        data = {}
        if not 'gsm_a.ccch' in pkt:
            return data

        #get arfcn list of tranxmit channel
        search = re.search(bcch_process.ARFCN_RE, pkt['gsm_a.ccch'].gsm_a_rr_arfcn_list.showname)
        channels = [int(arfcn) for arfcn in search.group(1).split(' ')]

        data.update({'arfcn': channels})
        data.update({'current_arfcn': pkt['gsmtap'].arfcn})
        data.update({'frame_number': pkt['gsmtap'].frame_nr})
        data.update({'signal_dbm': pkt['gsmtap'].signal_dbm})
        return data

    @staticmethod
    def parse_sysinfo_3(pkt):
        data = {}
        if not 'gsm_a.ccch' in pkt:
            return data
        
        if pkt['gsm_a.ccch'].gsm_a_rr_selection_parameters.show == '1': 
            find_pos = pkt['gsm_a.ccch'].gsm_a_rr_temporary_offset.showname_value.find('dB')
            temp_offset = pkt['gsm_a.ccch'].gsm_a_rr_temporary_offset.showname_value[:find_pos - 1]
            find_pos = pkt['gsm_a.ccch'].gsm_a_rr_penalty_time.showname_value.find('s')
            penalty_time = pkt['gsm_a.ccch'].gsm_a_rr_penalty_time.showname_value[:find_pos-1]
            find_pos = pkt['gsm_a.ccch'].gsm_a_rr_cell_reselect_offset.showname_value.find('db')
            cell_resel_offset = pkt['gsm_a.ccch'].gsm_a_rr_cell_reselect_offset.showname_value[:find_pos - 1]
            cbq = pkt['gsm_a.ccch'].gsm_a_rr_cbq.showname_value
            data.update({'sp': {
                'sp_cbq': cbq, 
                'sp_to': temp_offset, 
                'sp_pt': penalty_time, 
                'sp_cro': cell_resel_offset
                }})

        data.update({'cell_id': pkt['gsm_a.ccch'].gsm_a_bssmap_cell_ci })
        data.update({'frame_number': pkt['gsmtap'].frame_nr})
        data.update({'signal_dbm': pkt['gsmtap'].signal_dbm})
        return data

    @staticmethod
    def parse_sysinfo_4(pkt):
        data = {}
        if not 'gsm_a.ccch' in pkt:
            return data
        
        if pkt['gsm_a.ccch'].gsm_a_rr_selection_parameters.show == '1': 
            find_pos = pkt['gsm_a.ccch'].gsm_a_rr_temporary_offset.showname_value.find('dB')
            temp_offset = pkt['gsm_a.ccch'].gsm_a_rr_temporary_offset.showname_value[:find_pos - 1]
            find_pos = pkt['gsm_a.ccch'].gsm_a_rr_penalty_time.showname_value.find('s')
            penalty_time = pkt['gsm_a.ccch'].gsm_a_rr_penalty_time.showname_value[:find_pos-1]
            find_pos = pkt['gsm_a.ccch'].gsm_a_rr_cell_reselect_offset.showname_value.find('db')
            cell_resel_offset = pkt['gsm_a.ccch'].gsm_a_rr_cell_reselect_offset.showname_value[:find_pos - 1]
            cbq = pkt['gsm_a.ccch'].gsm_a_rr_cbq.showname_value
            data.update({'sp': {
                'sp_cbq': cbq, 
                'sp_to': temp_offset, 
                'sp_pt': penalty_time, 
                'sp_cro': cell_resel_offset
                }})

        data.update({'frame_number': pkt['gsmtap'].frame_nr})
        data.update({'signal_dbm': pkt['gsmtap'].signal_dbm})
        data.update({
                    'mcc': pkt['gsm_a.ccch'].e212_lai_mcc ,
                    'mnc': pkt['gsm_a.ccch'].e212_lai_mnc ,
                    'lac': str(int(pkt['gsm_a.ccch'].gsm_a_lac, 16)) ,
                    })

        return data

    @staticmethod
    def parse_sysinfo_2ter(pkt):
        
        data = {}
        if not 'gsm_a.ccch' in pkt:
            return data

        #get arfcn list of tranxmit channel
        search = re.search(bcch_process.ARFCN_RE, pkt['gsm_a.ccch'].gsm_a_rr_arfcn_list.showname)
        channels = [int(arfcn) for arfcn in search.group(1).split(' ')]

        data.update({'arfcn': channels})
        data.update({'current_arfcn': pkt['gsmtap'].arfcn})
        data.update({'frame_number': pkt['gsmtap'].frame_nr})
        data.update({'signal_dbm': pkt['gsmtap'].signal_dbm})

        return data

    @staticmethod
    def parse_sysinfo_2quater(pkt):
        data = {}
        return data

    @staticmethod
    def parse_sysinfo_13(pkt):
        data = {}
        return data

class gsm_process():
    def __init__(self):
        self.cell_id = None
        self.lai = None
        self.current_arfcn = -1
        self.start_offset = -1
        self.stop_offset = -1
        self.neighbor_arfcns = None
        
        self.scan_complete = False
        self.cell_trail = []
        self.current_pkt = None
        self.current_state = None
        self.scan_complete_event = None
        
        self.snr_sum = 0 
        self.rxlev_sum = 0
        self.rxlev_count = 0
        self.systeminfo = system_info()

    def reset_channel(self, arfcn):
        self.cell_id = None
        self.lai = None
        self.current_arfcn = arfcn
        self.neighbor_arfcns = None
        
        self.scan_complete = False
        self.current_state = None
        self.scan_complete_event.clear()

        self.rxlev_sum = 0
        self.snr_sum = 0
        self.rxlev_count = 0
        self.systeminfo.si_reset(arfcn)

    def set_offset_start(self, offset):
        self.start_offset = offset
    
    def set_offset_stop(self, offset):
        self.stop_offset = offset
     
    def extract_cell_entry(self, cell_entry):
        if cell_entry.__class__.__name__ != 'CellNeighbor':
            print("[ERROR PARSER] is not cached cell neightbor struct".format(cell_entry))
            return
        print("[PACKET PROCESS]extract system information si2: {} ---- si2ter: {}"
            .format(cell_entry.system_info.si2_msg, cell_entry.system_info.si2ter_msg))
        self.systeminfo.data_copy(cell_entry.system_info)
 
    #process state machine
    def process_next_packet(self, pkt):
        if not 'gsmtap' in pkt:
            return
        
        if int(self.current_arfcn) != int(pkt['gsmtap'].arfcn):
            print("current tunner on {}, get packet {}, with frame number {} drop".format(self.current_arfcn, pkt['gsmtap'].arfcn, pkt['gsmtap'].frame_nr))
            return
        gsm_header = pkt['gsmtap']
        self.current_arfcn = pkt['gsmtap'].arfcn
        self.current_signal = pkt['gsmtap'].signal_dbm
        self.current_snr = int(pkt['gsmtap'].snr_db)
        print("DEBUG SRN {} packet snr {}".format(self.current_snr, pkt['gsmtap'].snr_db))
        self.rxlev_sum += int(self.current_signal)
        self.snr_sum += self.current_snr if self.current_snr > 0 else (255 + self.current_snr)

        self.rxlev_count += 1
        self.scan_complete = True
        if gsm_header.chan_type == '1':
            # process BCCH channel
            pkt_data = gsm_process.process_bcch_packet(pkt)
            if pkt_data == None:
                return

            print("systeminfo type: {} ------ capture time {}".format(pkt_data['type'], pkt_data['sniff_time']))
            if pkt_data['type'] == 'SYSTEM_INFO_1':
                self.systeminfo.si1_msg['tranx_arfcn'] = pkt_data['arfcn']
                self.systeminfo.si1_msg['frame_number'] = pkt_data['frame_number']
                self.systeminfo.si1_msg['signal_dbm'] = pkt_data['signal_dbm']
                self.systeminfo.si1_msg['sniff_time'] = pkt_data['sniff_time']
            
            elif pkt_data['type'] == 'SYSTEM_INFO_2':
                self.neighbor_arfcn = pkt_data['arfcn']
                self.systeminfo.si2_msg['neighbor_arfcn'] = pkt_data['arfcn']
                self.systeminfo.si2_msg['frame_number'] = pkt_data['frame_number']
                self.systeminfo.si2_msg['signal_dbm'] = pkt_data['signal_dbm']
                self.systeminfo.si2_msg['sniff_time'] = pkt_data['sniff_time']
             
            elif pkt_data['type'] == 'SYSTEM_INFO_2TER':
                self.neighbor_arfcn = pkt_data['arfcn']
                self.systeminfo.si2ter_msg['frame_number'] = pkt_data['frame_number']
                self.systeminfo.si2ter_msg['signal_dbm'] = pkt_data['signal_dbm']
                self.systeminfo.si2ter_msg['neighbor_arfcn'] = pkt_data['arfcn']
                self.systeminfo.si2ter_msg['sniff_time'] = pkt_data['sniff_time']
           
            elif pkt_data['type'] == 'SYSTEM_INFO_3':
                self.cell_id = pkt_data['cell_id']
                self.systeminfo.si3_msg['cell_id'] = pkt_data['cell_id']
                self.systeminfo.si3_msg['frame_number'] = pkt_data['frame_number']
                self.systeminfo.si3_msg['signal_dbm'] = pkt_data['signal_dbm']
                self.systeminfo.si3_msg['sniff_time'] = pkt_data['sniff_time']
                if 'sp' in pkt_data:
                    self.sp_valid = True
                    self.systeminfo.sp_cro = pkt_data['sp']['sp_cro']
                    self.systeminfo.sp_pt = pkt_data['sp']['sp_pt']
                    self.systeminfo.sp_to = pkt_data['sp']['sp_to']
                    self.systeminfo.sp_cbq = pkt_data['sp']['sp_cbq']
           
            elif pkt_data['type'] == 'SYSTEM_INFO_4':
                self.lai = pkt_data['mcc'] + pkt_data['mnc'] + pkt_data['lac']
                self.systeminfo.si4_msg['mcc'] = pkt_data['mcc']
                self.systeminfo.si4_msg['mnc'] = pkt_data['mnc']
                self.systeminfo.si4_msg['lac'] = pkt_data['lac']
                self.systeminfo.si4_msg['frame_number'] = pkt_data['frame_number']
                self.systeminfo.si4_msg['signal_dbm'] = pkt_data['signal_dbm']
                self.systeminfo.si4_msg['sniff_time'] = pkt_data['sniff_time']
                if 'sp' in pkt_data:
                    self.sp_valid = True
                    self.systeminfo.sp_cro = pkt_data['sp']['sp_cro']
                    self.systeminfo.sp_pt = pkt_data['sp']['sp_pt']
                    self.systeminfo.sp_to = pkt_data['sp']['sp_to']
                    self.systeminfo.sp_cbq = pkt_data['sp']['sp_cbq']
   
            # commit cell identify to database when have enough system information	
            if self.systeminfo.si1_msg and self.systeminfo.si2_msg and self.systeminfo.si2ter_msg and\
                self.systeminfo.si3_msg and self.systeminfo.si4_msg:
                
                self.systeminfo.si_valid = True
                #check cell identify and commit to database when meet new cell
                if len(self.cell_trail) == 0 or self.cell_id != self.cell_trail[-1]:
                    self.cell_trail.append(self.cell_id)
                print("[PACKET PROCESS]receive system infomation, send signal to terminate channel scan")
                # signal scan comple found signal channel and continue 
                self.scan_complete = True
                self.scan_complete_event.set()


        # end of processing systeminfo block
        elif gsm_header.chan_type == '2':
            #process CCCH channel
            pass
        
        elif gsm_header.chan_type == '8':
            #process LAPD channel
            pass

        else:
            print("[DEBUG PACKET] {}".format(pkt))
            #return 
 
        # send signal to terminate schannel scan	
        if self.systeminfo.si1_msg and self.systeminfo.si2_msg and \
            self.systeminfo.si3_msg and self.systeminfo.si4_msg:
            
            print("[PACKET PROCESS]success decode packet, send signal to terminate channel scan")
            # signal scan comple found signal channel and continue 
            self.scan_complete = True
            self.scan_complete_event.set()

    @staticmethod
    def process_bcch_packet(pkt):
        if not 'gsm_a.ccch' in pkt:
            return None

        data = {}
        data.update({'sniff_time': pkt.sniff_time})
        #process system infomation 1
        if int(pkt['gsm_a.ccch'].gsm_a_dtap_msg_rr_type, 16) == bcch_process.SYSTEM_INFO_1:
            data.update(bcch_process.parse_sysinfo_1(pkt))
            data.update({'type': 'SYSTEM_INFO_1'})
        
        #process system infomation 2
        elif int(pkt['gsm_a.ccch'].gsm_a_dtap_msg_rr_type, 16) == bcch_process.SYSTEM_INFO_2:
            data.update(bcch_process.parse_sysinfo_2(pkt))
            data.update({'type': 'SYSTEM_INFO_2'})
        
        #process system infomation 3
        elif int(pkt['gsm_a.ccch'].gsm_a_dtap_msg_rr_type, 16) == bcch_process.SYSTEM_INFO_3:
            data.update(bcch_process.parse_sysinfo_3(pkt))
            data.update({'type': 'SYSTEM_INFO_3'})
        
        #process system infomation 4
        elif int(pkt['gsm_a.ccch'].gsm_a_dtap_msg_rr_type, 16) == bcch_process.SYSTEM_INFO_4:
            data.update(bcch_process.parse_sysinfo_4(pkt))
            data.update({'type': 'SYSTEM_INFO_4'})
        
        #process system infomation 13
        elif int(pkt['gsm_a.ccch'].gsm_a_dtap_msg_rr_type, 16) == bcch_process.SYSTEM_INFO_13:
            data.update(bcch_process.parse_sysinfo_13(pkt))
            data.update({'type': 'SYSTEM_INFO_13'})

        #process system infomation 2ter
        elif int(pkt['gsm_a.ccch'].gsm_a_dtap_msg_rr_type, 16) == bcch_process.SYSTEM_INFO_2TER:
            data.update(bcch_process.parse_sysinfo_2ter(pkt))
            data.update({'type': 'SYSTEM_INFO_2TER'})

        #process system infomation 2quater
        elif int(pkt['gsm_a.ccch'].gsm_a_dtap_msg_rr_type, 16) == bcch_process.SYSTEM_INFO_2QUATER:
            data.update(bcch_process.parse_sysinfo_2quater(pkt))
            data.update({'type': 'SYSTEM_INFO_2QUATER'})
        else:
            data = None
        
        return data
