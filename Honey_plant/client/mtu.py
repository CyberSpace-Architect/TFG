import logging
import threading
import time

from pyModbusTCP.client import ModbusClient
from typing import List

from client.customlogging import CustomLogger
from servers.plc1.honeyplc1 import HoneyPLC1
from servers.plc2.honeyplc2 import HoneyPLC2
from servers.plc3.honeyplc3 import HoneyPLC3
from servers.plc4.honeyplc4 import HoneyPLC4
from servers.plc5.honeyplc5 import HoneyPLC5


class MTU:
    # client parameters
    slaves_address = '127.0.0.1'
    refresh_rate = 3

    def __init__(self):
        pass

    def logic_plc1(self, plc1_client: ModbusClient, logger: logging.Logger):
        regs: List[float] = plc1_client.read_holding_registers(0, 3)
        regs[2] = regs[2] / 100

        b1, v1, tank_lvl = regs
        logger.info(f'PLC1 values:\n\tb1: {b1},\n\tv1: {v1},\n\ttank_lvl: {tank_lvl}')

        if tank_lvl > HoneyPLC1 .tank_thresholds['WARNING_HIGH']:
            if b1 != 0:
                plc1_client.write_single_register(HoneyPLC1 .data_addresses['b1'], 0)
                logger.warning(f'Raw water tank almost full --> Input pump b1 turned off')
            if v1 != 1:
                plc1_client.write_single_register(HoneyPLC1 .data_addresses['v1'], 1)
                logger.warning(f'Raw water tank almost full --> Output valve v1 opened')
        elif tank_lvl < HoneyPLC1 .tank_thresholds['WARNING_LOW']:
            if b1 != 1:
                plc1_client.write_single_register(HoneyPLC1 .data_addresses['b1'], 1)
                logger.warning(f'Raw water tank almost empty --> Input pump b1 turned on')
            if v1 != 0:
                plc1_client.write_single_register(HoneyPLC1 .data_addresses['v1'], 0)
                logger.warning(f'Raw water tank almost empty --> Output valve v1 closed')
        else:
            if v1 != 1:
                plc1_client.write_single_register(HoneyPLC1 .data_addresses['v1'], 1)
                logger.warning(f'Raw water tank with enough water --> Output valve v1 opened')

        time.sleep(self.refresh_rate)


    def logic_plc2(self, plc1_client: ModbusClient, plc2_client: ModbusClient, logger: logging.Logger):
        v1 = plc1_client.read_holding_registers(1, 1)[0]
        regs: List[float] = plc2_client.read_holding_registers(0, 7)
        regs[3] = regs[3] / 100

        b2, b3, s1_flow, s1_pressure, s2_flow, s2_conductivity, s2_salt = regs
        logger.info(f'PLC2 values:\n\tb2: {b2},\n\tb3: {b3},\n\ts1_flow: {s1_flow}, \
                    \n\ts1_pressure: {s1_pressure},\n\ts2_flow: {s2_flow}, \
                    \n\ts2_conductivity: {s2_conductivity},\n\ts2_salt: {s2_salt}')

        if v1 != 0:
            if b2 != 1:
                plc2_client.write_single_register(HoneyPLC2 .data_addresses['b2'], 1)
                logger.warning(f'Raw water output valve v1 open --> Water b2 pump turned on')
            if b3 != 1:
                plc2_client.write_single_register(HoneyPLC2 .data_addresses['b3'], 1)
                logger.warning(f'Raw water output valve v1 open --> Coagulant b3 pump turned on')
        else:
            if b2 != 0:
                plc2_client.write_single_register(HoneyPLC2 .data_addresses['b2'], 0)
                logger.warning(f'Raw water output valve v1 closed --> Water b2 pump turned off')
            if b3 != 0:
                plc2_client.write_single_register(HoneyPLC2 .data_addresses['b3'], 0)
                logger.warning(f'Raw water output valve v1 closed --> Coagulant b3 pump turned off')

        time.sleep(self.refresh_rate)


    def logic_plc3(self, plc2_client: ModbusClient, plc3_client: ModbusClient, logger: logging.Logger):
        s2_flow, s2_conductivity, s2_salt = plc2_client.read_holding_registers(4, 3)

        regs: List[float] = plc3_client.read_holding_registers(0, 12)

        regs[2] = regs[2] / 100
        regs[3] = regs[3] / 100
        regs[4] = regs[4] / 100
        regs[6] = regs[6] / 100
        regs[7] = regs[7] / 100
        regs[8] = regs[8] / 100
        regs[9] = regs[9] / 10
        regs[10] = regs[10] / 100

        b4, s3_flow, s3_pressure, s3_conductivity, s3_salt, s4_flow, s4_conductivity, \
            s4_salt, s4_ph, s4_temperature, s4_turbidity, s5_flow = regs

        logger.info(f'PLC3 values:\n\tb4: {b4},\n\ts3_flow: {s3_flow},\n\ts3_pressure: {s3_pressure}, \
                    \n\ts3_conductivity: {s3_conductivity},\n\ts3_salt: {s3_salt}, \n\ts4_flow: {s4_flow}, \
                    \n\ts4_conductivity: {s4_conductivity},\n\ts4_salt: {s4_salt}\n\ts4_ph: {s4_ph}, \
                    \n\ts4_temperature: {s4_temperature},\n\ts4_turbidity: {s4_turbidity},\n\ts5_flow: {s5_flow}')

        if s2_flow > 0:
            if s2_salt > 6000:
                plc3_client.write_single_register(HoneyPLC3 .data_addresses['b4'], 0)
                logger.warning(f'Detected inadequate filtered water inflow in s2 --> Pump b4 turned off')
            elif b4 != 1:
                plc3_client.write_single_register(HoneyPLC3 .data_addresses['b4'], 1)
                logger.warning(f'Detected adequate filtered water inflow in s2 --> Pump b4 turned on')
        else:
            if b4 != 0:
                plc3_client.write_single_register(HoneyPLC3 .data_addresses['b4'], 0)
                logger.warning(f'Not detected filtered water inflow in s2 --> Pump b4 turned off')

        time.sleep(self.refresh_rate)


    def logic_plc4(self, plc3_client: ModbusClient, plc4_client: ModbusClient, logger: logging.Logger):
        s4_flow = plc3_client.read_holding_registers(5, 1)[0]
        regs: List[float] = plc4_client.read_holding_registers(0, 10)

        regs[5] = regs[5] / 100
        regs[6] = regs[6] / 10
        regs[7] = regs[7] / 100
        regs[8] = regs[8] / 10
        regs[9] = regs[9] / 100

        s4_flow_plc4, v2, v3, v4, s6_flow, s6_free_chlorine, s6_conductivity, \
            s6_ph, s6_temperature, s6_turbidity = regs

        logger.info(f'PLC4 values:\n\ts4_flow: {s4_flow_plc4},\n\tv2: {v2},\n\tv3: {v3},\n\tv4: {v4}, \
                    \n\ts6_flow: {s6_flow},\n\ts6_free_chlorine: {s6_free_chlorine}, \
                    \n\ts6_conductivity: {s6_conductivity}, \n\ts6_ph: {s6_ph}, \
                    \n\ts6_temperature: {s6_temperature},\n\ts6_turbidity: {s6_turbidity}')

        if s4_flow > 0:
            if s4_flow_plc4 != s4_flow:
                plc4_client.write_single_register(HoneyPLC4 .data_addresses['s4_flow'], s4_flow)
            if v2 != 1:
                plc4_client.write_single_register(HoneyPLC4 .data_addresses['v2'], 1)
                logger.warning(f'Detected filtered water inflow in s4 --> NaClO valve v2 opened')
            if v3 != 1:
                plc4_client.write_single_register(HoneyPLC4 .data_addresses['v3'], 1)
                logger.warning(f'Detected filtered water inflow in s4 --> CaO valve v3 opened')
            if v4 != 1:
                plc4_client.write_single_register(HoneyPLC4 .data_addresses['v4'], 1)
                logger.warning(f'Detected filtered water inflow in s4 --> CO2 valve v4 opened')
        else:
            if s4_flow_plc4 > 0:
                plc4_client.write_single_register(HoneyPLC4 .data_addresses['s4_flow'], 0)
            if v2 != 0:
                plc4_client.write_single_register(HoneyPLC4 .data_addresses['v2'], 0)
                logger.warning(f'Not detected filtered water inflow in s4 --> NaClO valve v2 closed')
            if v3 != 0:
                plc4_client.write_single_register(HoneyPLC4 .data_addresses['v3'], 0)
                logger.warning(f'Not detected filtered water inflow in s4 --> CaO valve v3 closed')
            if v4 != 0:
                plc4_client.write_single_register(HoneyPLC4 .data_addresses['v4'], 0)
                logger.warning(f'Not detected filtered water inflow in s4 --> CO2 valve v4 closed')

        time.sleep(self.refresh_rate)


    def logic_plc5(self, plc4_client: ModbusClient, plc5_client: ModbusClient, logger: logging.Logger):
        s6_flow, s6_free_chlorine, s6_conductivity, \
            s6_ph, s6_temperature, s6_turbidity = plc4_client.read_holding_registers(4, 6)

        s6_free_chlorine = s6_free_chlorine / 100
        s6_conductivity = s6_conductivity / 10
        s6_ph = s6_ph / 100
        s6_temperature = s6_temperature / 10
        s6_turbidity = s6_turbidity / 100

        regs: List[float] = plc5_client.read_holding_registers(0, 3)
        regs[2] = regs[2] / 100

        v5, b5, tank_lvl = regs
        logger.info(f'PLC5 values:\n\tv5: {v5},\n\tb5: {b5},\n\ttank_lvl: {tank_lvl}')

        # First, check if water inflow is potable, because no matter what, not potable
        # water cannot enter the tank
        if s6_flow < 0 or not self.fulfills_potability_standards(s6_free_chlorine, s6_conductivity,
                                                            s6_ph, s6_temperature, s6_turbidity):
            if v5 == 1:
                plc5_client.write_single_register(HoneyPLC5 .data_addresses['v5'], 0)
                logger.warning(f'Product water tank inflow is not suitable --> Input valve v5 closed')
        else:
            if tank_lvl > HoneyPLC5 .tank_thresholds['WARNING_HIGH']:
                if v5 != 0:
                    plc5_client.write_single_register(HoneyPLC5 .data_addresses['v5'], 0)
                    logger.warning(f'Product water tank almost full --> Input valve v5 closed')
                if b5 != 1:
                    plc5_client.write_single_register(HoneyPLC5 .data_addresses['b5'], 1)
                    logger.warning(f'Product water tank almost full --> Output pump b4 turned on')
            elif tank_lvl < HoneyPLC5 .tank_thresholds['WARNING_LOW']:
                if v5 != 1:
                    plc5_client.write_single_register(HoneyPLC5 .data_addresses['v5'], 1)
                    logger.warning(f'Product water tank almost empty, water inflow active with appropriate quality '
                                   f'--> Input valve v5 opened')
                if b5 != 0:
                    plc5_client.write_single_register(HoneyPLC5 .data_addresses['b5'], 0)
                    logger.warning(f'Product water tank almost empty --> Output pump b4 turned off')
            else:
                if b5 != 1:
                    plc5_client.write_single_register(HoneyPLC5 .data_addresses['b5'], 1)
                    logger.warning(f'Product water tank with enough water --> Output pump b4 turned on')

            time.sleep(self.refresh_rate)


    @staticmethod
    def fulfills_potability_standards(free_chlorine: float, conductivity: float, ph: float, temperature: float,
                                      turbidity: float):
        # Page 66 Calidad del agua de consumo humano en España 2021
        return in_float_range(free_chlorine, 0.2, 1) and in_float_range(conductivity, 0.1, 2499) \
               and in_float_range(ph, 6.5, 9.5) and in_float_range(temperature, 10, 25) \
               and in_float_range(turbidity, 0.1, 1)


    def start(self):
        plc1_client = ModbusClient(host='plc1_server', port=502, auto_open=True)
        plc2_client = ModbusClient(host='plc2_server', port=502, auto_open=True)
        plc3_client = ModbusClient(host='plc3_server', port=502, auto_open=True)
        plc4_client = ModbusClient(host='plc4_server', port=502, auto_open=True)
        plc5_client = ModbusClient(host='plc5_server', port=502, auto_open=True)

        logger = getattr(CustomLogger("Scada"), 'logger')

        while True:
            t1 = threading.Thread(target=self.logic_plc1(plc1_client, logger))
            t1.start()
            t2 = threading.Thread(target=self.logic_plc2(plc1_client, plc2_client, logger))
            t2.start()
            t3 = threading.Thread(target=self.logic_plc3(plc2_client, plc3_client, logger))
            t3.start()
            t4 = threading.Thread(target=self.logic_plc4(plc3_client, plc4_client, logger))
            t4.start()
            t5 = threading.Thread(target=self.logic_plc5(plc4_client, plc5_client, logger))
            t5.start()


def in_float_range(value: float, min_value:float, max_value:float):
    return min_value < value < max_value


if __name__ == '__main__':
    mtu = MTU()
    mtu.start()
