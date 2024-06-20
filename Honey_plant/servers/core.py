import socket
import threading
import logging
from pyModbusTCP.server import ModbusServer, DataBank
from pyModbusTCP.constants import EXP_ILLEGAL_FUNCTION
from servers.jsonlogging import JsonFileLogger


class HoneyPLC:
    # server parameters
    host = '0.0.0.0'
    port = 502

    # Plc I/O data
    data: dict[str, int] = None
    data_addresses: dict[str, int] = None

    def __init__(self):
        # Create plc modbus server instance
        self.server = LoggerModbusServer(host=HoneyPLC.host, port=HoneyPLC.port, data_bank=HoneyPLCDataBank(self))

        # Set logging configuration
        logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%d-%m-%Y %H:%M:%S', level=logging.DEBUG)


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


class HoneyPLCDataBank(DataBank):
    def __init__(self, honeyPLC: HoneyPLC):
        self.honeyPLC = honeyPLC
        super().__init__()

    def get_holding_registers(self, address, number=1, srv_info=None):
        # get water tank sensors data
        # set holding registers with updated data before accessing them
        for data_address, value in zip(self.honeyPLC.data_addresses.values(), self.honeyPLC.data.values()):
            self._h_regs[data_address] = value
        try:
            return [self._h_regs[i] for i in range(address, address+number)]
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
                        self.honeyPLC.data[key_from_value(self.honeyPLC.data_addresses, c_address)] = c_value
            else:
                return None
        # on server update
        if srv_info:
            # notify changes with on change method (after atomic update)
            for address, from_value, to_value in changes_list:
                self.on_holding_registers_change(address, from_value, to_value, srv_info=srv_info)
        return True

    def on_coils_change(self, address, from_value, to_value, srv_info):
        logger = logging.getLogger('pyModbusTCP.server')
        logging.setLoggerClass(JsonFileLogger)
        jsonLogger = logging.getLogger('jsonLogger')
        logging.setLoggerClass(logging.Logger)
        logger.warning(f'>>> Coil with address [{address}] changed from [{from_value}] to [{to_value}]')
        jsonLogger.warning(msg='>>> Coil value changed:',
                           extra={'address:': address, 'from_value': from_value, 'to_value': to_value})

    def on_holding_registers_change(self, address, from_value, to_value, srv_info):
        logger = logging.getLogger('pyModbusTCP.server')
        logging.setLoggerClass(JsonFileLogger)
        jsonLogger = logging.getLogger('jsonLogger')
        logging.setLoggerClass(logging.Logger)
        logger.warning(f'>>> Holding register with address [{address}] changed from [{from_value}] to [{to_value}]')
        jsonLogger.warning(msg='>>> Holding register value changed:',
                           extra={'address:': address, 'from_value': from_value, 'to_value': to_value})


class LoggerModbusServer(ModbusServer):
    """ ModbusServer subclass modified to log in screen and in file
        ModbusTCP protocol actions made by connections """

    def __init__(self, host='localhost', port=502, no_block=False, ipv6=False,
                 data_bank=None, data_hdl=None, ext_engine=None, device_id=None):
        super().__init__(host, port, no_block, ipv6, data_bank, data_hdl, ext_engine, device_id)

        JsonFileLogger('jsonLogger')

    class ModbusService(ModbusServer.ModbusService):

        def __init__(self, request, client_address, server):
            super().__init__(request, client_address, server)

        def handle(self):
            logger = logging.getLogger('pyModbusTCP.server')
            logging.setLoggerClass(JsonFileLogger)
            jsonLogger = logging.getLogger('jsonLogger')
            logging.setLoggerClass(logging.Logger)
            # try/except end current thread on ModbusServer._InternalError or socket.error
            # this also close the current TCP session associated with it
            # init and update server info structure
            session_data = ModbusServer.SessionData()

            try:
                # main processing loop
                while True:
                    # init session data for new request
                    session_data.new_request()
                    # receive mbap from client
                    session_data.request.mbap.raw = self._recv_all(7)
                    # receive pdu from client
                    session_data.request.pdu.raw = self._recv_all(session_data.request.mbap.length - 1)

                    session_data.client.address, session_data.client.port = self.request.getpeername()
                    mbap = session_data.request.mbap
                    pdu = session_data.request.pdu
                    logger.debug(f'>>> New request received: \
                                 \n\tOrigin: \
                                 \n\t\tIP: {session_data.client.address} \n\t\tPort: {session_data.client.port} \
                                 \n\tMBAP header: \
                                 \n\t\tTransaction ID: {mbap.transaction_id} \n\t\tProtocol ID: {mbap.protocol_id} \
                                 \n\t\tLength: {mbap.length} \n\t\tUnitID: {mbap.unit_id} \
                                 \n\tPDU: \
                                 \n\t\tFunction code: {pdu.func_code} \n\t\tData: {pdu.raw[1:len(pdu.raw)]}')
                    jsonLogger.debug(msg='>>> New request received: ',
                                     extra={'Origin':
                                                {'IP:': session_data.client.address,
                                                 'Port:': session_data.client.port},
                                            'MBAP header':
                                                {'Transaction ID:': mbap.transaction_id,
                                                 'Protocol ID:': mbap.protocol_id,
                                                 'Length:': mbap.length,
                                                 'UnitID:': mbap.unit_id},
                                            'PDU':
                                                {'Function code': pdu.func_code,
                                                 'Data:': pdu.raw[1:len(pdu.raw)]}})

                    # update response MBAP fields with request data
                    session_data.set_response_mbap()
                    # pass the current session data to request engine
                    self.server.engine(session_data)
                    # send the tx pdu with the last rx mbap (only length field change)
                    self._send_all(session_data.response.raw)
            except (ModbusServer.Error, socket.error) as e:
                req_ip, req_port = self.request.getpeername()
                # on main loop except: exit from it and cleanly close the current socket
                self.request.close()
                # debug message
                logger.debug(f'>>> Connection with client closed: \
                                 \n\tClient: \
                                 \n\t\tIP: {req_ip} \n\t\tPort: {req_port}')
                jsonLogger.debug(msg=f'>>> Connection with client closed: ',
                                 extra={'Client':
                                            {'IP:': req_ip,
                                             'Port:': req_port}})

    def _internal_engine(self, session_data):
        """ Default internal processing engine: call default modbus func.
            :type session_data: ModbusServer.SessionData """

        logger = logging.getLogger('pyModbusTCP.server')
        logging.setLoggerClass(JsonFileLogger)
        jsonLogger = logging.getLogger('jsonLogger')
        logging.setLoggerClass(logging.Logger)

        try:
            # call the ad-hoc function, if none exists, send an "illegal function" exception
            func = self._func_map[session_data.request.pdu.func_code]
            # check function found is callable
            if not callable(func):
                raise TypeError
            # call ad-hoc func
            logger.warning(f'>>> Call to {function_codes.get(session_data.request.pdu.func_code)} function')
            jsonLogger.warning(f'>>> Call to {function_codes.get(session_data.request.pdu.func_code)} function')
            func(session_data)
        except (TypeError, KeyError):
            session_data.response.pdu.build_except(session_data.request.pdu.func_code, EXP_ILLEGAL_FUNCTION)


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

# Modbus function codes for logging
function_codes = {
    0x01: 'READ_COILS',
    0x02: 'READ_DISCRETE_INPUTS',
    0x03: 'READ_HOLDING_REGISTERS',
    0x04: 'READ_INPUT_REGISTERS',
    0x05: 'WRITE_SINGLE_COIL',
    0x06: 'WRITE_SINGLE_REGISTER',
    0x0F: 'WRITE_MULTIPLE_COILS',
    0x10: 'WRITE_MULTIPLE_REGISTERS',
    0x17: 'WRITE_READ_MULTIPLE_REGISTERS',
    0x2B: 'ENCAPSULATED_INTERFACE_TRANSPORT'
}