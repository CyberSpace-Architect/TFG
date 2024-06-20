import threading
import logging
from pyModbusTCP.server import ModbusServer, DataBank

class PLC:
    # server parameters
    host = '0.0.0.0'
    port = 502

    # Plc I/O data
    data: dict[str, int] = None
    data_addresses: dict[str, int] = None

    def __init__(self):
        # Create plc modbus server instance
        self.server = ModbusServer(host=PLC.host, port=PLC.port, data_bank=PLCDataBank(self))

        # Set logging config
        logging.basicConfig()
        logging.getLogger('pyModbusTCP.server').setLevel(logging.DEBUG)

    def run_modbus_server(self):
        logging.debug("Starting modbus server\n")
        self.server.start()

    def run_behaviour(self):
        logging.debug("Starting physical process\n")
        pass

    def start(self):
        t1 = threading.Thread(target=self.run_behaviour)
        t1.start()

        self.run_modbus_server()

""" PLC class execution example: 
if __name__ == '__main__':
    plc = PLC()
    plc.start()
"""

class PLCDataBank(DataBank):
    def __init__(self, plc: PLC):
        self.plc = plc
        super().__init__()

    def get_holding_registers(self, address, number=1, srv_info=None):
        # get post-treatment sensors data
        # set holding registers with updated data before accessing them
        for i, value in enumerate(self.plc.data.values()):
            self._h_regs[i] = value
        try:
            return [self._h_regs[i] for i in range(address, address + number)]
        except KeyError:
            return 'ERROR setting holding registers'

    def set_holding_registers(self, address, word_list, srv_info=None):
        # ensure word_list values are int with a max bit length of 16
        word_list = [int(w) & 0xffff for w in word_list]
        # keep trace of any changes
        changes_list = []
        # ensure atomic update of internal data
        with self._h_regs_lock:
            if (address >= 0) and (address + len(word_list) <= len(self._h_regs)):
                for offset, c_value in enumerate(word_list):
                    c_address = address + offset
                    if self._h_regs[c_address] != c_value:
                        changes_list.append((c_address, self._h_regs[c_address], c_value))
                        self._h_regs[c_address] = c_value
                        # update local variable with new reg value
                        self.plc.data[key_from_value(self.plc.data_addresses, c_address)] = c_value
            else:
                return None
        # on server update
        if srv_info:
            # notify changes with on change method (after atomic update)
            for address, from_value, to_value in changes_list:
                self.on_holding_registers_change(address, from_value, to_value, srv_info=srv_info)
        return True


def key_from_value(dictionary: dict, value: object):
    """ Function to retrieve a key value given its value

    :param dictionary: dict
    :param value: object
    :return: object
    """
    key = None
    it_dict = iter(dictionary.items())

    while key is None:
        k, v = next(it_dict, None)
        if v == value:
            key = k

    return key

