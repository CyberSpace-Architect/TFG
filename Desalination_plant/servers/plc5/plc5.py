import time
from servers.core import PLC, PLCDataBank, key_from_value


class PLC5(PLC):

    # Plc I/O data
    data = {
        'v5': 0,
        'b5': 0,
        'tank_lvl': 0
    }

    data_addresses = {
        'v5': 0,
        'b5': 1,
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
        """ Physical process function (product water tank process) """
        print("Starting physical process\n")

        inflow = 0.64         # 2304m3/h = 0.64m3/s (4 pumps plc4)
        # outflow = 0.18      # 828m3/h = 0.24m3/s
        outflow = 0.72        # 2484m3/h = 0.72m3/s (3 output pumps)

        tank_lvl_decimal = self.data['tank_lvl'] / 100
        new_tank_lvl = tank_lvl_decimal if tank_lvl_decimal > 0 else 0.0  # lvl cannot be lower than 0

        while True:
            if self.data['v5'] == 1:
                new_tank_lvl += inflow
            if self.data['b5'] == 1:
                new_tank_lvl -= outflow if outflow < new_tank_lvl else 0.0  # lvl cannot be lower than 0

            self.data['tank_lvl'] = int(round(new_tank_lvl, 2) * 100)  # save decimal value as int in register
            time.sleep(1)


if __name__ == '__main__':
    plc5 = PLC5()
    plc5.start()