from datetime import datetime
from app.system_info import system_info
from app.database import API, MySQL_external
from app.helper import scale
import logging
import math

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

class CellSelect():
    #class define current cell select state 
    def __init__(self, serve_num=5):
        # list of monitor CellNeighbor belong to strongest channels
        self.serve_num = serve_num
        self.cells = []
        self.cell_trail = []
        self.active_time = 0

    def insert_cell_entry(self, cellneighbor=None):
        logger.info("[CELL_SELECT]insert channel {} to neighbor list {}".format(cellneighbor.arfcn, 
            [cell.arfcn for cell in self.cells]))
        if cellneighbor.__class__.__name__ != 'CellNeighbor':
            logger.info('[CELL_SELECT]insert invalid object')
            return
        self.cells.append(cellneighbor)

    def _remove_cell_entry(self, arfcn):
        for i in self.cells:
            if i.arfcn == arfcn:
                logger.info("[CELL_SELECT] remove channel {} from list struct serving {}".format(i.arfcn, [cell.arfcn for cell in self.cells])) 
                self.cells.remove(i)
                return True
        return False
    
    def remove_cell_entry(self, cellneighbor=None):
        logger.info("[CELL_SELECT] remove channel {} from list struct serving {}".format(cellneighbor.arfcn, [cell.arfcn for cell in self.cells])) 
        if cellneighbor.__class__.__name__ == 'CellNeighbor':
            self.cells.remove(cellneighbor)
            return True
        return False

    def get_cell_entry(self, arfcn):
        """--> CellNeighbor"""
        for cell in self.cells:
            if cell.arfcn == arfcn:
                return cell
        return None
    
    def sort_select_cell(self, sorttime, index_round=0):
        self.active_time = sorttime
        # Recalculate c1 c2 sort and select cell with highest priority
        #print("[CELL SELECT]sort neighbor cell {}".format([cell.arfcn for cell in self.cells]))
        for cell_entry in self.cells:
            cell_entry.c1 = cell_entry.calculate_c1()
            cell_entry.c2 = cell_entry.calculate_c2()

            # calculate weigh for rxlev, snr, ber
            cell_entry.rxlev_criteria = cell_entry.calculate_rxlev_criteria(arfcn=cell_entry.arfcn, 
                    calculate_time=self.active_time, attr_value=cell_entry.rxlev_avg_dbm, index_round=index_round)
            cell_entry.snr_criteria = cell_entry.calculate_snr_criteria(arfcn=cell_entry.arfcn, 
                    calculate_time=self.active_time, attr_value=cell_entry.snr_avg_level, index_round=index_round)
            cell_entry.ber_criteria = cell_entry.calculate_ber_criteria(arfcn=cell_entry.arfcn, 
                    calculate_time=self.active_time, attr_value=cell_entry.ber_avg_ratio, index_round=index_round)

            logger.info("[CELL SELECT] arfcn {} calculated rxlev: {}, calculated snr: {}, calculated ber: {}"
                    .format(cell_entry.arfcn, cell_entry.rxlev_criteria, cell_entry.snr_criteria, cell_entry.ber_criteria))

            cell_entry.cc = cell_entry.calculate_criteria()
        #TODO better algorithm to select serving cells
        self.sort_arfcn(key = 'CC')
        return [cell.arfcn for cell in self.cells]

    def sort_arfcn(self, key = 'CC'):

        def C2_sort(entry):
            if not hasattr(entry, 'c2'):
                return -99
            else:
                return entry.c2

        def CC_sort(entry):
            if not hasattr(entry, 'cc'):
                return -99
            elif hasattr(entry, 'cc'):
                return entry.cc

        if key == 'C2':
            self.cells.sort(key=C2_sort, reverse=True)
        elif key == 'CC':
            self.cells.sort(key=CC_sort, reverse=True)
        else:
            logger.info("[ERROR]key function to sort not found")

        logger.info("[SORTDEBUG]after sort list neighbor {}".format([neighbor.arfcn for neighbor in self.cells]))
        return [cell.arfcn for cell in self.cells]

class CellNeighbor():
    ENTRY_TTL_MAX = 2
    CELL_SERVING_CRITERIA = 7
    SERVING_TIME_VALID = 60
    GSM_SAMPLERATE = 2 * 1625000 / 6
    NUMBER_SAMPLE_CRITERIA = 7
    LOST_SIGNAL_PENALTY = 7
    LACK_SAMPLE_PENALTY = 2
    BELOW_LIMIT_PENALTY = 5
    
    RXLEV_WEIGH = 1
    SNR_WEIGH = 0.7
    BER_WEIGH = 0.1

    STANDARD_RANGE = (1, 100)
    RXLEV_RANGE = (-100, -30)
    RXLEV_LIMIT = -65
    SNR_RANGE = (0, 255)
    SNR_LIMIT = 100
    BER_RANGE = (0, 0.1)

    instance_counter = 0

    def __init__(self, si_struct, arfcn, rxlev_avg_dbm, rxlev_count, start_sample, snr_avg_level):
        self.system_info = system_info()
        self.system_info.data_copy(si_struct)
        self.arfcn = arfcn
        self.cell_select_id = CellNeighbor.instance_counter
        self.entry_ttl = CellNeighbor.ENTRY_TTL_MAX
        self.db_object = None
        self.info_mask = 0x0
        self.start_sample = start_sample
        self.sniff_time = 0
        self.round_counter = 1
        
        # parameter to calculate c1
        self.rxlev_avg_dbm = rxlev_avg_dbm
        self.snr_avg_level = snr_avg_level
        self.ber_avg_ratio = -1 #TODO process this value
        self.rxlev_count = rxlev_count
        self.rxlev_acc_min = 0
        self.ms_txpwr_max_cch = 0
        self.p = 0

        #parameter to calculate c2
        self.time_create = datetime.now()
        self.start_pending = None
        self.is_serving = False
        self.c1 = self.calculate_c1()
        self.c2 = self.calculate_c2()
    
        #parameter to calculate cc
        self.snr_criteria = 0
        self.rxlev_criteria = 0
        self.ber_criteria = 0
        CellNeighbor.instance_counter += 1

    def update_cell_entry(self, cellneighbor):
        if cellneighbor.__class__.__name__ != 'CellNeighbor':
            logger.info('[ERROR]update invalid object')
            return
        
        logger.info("[CELL_SELECT]update cell select entries si2 message {}, si2ter message {}"
                .format(cellneighbor.system_info.si2_msg, cellneighbor.system_info.si2ter_msg))
        if cellneighbor.system_info.si1_msg:
            self.system_info.si1_msg = cellneighbor.system_info.si1_msg
        if cellneighbor.system_info.si2_msg:
            self.system_info.si2_msg = cellneighbor.system_info.si2_msg
        if cellneighbor.system_info.si2ter_msg:
            self.system_info.si2ter_msg = cellneighbor.system_info.si2ter_msg
        if cellneighbor.system_info.si3_msg:
            self.system_info.si3_msg = cellneighbor.system_info.si3_msg
        if cellneighbor.system_info.si4_msg:
            self.system_info.si4_msg = cellneighbor.system_info.si4_msg

        self.snr_avg_level = cellneighbor.snr_avg_level
        self.rxlev_avg_dbm = cellneighbor.rxlev_avg_dbm
        self.rxlev_count += cellneighbor.rxlev_count
        self.sniff_time += cellneighbor.sniff_time
        self.start_sample = cellneighbor.start_sample
        self.entry_ttl = CellNeighbor.ENTRY_TTL_MAX
        self.round_counter += 1
        self.system_info.mask = self.system_info.mask | cellneighbor.system_info.mask

    def calculate_c1(self):
        a = self.rxlev_avg_dbm - self.rxlev_acc_min
        b = self.ms_txpwr_max_cch - self.p

        max_b_0 = b if b > 0 else 0

        c1 = a - max_b_0
        return c1
        #return c1 + self.rxlev_count / 9

    def calculate_c2(self):
        c2 = self.c1
        if not self.system_info.sp_valid:
            #print("[DEBUG] no extended reselection parameter avaiable C2 = C1 =")
            return c2

        if self.system_info.sp_pt == 31:
            logger.error("[DEBUG]penalty time is '11111'")
            c2 -= (self.system_info.sp_cro << 1)
            return c2

        c2 += (self.system_info.sp_cro << 1)
        if self.entry_ttl == 0:
            c2 -= 20
        if self.is_serving:
            return c2

        #penalty time reached
        penalty_time =  datetime.now() - self.time_create
        if  penalty_time.seconds >= self.system_info.sp_pt:
            return c2
        
        #penalty time not reached, subtract off set
        if self.system_info.sp_to < 7:
            c2 -= self.system_info.sp_to * 10
        else:
            c2 = -1000

        return c2

    # TODO calculate better weigh for snr_avg_level and CELL_SERVING_CRITERIA
    # the bigger CELL_SERVING_CRITERIA the more likely cell will persist from last round strongest 
    def calculate_criteria(self):
        count = 0
        cc = 0
        if self.snr_criteria:
            cc += self.SNR_WEIGH * self.snr_criteria 
            count += self.SNR_WEIGH
        if self.rxlev_criteria:
            cc += self.RXLEV_WEIGH * self.rxlev_criteria
            count += self.RXLEV_WEIGH
        if self.ber_criteria:
            cc += self.BER_WEIGH * self.ber_criteria

        if count == 0:
            criteria = self.c2
        else:
            criteria = cc / count
        
      
        return criteria
    
    @staticmethod
    def calculate_rxlev_criteria(arfcn, calculate_time, attr_value=-1, index_round=0):
        stop_offset = calculate_time
        time_window = CellNeighbor.SERVING_TIME_VALID  * CellNeighbor.GSM_SAMPLERATE 
        start_offset = stop_offset - time_window
        if start_offset < 0:
            start_offset = 0
        query = API.get_rounds_rxlev_info(arfcn=arfcn,
                start_offset=start_offset,
                stop_offset=stop_offset,
                #nlimit=CellNeighbor.NUMBER_SAMPLE_CRITERIA)
                index_round=index_round,
                nlimit=-1)
        
        # relevs is an array of receiver power from previous round with higher index is recently scan round
        rxlevs = []
        for round in query:
            # Return tuple of round average power and time from this round
            rxlevs.append(tuple((round[0], round[1] - start_offset)))

        sum = 0
        count = 0
        for rxlev in rxlevs:
            sum += rxlev[0] * rxlev[1]
            #logger.info(" {} += {} * {} [sum += rxlev * time]".format(sum, rxlev[0], rxlev[1]))
            count += rxlev[1]
        
        sample_number = len(rxlevs)
        if count == 0:
            return CellNeighbor.STANDARD_RANGE[0]
        # If database query return current value or attr value not set   
        elif sample_number > 0 and rxlevs[-1][1] == time_window or attr_value == -1:
            value = sum  / count
        # If database return not enought elem
        else:
            value = (sum + attr_value * time_window) / (count + time_window)

        # If not enough sample to calculate criteria value subtract penaty value
        if sample_number < CellNeighbor.NUMBER_SAMPLE_CRITERIA:
            value -= (CellNeighbor.NUMBER_SAMPLE_CRITERIA - sample_number) * CellNeighbor.LACK_SAMPLE_PENALTY
        
        # If rxlev or snr level is lower than limit subtract a penelty amount
        if attr_value < CellNeighbor.RXLEV_LIMIT:
            value -= CellNeighbor.BELOW_LIMIT_PENALTY
        
        # logger.info("[CELL SELECT]debug calculate rxlev criteria arfcn {} rxlevs {} return {}"
        #         .format(arfcn, rxlevs, value))
        # If round doesnt get signal from scan and use cached info from previous round subtract penalty amount
        return scale(value, CellNeighbor.RXLEV_RANGE, CellNeighbor.STANDARD_RANGE)

    @staticmethod
    def calculate_snr_criteria(arfcn, calculate_time, attr_value=-1, index_round=0):
        stop_offset = calculate_time
        time_window = CellNeighbor.SERVING_TIME_VALID  * CellNeighbor.GSM_SAMPLERATE 
        start_offset = stop_offset - time_window
        if start_offset < 0:
            start_offset = 0
        query = API.get_rounds_snr_info(arfcn=arfcn,
                start_offset=start_offset, stop_offset=stop_offset,
                #nlimit=CellNeighbor.NUMBER_SAMPLE_CRITERIA)
                index_round=index_round,
                nlimit=-1)
        
        # snrs is an array of signal noise ratio  from previous round with higher index is recently scan round
        snrs = []
        for round in query:
            # Return tuple of round average power and time from this round
            snrs.append(tuple((round[0], round[1] - start_offset)))

        sum = 0
        count = 0
        for snr in snrs:
            sum += snr[0] * snr[1]
            #logger.info(" {} += {} * {} [sum += snr * time]".format(sum, snr[0], snr[1]))
            count += snr[1]
        
        sample_number = len(snrs)
        if count == 0:
            return CellNeighbor.STANDARD_RANGE[0]
        # If database query return current value or attr value not set   
        elif sample_number > 0 and snrs[-1][1] == time_window or attr_value==-1:
            value = sum  / count 
        # If database return not enought elem
        else:
            value = (sum + attr_value * time_window) / (count + time_window)
       
        # If not enough sample to calculate criteria value subtract penaty value
        if sample_number < CellNeighbor.NUMBER_SAMPLE_CRITERIA:
            value -= (CellNeighbor.NUMBER_SAMPLE_CRITERIA - sample_number) * CellNeighbor.LACK_SAMPLE_PENALTY
        
        if attr_value < CellNeighbor.SNR_LIMIT:
            value -= CellNeighbor.BELOW_LIMIT_PENALTY
        
        # logger.info("[CELL SELECT]debug calculate snr criteria arfcn {} snrs {} return {}"
        #         .format(arfcn, snrs, value))
        # If round doesnt get signal from scan and use cached info from previous round subtract penalty amount
        #value -= (CellNeighbor.ENTRY_TTL_MAX - entry_ttl) * CellNeighbor.LOST_SIGNAL_PENALTY
        return scale(value, CellNeighbor.SNR_RANGE, CellNeighbor.STANDARD_RANGE)

    @staticmethod
    def calculate_ber_criteria(arfcn, calculate_time, attr_value=-1, index_round=0):
        stop_offset = calculate_time
        time_window = CellNeighbor.SERVING_TIME_VALID  * CellNeighbor.GSM_SAMPLERATE 
        start_offset = stop_offset - time_window
        if start_offset < 0:
            start_offset = 0
        query = MySQL_external.get_rounds_ber_info(arfcn=arfcn, 
                start_offset=start_offset, stop_offset=stop_offset,
                index_round=index_round,
                #nlimit=CellNeighbor.NUMBER_SAMPLE_CRITERIA)
                nlimit=10)
        
        # bers is an array of signal noise ratio  from previous round with higher index is recently scan round
        bers = []
        for round in query:
            # Return tuple of round average power and time from this round
            bers.append(tuple((round[0], round[1] - start_offset)))

        sum = 0
        count = 0
        #logger.info("[CELL SELECT]debug calculate ber criteria arfcn {} bers {}".format(arfcn, bers))
        for ber in bers:
            sum += ber[0] * ber[1]
            #logger.info(" {} += {} * {} [sum += ber * time]".format(sum, ber[0], ber[1]))
            count += ber[1]

        sample_number = len(bers)
        if count == 0:
            return CellNeighbor.STANDARD_RANGE[0]
        # If database query return current value or attr value not set   
        elif sample_number > 0 and bers[-1][1] == time_window or attr_value==-1:
            value = sum  / count 
        # If database not return current value
        else:
            value = (sum + attr_value * time_window) / (count + time_window)
       
        # logger.info("[CELL SELECT]debug calculate ber criteria arfcn {} bers {} return {}"
        #         .format(arfcn, bers, value))
        _value = scale(value, CellNeighbor.BER_RANGE, CellNeighbor.STANDARD_RANGE)
        return CellNeighbor.STANDARD_RANGE[1] - _value

