import random
import time
from servers.core import PLC, PLCDataBank, key_from_value


class PLC4(PLC):

    # Plc I/O data
    data = {
        's4_flow': 0,
        'v2': 0,
        'v3': 0,
        'v4': 0,
        's6_flow': 0,
        's6_free_chlorine': 0,
        's6_conductivity': 0,
        's6_ph': 0,
        's6_temperature': 0,
        's6_turbidity': 0
    }

    data_addresses = {
        's4_flow': 0,
        'v2': 1,
        'v3': 2,
        'v4': 3,
        's6_flow': 4,
        's6_free_chlorine': 5,
        's6_conductivity': 6,
        's6_ph': 7,
        's6_temperature': 8,
        's6_turbidity': 9,
    }

    def __init__(self):
        super().__init__()

    def run_behaviour(self):
        """ Physical process function (post-treatment process) """
        print("Starting physical process\n")

        inflow = 2304  # m3/h 4 pumps (576m3/h)

        while True:
            # Update s6 values
            if self.data['s4_flow'] >= inflow:
                self.data['s6_temperature'] = int(round(random.uniform(19, 23), 1) * 10)   # Page 97 Guia desalacion
                self.data['s6_turbidity'] = int(round(random.uniform(0.1, 1.0), 2) * 100)  # Page 172 informe AC 2021
                self.data['s6_flow'] = self.data['s4_flow']

                # Depending on the application or not of each post-treatment chemical, water values will vary:
                # NaClO application increases free chlorine
                if self.data['v2'] == 1:
                    # Guias para la calidad del agua de consumo humano: Cuarta edicion pag 580 (min 0,2mg/l)
                    # y BOE-A-2003-3596 Anexo I ==> C (max 1mg/l)
                    self.data['s6_free_chlorine'] = int(round(random.uniform(0.2, 1), 2) * 100)
                else:
                    self.data['s6_free_chlorine'] = int(round(random.uniform(0.0, 0.19), 2) * 100)
                # CaO application increases conductivity and ph
                if self.data['v3'] == 1:
                    # Correlation between conductivity and total dissolved solids in various
                    # types of water: A review ==> Page 3
                    self.data['s6_conductivity'] = int(round(random.uniform(300, 800), 2) * 10)
                    # Reduced Lime Feeds: Effects on Operational Costs and Water Quality
                    self.data['s6_ph'] = int(round(random.uniform(10, 12), 2) * 100)
                else:
                    self.data['s6_conductivity'] = int(
                        round(random.uniform(100, 299), 2) * 10)  # Below range indicated above
                    self.data['s6_ph'] = int(round(random.uniform(5, 6), 2) * 100)  # Page 94 guia desalacion
                # CO2 application reduces ph
                if self.data['v4'] == 1:
                    self.data['s6_ph'] = int(round(random.uniform(8, 9), 2) * 100)  # Page 96 and 97 guia desalacion
            else:
                # No water inflow ==> No water outflow ==> All values=0
                self.data['s6_flow'] = 0
                self.data['s6_free_chlorine'] = 0
                self.data['s6_conductivity'] = 0
                self.data['s6_ph'] = 0
                self.data['s6_temperature'] = 0
                self.data['s6_turbidity'] = 0

            time.sleep(1)


if __name__ == '__main__':
    plc4 = PLC4()
    plc4.start()