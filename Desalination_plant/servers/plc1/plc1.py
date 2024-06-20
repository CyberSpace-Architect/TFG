import time
from servers.core import PLC, PLCDataBank, key_from_value


class PLC1(PLC):

    # Plc I/O data
    data = {
        'b1': 0,
        'v1': 0,
        'tank_lvl': 0
    }

    data_addresses = {
        'b1': 0,
        'v1': 1,
        'tank_lvl': 2
    }

    tank_thresholds = {
        # 'WARNING_HIGH': 2500,
        'WARNING_HIGH': 250,
        # 'WARNING_LOW': 500
        'WARNING_LOW': 50
    }

    def __init__(self):
        super().__init__()

    def run_behaviour(self):
        """ Physical process function (raw water tank process) """
        print("Starting physical process\n")

        # inflow = 0.48       # 1728m3/h = 0.48m3/s
        inflow = 3.36         # 7 input pumps
        # outflow = 0.16      # 576m3/h = 0.16m3/s
        outflow = 1.76        # 11 output pumps

        tank_lvl_decimal = self.data['tank_lvl'] / 100
        new_tank_lvl = tank_lvl_decimal if tank_lvl_decimal > 0 else 0.0  # lvl cannot be lower than 0

        while True:
            if self.data['b1'] == 1:
                new_tank_lvl += inflow
            if self.data['v1'] == 1:
                new_tank_lvl -= outflow if outflow < new_tank_lvl else 0.0  # lvl cannot be lower than 0

            self.data['tank_lvl'] = int(round(new_tank_lvl, 2) * 100)  # save decimal value as int in register
            time.sleep(1)


if __name__ == '__main__':
    plc1 = PLC1()
    plc1.start()