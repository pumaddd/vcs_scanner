from test import database
from test import logger

import numpy as np
import matplotlib.pyplot as plt

class TargetMobile():
    RXLEV_LIMIT = -90

    def __init__(self):
        pass

    def plot_selected_arfcns(self, arfcns=[55], round_limit=528):
        logger.info("Plot mobile with rounds number {}".format(round_limit))
        fig, ax = plt.subplots(nrows=2, ncols=1)
        for arfcn in arfcns:
            target_data = database.get_target_rounds_info(arfcn=arfcn, round_limit=round_limit)
            x_axis_attr = [point[1] for point in target_data]
            y_axis_attr = [point[0] for point in target_data]

            ax[0].plot(x_axis_attr, y_axis_attr, linestyle='dashed', label="rxlev {}".format(arfcn))
            ax[1].plot(x_axis_attr, y_axis_attr, linestyle='dashed', label="rxlev {}".format(arfcn))
        
        # Plot main camping cell
        camp_cell = database.get_target_camping(round_limit=round_limit)
        x_axis_attr = [point[1] for point in camp_cell]
        y_axis_attr = [point[0] for point in camp_cell]
        ax[1].plot(x_axis_attr, y_axis_attr, linestyle='-', label="rxlev cell", linewidth=2, color="red")
        
        logger.info("camping cell at {}".format([round[2] for round in camp_cell]))
        ax[0].legend(loc="upper left", prop={'size': 10})
        ax[1].legend(loc="upper left", prop={'size': 10})
        plt.subplots_adjust(top=0.98, bottom=0.02, left=0.02, right=0.98, hspace=0.2, wspace=0.2)
        plt.show()
    
    def plot_mobile_database(self, network="VIETTEL", round_limit=528):

        fig, ax = plt.subplots(nrows=2, ncols=1)
        # Get arfcn in database and plot
        arfcns = database.get_database_mobile_arfcns()
        reselect_points = []
        for arfcn in arfcns:
            target_data = database.get_target_rounds_info(arfcn=arfcn, round_limit=round_limit)
            x_axis_attr = []
            y_axis_attr = []
            last_round = 0
            for point in target_data:
                if point[2] > last_round + 1:
                    x_axis_attr.append(np.nan)
                    y_axis_attr.append(np.nan)

                x_axis_attr.append(point[1])
                y_axis_attr.append(point[0] if int(point[0]) > TargetMobile.RXLEV_LIMIT else TargetMobile.RXLEV_LIMIT)
                last_round=point[2]

            ax[0].plot(x_axis_attr, y_axis_attr, linestyle='dashed', label="rxlev {}".format(arfcn))
            ax[1].plot(x_axis_attr, y_axis_attr, linestyle='dashed', label="rxlev {}".format(arfcn))
        
        # Plot main camping cell
        x_axis_attr = []
        y_axis_attr = []
        camp_cell = database.get_target_camping(round_limit=round_limit)
        serving_arfcn = 0
        for point in camp_cell:
            x_axis_attr.append(point[1])
            y_axis_attr.append(point[0])
            # Index cell at reselected point
            if point[2] != serving_arfcn:
                reselect_points.append(point)
                ax[1].annotate(point[2], (point[1], point[0]))
                ax[1].plot(point[1], point[0], 'o')
                serving_arfcn = point[2]
        
        ax[1].plot(x_axis_attr, y_axis_attr, linestyle='-', label="rxlev cell", linewidth=2, color="red")
        
        logger.info("camping cell at {}".format([round[2] for round in camp_cell]))
        ax[0].legend(loc="upper left", prop={'size': 10})
        ax[1].legend(loc="upper left", prop={'size': 10})
        plt.subplots_adjust(top=0.98, bottom=0.02, left=0.02, right=0.98, hspace=0.2, wspace=0.2)
        plt.show()
 
