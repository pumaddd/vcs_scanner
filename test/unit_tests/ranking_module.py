import numpy as np
import matplotlib.pyplot as plt
import sys, os
import logging

from app import cell_select
from app.cell_select import CellNeighbor
from app.database import API
from app.database import MySQL_external
from test import ch

__info__ = {
    'name': 'ranking_module',
    'role': 'unit_test',
    'module': "app.cell_select",
    'description': 'return true if ranking of cell sorted as expected',
    }

class TestModule():
    
    DATA_INPUT = {
            "round":    9,
            "sample_offset":    23774953,
            "entries":[
                {"arfcn":  53, "rank": 1, "average_pwr": -55, "snr_avg_level": 222, "burst_count": 1902},
                {"arfcn":  55, "rank": 2, "average_pwr": -60, "snr_avg_level": 208, "burst_count": 3703},
                {"arfcn":  47, "rank": 3, "average_pwr": -64, "snr_avg_level": 162, "burst_count": 2138},
                {"arfcn":  58, "rank": 4, "average_pwr": -68, "snr_avg_level": 137, "burst_count": 4166},
                {"arfcn":  46, "rank": 5, "average_pwr": -68, "snr_avg_level": 112, "burst_count": 2233},
                ]
            }

    def __init__(self):
            self.logger = logging.getLogger(__name__)
            #self.logger.addHandler(ch)
            pass

    def run_test(self):
        cells = cell_select.CellSelect()

        # create cell neighbor struct is module for cell select ranking
        cellneighbors = []
        for neighbor in self.DATA_INPUT["entries"]:
            cellneighbor = cell_select.CellNeighbor(si_struct=None, 
                    arfcn=neighbor["arfcn"], 
                    rxlev_avg_dbm=neighbor["average_pwr"],
                    rxlev_count=neighbor["burst_count"],
                    start_sample=self.DATA_INPUT["sample_offset"],
                    snr_avg_level=neighbor["snr_avg_level"],
                    )
            cellneighbors.append(cellneighbor)
            cells.insert_cell_entry(cellneighbor)

        sorted_cells = cells.sort_select_cell(sorttime=self.DATA_INPUT["sample_offset"])
        print("[TEST OUTPUT]get list after sorted {}".format(sorted_cells))

        for cell_input in self.DATA_INPUT["entries"]:
            # sorted cell return list with index from 0 is the strongest so we add 1 and compare with input
            if cell_input["rank"] != sorted_cells.index(cell_input["arfcn"]) + 1:
                print("[TEST FAIL]get arfcn {} return after sort with rank {} expect {}".format(cell_input["arfcn"], sorted_cells.index(cell_input["arfcn"]) + 1, cell_input["rank"]))
                return False

        print("[TEST PASS]out put arfcn after sorted {}".format(sorted_cells))
        return True
   
    def module_test(self, arfcns=[], attr="rxlev", start=0, stop=-1, index_round=0):
        # Loop over scanner info and calculate attr ranking information
        if attr == "rxlev":
            criteria_func = CellNeighbor.calculate_rxlev_criteria
            attr_range = CellNeighbor.RXLEV_RANGE[1] - CellNeighbor.RXLEV_RANGE[0]
            query_func = API.get_rounds_rxlev_info
        elif attr == "snr":
            criteria_func = CellNeighbor.calculate_snr_criteria
            attr_range = CellNeighbor.SNR_RANGE[1]  - CellNeighbor.SNR_RANGE[0]
            query_func = API.get_rounds_snr_info
        elif attr == "ber":
            criteria_func = CellNeighbor.calculate_ber_criteria
            attr_range = CellNeighbor.BER_RANGE[1] - CellNeighbor.BER_RANGE[0]
            query_func = MySQL_external.get_rounds_ber_info
        elif attr == "random":
            criteria_func = CellNeighbor.calculate_snr_criteria
            attr_range = CellNeighbor.SNR_RANGE[1]  - CellNeighbor.SNR_RANGE[0]
            db_wrapper = random_generator_wrapper(arfcns=arfcns, stop_offset=stop)
            API.get_rounds_info = db_wrapper.get_test_rounds_info
        else:
            raise ValueError("Attr not valid !!!")

        fig, ax = plt.subplots(nrows=2, ncols=1)
        results = [] 
        if not arfcns:
            cells = API.get_cells_info(index_round=index_round)
            arfcns = [cell["arfcn"] for cell in cells]
        for arfcn in arfcns:
            # Query return array of attribute to estimate algorithm
            query = API.get_rounds_sample(stop_offset=stop, index_round=index_round)
            query_attr = query_func(arfcn=arfcn, start_offset=start, stop_offset=stop, index_round=index_round)

            x_axis_attr = []
            y_axis_attr = []
            if attr == "ber":
                query = [(round[1], query_attr.index(round)) for round in query_attr]
                round_sample_index = [round[1] for round in query]
            else:
                round_sample_index = [point[2]  for point in query_attr]
            
            self.logger.info("[MODULE RANKING TEST] get query:\n{}".format(query))
            criteria_list = []
            for round in query:
                criteria = criteria_func(arfcn=arfcn, calculate_time=round[0], index_round=index_round)
                criteria_list.append((criteria, round[0]))
                if round[1] in round_sample_index:
                    x_axis_attr.append(query_attr[round_sample_index.index(round[1])][1])
                    y_axis_attr.append(query_attr[round_sample_index.index(round[1])][0])
                else:
                    x_axis_attr.append(np.nan)
                    y_axis_attr.append(np.nan)
            print("[RANKING MODULE]debug arfcn {} x axis attr {}".format(arfcn, x_axis_attr)) 
            print("[RANKING MODULE]debug arfcn {} y axis attr {}".format(arfcn, y_axis_attr)) 
            self.logger.info("[MODULE RANKING TEST]Plot attribute:\n{}".format(round_sample_index))

            #self.logger.info("[MODULE RANKING TEST]Plot ranking:\n{}".format(criteria_list))
            entropy_attr = 0
            for y1, y2 in zip(y_axis_attr[:-1], y_axis_attr[1:]):
                entropy_attr += abs(y2 - y1)
            
            entropy_criteria = 0
            x_axis_criteria = []
            y_axis_criteria = []
            for point in criteria_list:
                x_axis_criteria.append(point[1] if point[0] > 0 else np.nan)
                y_axis_criteria.append(point[0] if point[0] > 0 else np.nan)
            for y1, y2 in zip(y_axis_criteria[:-1], y_axis_criteria[1:]):
                entropy_criteria += abs(y2 - y1)
 
            result = {
                "arfcn":    arfcn,
                "entropy_attr": (entropy_attr / attr_range),
                "entropy_criteria": (entropy_criteria / 100),
                }
            results.append(result)
            ax[0].plot(x_axis_attr, y_axis_attr, linestyle='solid', label="{} {}".format(attr, arfcn))
            ax[1].plot(x_axis_criteria, y_axis_criteria, linestyle='solid', label="criteria {}".format(arfcn))
        
        # Print result calculate from graph 
        for result in results:
            self.logger.info("entropy {} calculated for arfcn: {} attribute entroy: {} -- criteria entropy: {}"
                    .format(attr, result["arfcn"], result["entropy_attr"], result["entropy_criteria"]))
 
        #plt.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=None, hspace=None)
        ax[0].legend(loc="upper left", prop={'size': 10})
        ax[1].legend(loc="upper left", prop={'size': 10})
        plt.subplots_adjust(top=0.98, bottom=0.02, left=0.02, right=0.98, hspace=0.2, wspace=0.2)
        plt.show()
  
    def calculate_ranking_test(self, arfcns=[724], start=0, stop=-1):
        # Loop over scanner info and calculate attr ranking information
        results = []
        fig, ax = plt.subplots(nrows=2, ncols=1)
        for arfcn in arfcns:
            # Query return array of attribute to estimate algorithm
            query = API.get_rounds_info(arfcn=arfcn, start_offset=start, stop_offset=stop, attr=attr)

            self.logger.info("[MODULE RANKING TEST]Plot attribute:\n{}".format(query))
            criteria_list = []
            for round in query:
                criteria = criteria_func(arfcn=arfcn, calculate_time=round[1], attr_value=round[0])
                criteria_list.append((criteria, round[1]))
            
            #self.logger.info("[MODULE RANKING TEST]Plot ranking:\n{}".format(criteria_list))
            x_axis_attr = [point[1] for point in query]
            y_axis_attr = [point[0] for point in query]
            entropy_attr = 0
            for y1, y2 in zip(y_axis_attr[:-1], y_axis_attr[1:]):
                entropy_attr += abs(y2 - y1)
            
            entropy_criteria = 0
            x_axis_criteria = [point[1] for point in criteria_list]
            y_axis_criteria = [point[0] for point in criteria_list]
            for y1, y2 in zip(y_axis_criteria[:-1], y_axis_criteria[1:]):
                entropy_criteria += abs(y2 - y1)
 
            result = {
                "arfcn":    arfcn,
                "entropy_attr": (entropy_attr / attr_range),
                "entropy_criteria": (entropy_criteria / 100),
                }
            results.append(result)
            ax[0].plot(x_axis_attr, y_axis_attr, linestyle='solid', label="{} {}".format(attr, arfcn))
            ax[1].plot(x_axis_criteria, y_axis_criteria, linestyle='solid', label="criteria {}".format(arfcn))
        
        # Print result calculate from graph 
        for result in results:
            self.logger.info("entropy {} calculated for arfcn: {} attribute entroy: {} -- criteria entropy: {}"
                    .format(attr, result["arfcn"], result["entropy_attr"], result["entropy_criteria"]))
 
        #plt.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=None, hspace=None)
        ax[0].legend(loc="upper left", prop={'size': 10})
        ax[1].legend(loc="upper left", prop={'size': 10})
        plt.subplots_adjust(top=0.98, bottom=0.02, left=0.02, right=0.98, hspace=0.2, wspace=0.2)
        plt.show()
 
class random_generator_wrapper():
    def __init__(self, arfcns=[55], num_sample=100, random_distribute="random", stop_offset=-1, attr_ref="rxlev"):
        
        if random_distribute == "poisson":
            random_func = np.random.poisson
        elif random_distribute == "normal":
            random_func = np.random.normal
        elif random_distribute == "random":
            random_func = np.random.ranf

        self.generated_tables = []
        for arfcn in arfcns:
            table = {"arfcn":  arfcn}
            _refence = API.get_rounds_info(arfcn=arfcn, stop_offset=stop_offset, attr=attr_ref)
            _size = len(_refence)
            random_l = random_func(size=_size)
            random_table = zip(random_l, [value[1] for value in _refence])
            table.update({"random_table":  random_table})
            self.generated_tables.append(table)
            print("generate table: {}".format(table))
       
    def get_test_rounds_info(self, arfcn=None, start_offset=0, stop_offset=-1, **karg):
        random_table = []
        for table in self.generated_tables:
            if table["arfcn"] == arfcn:
                random_table = table["random_table"]
        if not random_table:
            return []
        
        round_info = []
        if stop_offset == -1:
            return [round for round in random_table] 

        for round in random_table:
            if round[1] < stop_offset and round[1] > start_offset:
                round_info.append(round)
        return round_info

