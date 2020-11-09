from app.models import neighbor_arfcn, tranx_arfcn, cell_info, scan_arfcn, scan_activity, debug_static
from app import session
from app import config
from app import packet_process
from app.database import API, MySQL_external
from app.recon_scan import recon_scan
from app import control_algorithm
from app import helper
from app import signal_handler
from app import machine_state
from datetime import datetime

import app
import logging
import cell_select, gsm_band
import time, os
import threading
import grgsm
import numpy
import gc

from threading import Thread
from multiprocessing import Process
from SimpleXMLRPCServer import SimpleXMLRPCServer
from app.system_info import system_info
from app.modules.scanners.auto_file_scanner import auto_file_scanner
from gnuradio import gr

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class GSMscanner():
    def __init__(self):
        self.GUARD_TIME = 3
        self.FLAG_CONFIG = 0x1f

        self.block_control = None
        self.bcch_channels = []
        self.bcch_flags = []
        self.cell_select = cell_select.CellSelect()

        # Sample offsets
        self.current_offset = 0
        self.stop_offset = 0
        self.sample_time = datetime.now()
        self.machine_state = machine_state.MachineState()

        # Set scanner initualize state
        logger.info('Sdr controller running, config start scan:')
        self.watchdog_counter = 0
        cell_select.CellNeighbor.instance_counter = API.get_last_cell_index() + 1

    def process_channels_from_round(self):
        self.watchdog_counter += 1
        # Get channels can sync from receiver
        sync_channels = list(self.block_control.get_list_arfcn())
        logger.info("Sync channels round {}: {}".format(self.current_round, sync_channels))

        # Get System Information from extract block
        chans = numpy.array(self.block_control.gsm_extract_system_info.get_chans())
        cell_ids = numpy.array(self.block_control.gsm_extract_system_info.get_cell_id())
        lacs = numpy.array(self.block_control.gsm_extract_system_info.get_lac())
        mccs = numpy.array(self.block_control.gsm_extract_system_info.get_mcc())
        mncs = numpy.array(self.block_control.gsm_extract_system_info.get_mnc())
        snr_sum = numpy.array(self.block_control.gsm_extract_system_info.get_sum_snr())
        pwr_db_sum = numpy.array(self.block_control.gsm_extract_system_info.get_sum_pwr_db())
        count_packet = numpy.array(self.block_control.gsm_extract_system_info.get_count_burst())
        cbq = numpy.array(self.block_control.gsm_extract_system_info.get_cbq())
        cell_reselect_offset = numpy.array(self.block_control.gsm_extract_system_info.get_cell_reselect_offset())
        temporary_offset = numpy.array(self.block_control.gsm_extract_system_info.get_temporary_offset())
        penalty_time = numpy.array(self.block_control.gsm_extract_system_info.get_penalty_time())
        mask = numpy.array(self.block_control.gsm_extract_system_info.get_mask())

        # Get stop offset
        self.stop_offset = self.block_control.get_stop_offset()
        # Check if offset get from file source is negative
        if self.stop_offset < 0:
            raise ValueError('Terminated !!! Invalid input')

        for channel in chans:
            sys_info = system_info(arfcn=channel)
            index = list(chans).index(channel)
            si2_neighbor_list = numpy.array(self.block_control.gsm_extract_system_info.get_neighbours(channel))
            si1_cell_list = numpy.array(self.block_control.gsm_extract_system_info.get_cell_arfcns(channel))

            # Create and parser System Information
            sys_info.mask = mask[index]
            logger.info("Mask for channel {}: {}".format(channel, sys_info.mask))
            if sys_info.mask & 0x10:
                # System Information 1
                sys_info.si1_msg['tranx_arfcn'] = si1_cell_list
                sys_info.si1_msg['frame_number'] = 0
                sys_info.si1_msg['signal_dbm'] = 0
            if sys_info.mask & 0x08:
                # System Information 2
                sys_info.si2_msg['neighbor_arfcn'] = si2_neighbor_list
                sys_info.si2_msg['frame_number'] = 0
                sys_info.si2_msg['signal_dbm'] = 0
            if sys_info.mask & 0x04:
                # System Information 2ter
                sys_info.si2ter_msg['neighbor_arfcn'] = si2_neighbor_list
                sys_info.si2ter_msg['frame_number'] = 0
                sys_info.si2ter_msg['signal_dbm'] = 0
            if sys_info.mask & 0x02:
                # System Information 3
                sys_info.si3_msg['cell_id'] = cell_ids[index]
            if sys_info.mask & 0x01:
                # System Information 4
                sys_info.si4_msg['lac'] = lacs[index]
                sys_info.si4_msg['mcc'] = mccs[index]
                sys_info.si4_msg['mnc'] = mncs[index]

            # Compute signal_strength and channel_snr
            if count_packet[index] != 0:
                signal_strength = pwr_db_sum[index] / count_packet[index]
                channel_snr = snr_sum[index] / count_packet[index]
                packet_count = count_packet[index]
            elif count_packet[index] == 0:
                logger.info("Channel {} sync but doesnt get any burst".format(channel))
                signal_strength = cell_select.CellNeighbor.RXLEV_RANGE[0]
                channel_snr = cell_select.CellNeighbor.SNR_RANGE[0]
                packet_count = 0

            # Create or update CellNeighbor
            cached_entry = self.cell_select.get_cell_entry(arfcn=channel)
            if cached_entry is None:
                # First time sync channel, create CellNeighbor
                cached_entry = cell_select.CellNeighbor(si_struct=sys_info,
                                                        arfcn=channel,
                                                        rxlev_avg_dbm=signal_strength,
                                                        start_sample=self.current_offset,
                                                        rxlev_count=packet_count,
                                                        snr_avg_level=channel_snr)
                cached_entry.sniff_time = self.stop_offset - self.current_offset
                self.cell_select.insert_cell_entry(cached_entry)
            elif cached_entry:
                # This channel was sync before, need update
                update_entry = cell_select.CellNeighbor(si_struct=sys_info,
                                                        arfcn=channel,
                                                        rxlev_avg_dbm=signal_strength,
                                                        start_sample=self.current_offset,
                                                        rxlev_count=packet_count,
                                                        snr_avg_level=channel_snr)
                update_entry.sniff_time = self.stop_offset - self.current_offset
                cached_entry.update_cell_entry(update_entry)

        # Get list arfcn can not sync
        channels_not_sync = list(set(self.bcch_channels) - set(sync_channels))
        for channel in channels_not_sync:
            cached_entry = self.cell_select.get_cell_entry(arfcn=channel)
            if cached_entry is None:
                # This channel never sync before
                continue
            elif cached_entry.entry_ttl > 0:
                # Decrement time to live
                logger.info("Decrement time to live list struct {}"
                      .format(cached_entry.arfcn))
                cached_entry.entry_ttl -= 1
            else:
                # Remove channel from bcch_channels
                logger.info("Remove channel from arfcn list struct {} on round {}"
                      .format(cached_entry.arfcn, self.current_round))
                if cached_entry.db_object:
                    cached_entry.db_object.stop_time = self.current_offset
                self.cell_select.remove_cell_entry(cached_entry)

        # Ranking cell
        logger.info("Sort select cell at offset {} index round {}".format(self.current_offset,
                                                                                 app.config.capture_round))
        self.cell_select.sort_select_cell(sorttime=self.current_offset, index_round=app.config.capture_round)
        # Compute channel_priority and commit to database
        channel_priority = 1
        signal_arfcns = []
        for channel_entry in self.cell_select.cells:
            # Do not push to database round lost signal
            if channel_entry.entry_ttl < cell_select.CellNeighbor.ENTRY_TTL_MAX:
                logger.info("Debug skip lost signal channel {}".format(channel_entry.arfcn))
                continue
            scan_commit = scan_arfcn(
                arfcn=channel_entry.arfcn,
                cell_select_info=channel_entry.cell_select_id,
                scan_level=1,
                rank=channel_priority,
                round=self.current_round,
                average_pwr=round(channel_entry.rxlev_avg_dbm),
                snr_avg_level=channel_entry.snr_avg_level,
                pkt_number=round(channel_entry.rxlev_count),
                sample_offset=self.current_offset,
                timestamp=datetime.now(),
                sniff_time=channel_entry.sniff_time,
                round_counter=channel_entry.round_counter,
                rxlev_debug_criteria=channel_entry.rxlev_criteria,
                snr_debug_criteria=channel_entry.snr_criteria,
                index_round=app.config.capture_round,
            )
            session.add(scan_commit)
            signal_arfcns.append(channel_entry.arfcn)
            neighbor_arfcns = []
            # Get neighbor arfcns list to next round
            if channel_entry.system_info.mask & 0x08:
                # System Information 2
                neighbor_arfcns.extend(channel_entry.system_info.si2_msg["neighbor_arfcn"])
                # TODO if SI2 then push to database, so SI2ter ????
            if channel_entry.system_info.mask & 0x04:
                # System Information 2ter
                neighbor_arfcns.extend(channel_entry.system_info.si2ter_msg["neighbor_arfcn"])

            # Create new cell info if cell not already tracking
            if channel_entry.cell_select_id not in self.cell_select.cell_trail:
                cell = cell_info(cell_id=-1, mcc=-1, mnc=-1, lac=-1,
                                 cell_arfcn=channel_entry.arfcn,
                                 cell_select_info=channel_entry.cell_select_id,
                                 start_time=channel_entry.start_sample,
                                 index_round=app.config.capture_round,
                                 )
                channel_entry.db_object = cell
                channel_entry.info_mask = 0x0
                # Push in cell_trail
                self.cell_select.cell_trail.append(channel_entry.cell_select_id)
                session.add(channel_entry.db_object)

            # Update System Information to database
            if channel_entry.system_info.mask & 0x02 and not channel_entry.info_mask & 0x02:
                # System Information 3 
                channel_entry.db_object.cell_id = channel_entry.system_info.si3_msg['cell_id']
                channel_entry.info_mask = channel_entry.info_mask | 0x02
            if channel_entry.system_info.mask & 0x01 and not channel_entry.info_mask & 0x01:
                # System Information 4
                channel_entry.db_object.mcc = channel_entry.system_info.si4_msg['mcc']
                channel_entry.db_object.mnc = channel_entry.system_info.si4_msg['mnc']
                channel_entry.db_object.lac = channel_entry.system_info.si4_msg['lac']
                channel_entry.info_mask = channel_entry.info_mask | 0x01
            if channel_entry.system_info.mask & 0x10 and not channel_entry.info_mask & 0x10:
                # System Information 1
                for temp_arfcn in channel_entry.system_info.si1_msg['tranx_arfcn']:
                    tranx = tranx_arfcn(
                        current_arfcn=channel_entry.arfcn,
                        tranx_arfcn=temp_arfcn,
                        cell_select_info=channel_entry.cell_select_id,
                        sample_offset=self.current_offset,
                    )
                    session.add(tranx)
                channel_entry.info_mask = channel_entry.info_mask | 0x10

            logger.info("Prepare neighbor_arfcns from channel {}: {}".format(channel_entry.arfcn, neighbor_arfcns))
            for arfcn in neighbor_arfcns:
                # Check arfcn in bcch_channels, if not append it
                if arfcn not in self.bcch_channels:
                    self.bcch_channels.append(arfcn)
            channel_priority += 1

        # Finish process channels entries
        if not signal_arfcns:
            # signal arfcn list is empty commit empty round to database
            scan_commit = scan_arfcn(
                round=self.current_round,
                timestamp=datetime.now(),
                sample_offset=self.current_offset,
                index_round=app.config.capture_round,
            )
            session.add(scan_commit)
        elif signal_arfcns:
            # Signal arfcn list is not empty reset watchdog counter and process signal channels
            self.watchdog_counter = 0

        # Done round update start offset
        try:
            session.commit()
        except Exception as e:
            logger.error("Error fail to commit to database {}".format(e))
            session.rollback()

    def initualize_scanner(self):
        self.current_round = API.get_last_scan_round()
        self.start_scan = API.get_start_offset()
        self.stop_scan = API.get_stop_offset()
        self.mode = API.get_scanning_mode()
        self.last_state = API.get_last_scan_state()
        # Last capture round is empty start capture_round at capture round 0
        logger.info("Instaulize scanner with state {} config {}".format(self.last_state, app.config.state))
        if self.last_state.get("capture_round") == -1:
            logger.info("Start scanner from start capture round 0")
            capture_round = 0
            self.start_scan = 0
        elif self.last_state.get("activity") == "NETWORK_CHANGE":
            capture_round = self.last_state.get("capture_round") + 1
            self.start_scan = 0
            self.current_round = 1
            # Offset 1 round from lost signal round from last scan
            logger.info("Start scanner when change network to capture round {}"
                          .format(capture_round))
        elif self.last_state.get("activity") == "LOST_SIGNAL":
            _time_delta = (datetime.now() - self.last_state.get("timestamp")).total_seconds()
            capture_round = self.last_state.get("capture_round")
            self.start_scan = self.last_state.get("sample_offset_stop") + (_time_delta * 1625000 * 2 / 6)
            logger.info("Start scanner when lost signal capture round {} from offset {}"
                          .format(capture_round, self.start_scan))
            logger.info("Time delta stop offset {} now {}"
                          .format(self.last_state.get("timestamp"), datetime.now()))
        
        elif self.last_state.get("activity") == "STOPPED":
            app.config.state = "STOPPED"
            logger.info("Scanner stop until receive new setting {}"
                          .format(app.config.state))
            while app.config.state == "STOPPED":
                time.sleep(1)
            self.start_scan = self.last_state.get("sample_offset_stop")
            capture_round = self.last_state.get("capture_round")
            app.config.capture_round = capture_round
            self.current_offset = self.start_scan
            logger.info("Initualize scanner with state {}".format(self.last_state))
            self.state_processing()

        elif self.last_state.get("activity") == "POWER_OFF":
            self.start_scan = self.last_state.get("sample_offset_stop")
            self.current_round = self.last_state.get("last_round")
            self.current_offset = self.last_state.get("last_scan_offset")
            capture_round = self.last_state.get("capture_round")
            app.config.state = "POWER_OFF"
            app.config.capture_round = capture_round
            logger.info("Scanner set last round to power off state !!!")
            self.state_processing()
        else:
            capture_round = MySQL_external.get_capture_info().get("capture_round")
            logger.info("Start scanner at realty capture round{}"
                          .format(capture_round))
        
        logger.info("Start scanner from database round {} capture round {} offset {}" \
                      .format(self.current_round, capture_round, self.start_scan))
        self.sample_time = datetime.now()
        # Wait until configured network have data in database
        while True:
            time.sleep(1)
            if MySQL_external.check_network_info(capture_round=capture_round):
                logger.info("check capture round info: capture round {}".format(capture_round))
                break

        app.config.capture_round = capture_round
        app.config.network = MySQL_external.get_network_from_capture_round(app.config.capture_round)
        self.machine_state.create_file()
        # channel input maybe empty or not set and have none value
        if config.channels:
            self.bcch_channels = [int(channel) for channel in config.channels]
        else:
            _wideband_start = datetime.now()
            logger.info("recon scan start ---- at time {}, offset {} operator {}" \
                  .format(_wideband_start, self.start_scan, config.network))
            recon_scanner = recon_scan(provider=config.network, bands=config.bands,
                                       device=config.device, greedy=True, start_offset=self.start_scan)
            self.bcch_channels = recon_scanner.do_scan()
            _wideband_stop = datetime.now()
            _time_delta = (_wideband_stop - _wideband_start).seconds
            # self.current_offset = self.start_scan +  _time_delta * 1625000*2/6
            logger.info("recon scan complete {} ---- at time {}, offset {} scan band {}"\
                    .format(self.bcch_channels, _wideband_stop, self.current_offset, recon_scanner.SCAN_BANDS))
            app.config.bands = recon_scanner.SCAN_BANDS
            if len(app.config.bands) == 1:
                self.FLAG_CONFIG -= 0x04
                logger.info("[RECON SCAN] remove sys2ter flag from scan flags scanning band {}"
                        .format(config.bands))
            self.sample_time = recon_scanner.start_time

    def controller_sdr(self):
        # wait untill initualize sdr block
        self.initualize_scanner()  # KEEP
        _time_delta = (datetime.now() - self.sample_time).total_seconds()
        # if self.last_state.get("activity") == "LOST_SIGNAL":
        #     _time_delta = (datetime.now() - self.last_state.get("timestamp")).total_seconds()
        #     self.current_offset = int(self.last_state.get("sample_offset_stop") + _time_delta * 1625000*2/6)
        # else:
        #     _time_delta = (datetime.now() - self.sample_time).total_seconds()
        #     self.current_offset = _time_delta * 1625000*2/6
        self.current_offset = self.start_scan + _time_delta * 1625000 * 2 / 6
        logger.info("[TIMEDELTA]sample time offset {} now {} flag {}"
                      .format(self.sample_time, datetime.now(), self.bcch_flags))
        # keep value current_offset if continue channel scan from recon scan finish offset
        # or set current_offset at start_scan to start channel scan at starting point
        self.sample_time = datetime.now()
        _debug_static = None
        while True:
            _time_delta = 0
            # jump to neighbor bcch channel to measure power

            # handle prograam state
            self.state_processing()
            logger.info("stop state processing {}".format(datetime.now()))

            # Filter list bcch_channels by band and network
            logger.info("Filter bcch_channels by operator: {}".format(config.network))
            self.bcch_channels = gsm_band.arfcn.get_scan_arfcn(self.bcch_channels,
                                                               bands=config.bands,
                                                               network=config.network)
            self.bcch_channels.sort()
            # Init bcch_flags all 0
            self.bcch_flags = [0] * len(self.bcch_channels)
            for i in range(len(self.bcch_channels)):
                for neighbor in self.cell_select.cells:
                    if self.bcch_channels[i] == neighbor.arfcn and neighbor.system_info.mask & self.FLAG_CONFIG == self.FLAG_CONFIG:
                        self.bcch_flags[i] = 1

            logger.info("Start scan round {}, at offset {} scan channels {}, flag:  {} system flag {} at datetime {}"
                  .format(self.current_round, self.current_offset, self.bcch_channels, self.bcch_flags, self.FLAG_CONFIG, datetime.now()))

            # Free object self.block_control
            if self.block_control is not None:
                self.block_control = None
            gc.collect()

            # Init module auto file scanner
            # Start offset is last offset get from recon scan while start_scan is starting point of scan config
            _start_initualize = time.time()
            self.block_control = auto_file_scanner(arfcn=self.bcch_channels,
                                                   flag=self.bcch_flags,
                                                   offset=self.current_offset)
            _stop_initualize = time.time()
            self.block_control.set_max_burst(2)
            self.block_control.set_gain(40)
            # Start block control
            capture_offset = self.block_control.get_real_offset()
            #_stop_initualize = time.time()
            _offset_initualize = (_stop_initualize - _start_initualize) * 1625000*2/6

            logger.info("Set offset to file source {} real offset {}"
                  .format(self.current_offset ,capture_offset))
            if (capture_offset - self.current_offset - _offset_initualize) / (1625000 * 2 / 6) < self.GUARD_TIME:

                time.sleep((self.current_offset + _offset_initualize - capture_offset)/(1625000*2/6) + self.GUARD_TIME)
                _time_delta = _time_delta - ((self.current_offset + _offset_initualize - capture_offset)/(1625000*2/6) + self.GUARD_TIME)
                logger.error("[OFFSET ERROR]capture run slower than scanner {} reset to capture offset {} - {} _time_delta {}"
                    .format(self.current_offset, capture_offset, self.GUARD_TIME * 1625000*2/6, _time_delta))
            self.block_control.set_offset(sample_offset=self.current_offset)


#                self.block_control.set_offset(sample_offset=self.current_offset)
#            elif capture_offset - self.current_offset - _offset_initualize > 2 * self.GUARD_TIME * 1625000*2/6:
#                logging.error("[OFFSET ERROR]scanner slower than capture {} reset offset to capture offset {} - {}"
#                    .format(self.current_offset, capture_offset, self.GUARD_TIME * 1625000*2/6))
#                self.current_offset = capture_offset - self.GUARD_TIME * 1625000*2/6
#                self.block_control.set_offset(sample_offset=self.current_offset)

            capture_offset = self.block_control.get_real_offset()
            _debug_static = debug_static(
                sample_offset=self.current_offset,
                capture_offset=capture_offset , round=self.current_round, timestamp=datetime.now())
            session.add(_debug_static)

            _start_offset = time.time()
            self.block_control.start()
            self.block_control.wait()
            self.block_control.stop()
            print("DEBUG ---------------------------------------------- 01")
            _stop_offset = time.time()

            if self.block_control.get_process_items() == 0 and app.config.state == "RUNNING":
                logger.info("Block doesnt process any items trigger end of file")
                app.config.state = "STOPPED"

            self.process_channels_from_round()
            self.block_control.destroy()
            logger.info("Current neighbor list: {} watchdog counter {} -- at {}".format(self.bcch_channels,
                                                                                      self.watchdog_counter, datetime.now()))
            signal_arfcn = [neighbor.arfcn for neighbor in self.cell_select.cells]
            _time_delta = _time_delta + (datetime.now() - self.sample_time).total_seconds()
            logger.info("Round {} initualize time {} dsp time {} process time {} " \
                  .format(self.current_round, _stop_initualize - _start_initualize, _stop_offset - _start_offset,
                          _time_delta))
            self.current_offset = int(self.current_offset + _time_delta * 1625000 * 2 / 6)
            self.current_round += 1
            self.sample_time = datetime.now()

    def state_processing(self):
        logger.info("State processing debug current offset at {} capture round {} app state {}"
              .format(self.current_offset, app.config.capture_round, app.config.state))

        activity = app.config.state
        if self.watchdog_counter == 10:
            activity = "LOST_SIGNAL"

        elif app.config.state == "RUNNING":
            return

        elif self.mode == "OFFLINE" and self.stop_scan < self.current_offset:
            activity = "STOPPED"

        elif app.config.state == "NETWORK_CHANGE":
            activity = "NETWORK_CHANGE"

        elif app.config.state == "STOPPED":
            activity = "STOPPED"

        elif app.config.state == "POWER_OFF":
            activity = "NETWORK_CHANGE"

        _time_delta = (datetime.now() - self.sample_time).total_seconds()
        scan_end = scan_activity(
            last_round=self.current_round,
            sample_offset=self.current_offset + (_time_delta * 1625000 * 2 / 6),
            activity=activity,
            continues=True,
            index_round=app.config.capture_round,
            timestamp=datetime.now()
        )
        session.add(scan_end)
        try:
            session.commit()
        except Exception as e:
            logger.error(e)

        signal_handler.send_terminate()

    def setup_rpc_server(self):
        app.db.dispose()
        self.rpc_server = SimpleXMLRPCServer(("0.0.0.0", 8000))
        # self.rpc_server = SimpleThreadXMLRPCServer(("0.0.0.0", 8000))
        self.rpc_server.register_introspection_functions()
        from app.rpc_handler import RequestHandler
        logger.info("initualize rpc server")
        self.rpc_server.register_function(RequestHandler.trigger_calculate_ranking, "trigger_ranking")
        self.rpc_server.serve_forever()

    def run(self):
        if config.log:
            logger.info("save output to log file {} ---- timestamp {}".format(os.path.abspath(_file), datetime.now()))
            if os.path.isfile(config.log):
                _file = config.log
            else:
                _file = os.path.join(config.basedir, config.log)

            # open 2 file descriptor
            file_fd = os.open(_file, os.O_RDWR | os.O_CREAT | os.O_APPEND)
            # put /dev/null fds on 1 and 2
            os.dup2(file_fd, 1)
            os.dup2(file_fd, 2)

        threads = []
        process_thread = Thread(target=self.controller_sdr)
        api_handler_thread = Process(target=self.setup_rpc_server)

        # threads.append(self.process_thread)
        threads.append(api_handler_thread)
        threads.append(process_thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            helper.my_join(thread)
