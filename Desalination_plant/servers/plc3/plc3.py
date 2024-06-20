import random
import time
from servers.core import PLC, PLCDataBank, key_from_value


class PLC3(PLC):

    # Plc I/O data
    data = {
        'b4': 0,
        's3_flow': 0,
        's3_pressure': 0,
        's3_conductivity': 0,
        's3_salt': 0,
        's4_flow': 0,
        's4_conductivity': 0,
        's4_salt': 0,
        's4_ph': 0,
        's4_temperature': 0,
        's4_turbidity': 0,
        's5_flow': 0
    }

    data_addresses = {
        'b4': 0,
        's3_flow': 1,
        's3_pressure': 2,
        's3_conductivity': 3,
        's3_salt': 4,
        's4_flow': 5,
        's4_conductivity': 6,
        's4_salt': 7,
        's4_ph': 8,
        's4_temperature': 9,
        's4_turbidity': 10,
        's5_flow': 11
    }

    def __init__(self):
        super().__init__()

    def run_behaviour(self):
        """ Physical process function (desalination through reverse osmosis process) """
        print("Starting physical process\n")

        inflow = 6336           # m3/h 11 pumps (576m3/h)
        pressure = 68.64        # bars
        conversion_rate = 0.45  # product water flow rate from raw water flow (Page 63 Guía desalación)

        while True:
            # Update s3 values
            if self.data['b4'] == 1:
                self.data['s3_flow'] = inflow
                self.data['s3_pressure'] = int(pressure * 100)  # save decimal value as int in register

                # Calculate salinity based on values for seawater pretreated (Table 1 of "Correlation between conductivity
                # and total dissolved solid in various type of water: A review"
                self.data['s3_conductivity'] = int(round(random.uniform(500, 3000), 1) * 10)
                k = round(random.uniform(0.55, 0.75), 2)
                self.data['s3_salt'] = int(round(k * self.data['s3_conductivity'] / 10, 1) * 10)
            else:
                self.data['s3_flow'] = 0
                self.data['s3_pressure'] = 0
                self.data['s3_conductivity'] = 0
                self.data['s3_salt'] = 0

            # Update s4 and s5 values
            if self.data['s3_flow'] >= inflow and self.data['s3_pressure'] / 100 >= pressure:
                self.data['s4_flow'] = int(round(self.data['s3_flow'] * conversion_rate))
                self.data['s5_flow'] = int(round(self.data['s3_flow'] * (1 - conversion_rate)))

                # Calculate salinity based on values for distilled water after Reverse Osmosis
                self.data['s4_conductivity'] = int(round(random.uniform(1, 10), 1) * 10)
                k = 0.5
                self.data['s4_salt'] = int(round(k * self.data['s4_conductivity'], 1) * 10)
                self.data['s4_ph'] = int(round(random.uniform(5, 6), 2) * 100)              # Page 94 Guía desalación
                self.data['s4_temperature'] = int(round(random.uniform(10, 25), 1) * 10)    # Page 156 Guia desalación
                self.data['s4_turbidity'] = int(round(random.uniform(0.1, 1.0), 2) * 100)   # Page 172 informe AC 2021
            else:
                # No water inflow ==> No water outflow ==> All values = 0
                self.data['s4_flow'] = 0
                self.data['s5_flow'] = 0
                self.data['s4_conductivity'] = 0
                self.data['s4_salt'] = 0
                self.data['s4_ph'] = 0
                self.data['s4_temperature'] = 0
                self.data['s4_turbidity'] = 0

            time.sleep(1)


if __name__ == '__main__':
    plc3 = PLC3()
    plc3.start()