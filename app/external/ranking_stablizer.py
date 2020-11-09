import mysql.connector

class RakingModule():
    config = {
        'user': 'netsharing',
        'password': '12345678',
        'database': 'file.db',
        'host': '192.168.6.129',
        'raise_on_warnings': True
        }

    def __init__(self):
        self.round = 1
        self.current_selected = []

    def get_round_from_sample(self, sample=0):
        self.conn = mysql.connector.connect(**RakingModule.config)
        cursor = self.conn.cursor()
        cell_neighbors_query = "select * from scan_arfcn where round = \
                (select round from scan_arfcn where sample_offset < {} order by round desc limit 1)"
                .format(sample)

        cursor.execute(cell_neighbors_query)

        neighbors = self.cursor.fetchall()
        self.conn.close()    
        
        current_round = []
        for neighbor in neighbors:
            round_info = {
                    "id":   neighbor[0],
                    "arfcn":    neighbor[1],
                    "rank": neighbor[2],
                    "scan_level":   neighbor[3],
                    "round":    neighbor[4],
                    "average_pwr":  neighbor[5],
                    "pkt_number":   neighbor[6],
                    "timestamp":    neighbor[7],
                    "sample_offset":    neighbor[8],
                    "sniff_time": neighbor[9],
                    "round_counter":    neighbor[10],
                    "snr_avg_level":    neighbor[11],
                    }
            cell_select = CellSelect(round_info["arfcn"], round_info["average_pwr"], 
                    round_info["timestamp"], round_info["snr_avg_level"])
            current_round.append(cell_select)

        for channel in current_selected:


class CellSelect():
    def __init__(self, arfcn, average_pwr, timestamp, snr_avg_power):
        self.arfcn = arfcn
        self.average_pwr = average_pwr
        self.timestamp = timestamp
        self.snr_avg_power = snr_avg_power
        self.round_counter = 1

