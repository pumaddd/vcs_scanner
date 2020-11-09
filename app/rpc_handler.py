from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
from app import session
from app.database import API
from app.models import decode_ranking
from app.cell_select import CellSelect, CellNeighbor
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)
    
    @staticmethod
    def trigger_calculate_ranking(round, index_round):
        # Get entries info from round
        logging.info("Get call to calculate round {}".format(round))
        entries = []
        try:
            entries = API.get_round_entries(round=round, index_round=index_round)
        except Exception as e:
            logger.error("Error exception:")
            logger.info(e)
            import sys, traceback
            traceback.print_exc(file=sys.stdout)
            session.rollback()

        if not entries:
            return entries["entries"]
        
        sample_offset = entries["round_time"]

        # Create cell select install to calculate criteria
        cells_select = CellSelect()

        # Create cell neighbor struct is module for cell select ranking
        cellneighbors = []
        cells_followed = []
        for neighbor in entries["entries"]:
            if neighbor.cell_arfcn in cells_followed:
                logger.info("Cell alrady in follow list {}".format(cells_followed))
                continue

            cellneighbor = CellNeighbor(si_struct=None, 
                    arfcn=neighbor.cell_arfcn,
                    rxlev_avg_dbm=-1,
                    rxlev_count=-1,
                    start_sample=-1,
                    snr_avg_level=-1,
                    )
            cells_followed.append(neighbor.cell_arfcn)
            cellneighbor.cell_select_id = neighbor.cell_select_info
            cellneighbors.append(cellneighbor)
            cells_select.insert_cell_entry(cellneighbor)

        sorted_cells = cells_select.sort_select_cell(sorttime=sample_offset, index_round=index_round)
        
        for channel_entry in cells_select.cells:
            channel_info = decode_ranking(
                arfcn=channel_entry.arfcn,
                rank=cells_select.cells.index(channel_entry) + 1,
                round=round,
                timestamp=datetime.now(),
                rxlev_debug_criteria=channel_entry.rxlev_criteria, 
                snr_debug_criteria=channel_entry.snr_criteria,
                ber_debug_criteria=channel_entry.ber_criteria,
                cell_select_info=channel_entry.cell_select_id,
                index_round=index_round,
            )
            session.add(channel_info)

        logger.info("Out put arfcn after sorted {}".format(sorted_cells))
        session.commit()
        return sorted_cells
 
