import time
import random
from servers.core import *
from servers.jsonlogging import *


class HoneyPLC2(HoneyPLC):

    # Plc I/O data
    data = {
        'b2': 0,
        'b3': 0,
        's1_flow': 0,
        's1_pressure': 0,
        's2_flow': 0,
        's2_conductivity': 0,
        's2_salt': 0
    }

    data_addresses = {
        'b2': 0,
        'b3': 1,
        's1_flow': 2,
        's1_pressure': 3,
        's2_flow': 4,
        's2_conductivity': 5,
        's2_salt': 6
    }

    def __init__(self):
        super().__init__()

    def run_behaviour(self):
        """ Physical process function (pre-treatment filtering process) """
        print("Starting physical process\n")

        inflow = 6336        # m3/h 11 pumps (576m3/h)
        pressure = 4.12      # bars
        outflow = 6336       # m3/h 11 pumps (576m3/h)

        while True:
            if self.data['b2'] == 1:
                self.data['s1_flow'] = inflow
                self.data['s1_pressure'] = int(pressure * 100)    # save decimal value as int in register
            else:
                self.data['s1_flow'] = 0
                self.data['s1_pressure'] = 0

            if self.data['s1_flow'] >= inflow and self.data['s1_pressure'] / 100 >= pressure:
                self.data['s2_flow'] = outflow

                if self.data['b3'] == 1:
                    # Calculate salinity based on values for seawater pretreated (Table 1 of "Correlation between conductivity
                    # and total dissolved solid in various type of water: A review"
                    self.data['s2_conductivity'] = int(round(random.uniform(6000, 10000), 1))
                    k = round(random.uniform(0.55, 0.60), 2)
                    self.data['s2_salt'] = int(round(k * self.data['s2_conductivity']/10, 1))
                else:
                    # Calculate salinity based on values for seawater not properly pretreated"
                    self.data['s2_conductivity'] = int(round(random.uniform(35000, 45000), 1))
                    k = round(random.uniform(0.60, 0.65), 2)
                    self.data['s2_salt'] = int(round(k * self.data['s2_conductivity']/10, 1))
            else:
                self.data['s2_flow'] = 0

            time.sleep(1)


if __name__ == '__main__':
    honeyplc2 = HoneyPLC2()
    honeyplc2.start()