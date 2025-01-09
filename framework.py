import can
import serial
import threading
import queue
import time
import struct

# Register types (name, number of bytes, string for the struct library to decode the bytes)
REG_TYPE_UINT8 = ("uint8", 1, ">B")
REG_TYPE_UINT16 = ("uint16", 2, ">H")
REG_TYPE_UINT32 = ("uint32", 4, ">I")
REG_TYPE_UINT64 = ("uint64", 8, ">Q")
REG_TYPE_INT8 = ("int8", 1, ">b")
REG_TYPE_INT16 = ("int16", 2, ">h")
REG_TYPE_INT32 = ("int32", 4, ">i")
REG_TYPE_INT64 = ("int64", 8, ">q")
REG_TYPE_FLOAT = ("float", 4, ">f")

# Register event parameter
EVENT_TYPE_NEVER = 0    #No event is triggered
EVENT_TYPE_UPDATE = 1   #An event is triggered whenever the register is published with a different value than last time
EVENT_TYPE_ALWAYS = 2   #An event is triggered whenever the register is published

# Operation types (Upper bits of the MSB of a framework payload)
OP_TYPE_WRITE_REQ = 0b010
OP_TYPE_READ_REQ = 0b011
OP_TYPE_WRITE_RES = 0b100
OP_TYPE_READ_RES = 0b101
OP_TYPE_ERROR = 0b110
OP_TYPE_PUBLISH = 0b000

#The TIMESTAMP corresponds to the last time the register value was updated
# register  -> {"time": TIMESPAMP, "address": REGISTER_ADDRESS, "type": REG_TYPE, "value": VALUE, "length": LENGTH}
# operation -> {"time": TIMESTAMP, "type": OP_TYPE, "source": SOURCE_ADDRESS, "address": ADDRESS, "value": VALUE}
class Framework:
    def __init__(self, verbose=False):
        #list of register dictionnaries
        self.registers = []
        #to control the CAN and UART threads
        self.thread_uart_running = True
        self.thread_can_running = True
        #for debugging
        self.verbose = verbose

        #Address the CM4 uses as source when sending packets
        self.cm4_address = 0x00

        #initialize the CAN and UART buses
        self.bus_can = can.interface.Bus(channel="can0", bustype="socketcan", bitrate=1000000, dbitrate=4000000, fd=True)
        self.bus_uart = serial.Serial("/dev/ttyAMA0", 115200, timeout=0.5, xonxoff=False, rtscts=False, dsrdtr=False) #ttyS0
        self.timeout_ms = 500    #timeout for an STM32 response when doing reads or writes

        #list of register addresses for which the local value will automatically be updated when there is a publication of the register
        self.registers_subscribe_update = []
        #list of register addresses for which an "operation dictionary" will be added to the event queue when a different value to the local one is published
        self.registers_event_update = []
        #list of register addresses for which an "operation dictionary" will be added to the event queue when there is a publication of the register
        self.registers_event_always = []
        #queue filled with publish operations, should be consummed by the user
        self.queue_event = queue.Queue()

        #set the time now as reference/zero for all the future timestamps
        self.start_time = time.time()

    def __del__(self):
        self.thread_uart_running = False
        self.thread_can_running = False
        if self.verbose: print("[Framework] Threads stopped")

    def stop(self):
        self.thread_uart_running = False
        self.thread_can_running = False
        if self.verbose: print("[Framework] Threads stopped")

    #add a register and choose when to create events with it
    def RegisterAdd(self, address, type, length, value=None, subscribe_update = True, event_type = EVENT_TYPE_NEVER):
        if self._RegisterGet(address) is None:
            self.registers.append({"time": 0, "address": address, "type":type, "value": value, "length":length})
            if subscribe_update:
                self.registers_subscribe_update.append(address)
            if event_type == EVENT_TYPE_UPDATE:
                self.registers_event_update.append(address)
            elif event_type == EVENT_TYPE_ALWAYS:
                self.registers_event_always.append(address)
            if self.verbose: print("[Framework] Register {0} created".format(hex(address)))
        else:
            if self.verbose: print("[Framework] Register {0} already exists".format(hex(address)))

    #should only be used for registers with publish update enabled
    def RegisterRead(self, address):
        register = self._RegisterGet(address)
        if register is None:
            if self.verbose: print("[Framework] Register {0} does not exist".format(hex(address)))
            return None
        if self.verbose: print("[Framework] Reading local register {0}: {1} ({2})".format(hex(address), register["value"], hex(register["value"])))
        return register["value"]

    def ThreadUART(self):
        print("[Framework] UART Thread started")
        #contains only the "payload" part of the framework packet
        payload = []
        checksum = 0
        #the index of the byte that is being read
        index = 0
        #length of the "payload" part only
        length = 0
        while(self.thread_uart_running):
            value_uart = self.bus_uart.read(1)
            #timeout
            if len(value_uart) == 0:
                #index = 0
                continue
            value_uart = value_uart[0]
            #first start byte
            if (index==0) and (value_uart == 0xC3):
                checksum = 0xC3
                payload = []
                index += 1
            #second start byte
            elif (index==1) and (value_uart == 0x3C):
                checksum += 0x3C
                index += 1
            #source address
            elif (index==2):
                source = value_uart
                checksum += value_uart
                index += 1
            #packet length
            elif (index==3):
                length = value_uart
                checksum += value_uart
                index += 1
            #checksum
            elif (index == (4 + length)):
                checksum = ((~checksum)+1)&0xFF
                index += 1
                if(checksum != value_uart):
                    index = 0
                    if self.verbose: print("[Framework UART] Checksum error")
                    continue
            #end byte
            elif (index > 3) and (index >= (5 + length)):
                index = 0
                if value_uart != 0xFF:
                    if self.verbose: print("[Framework UART] Stop byte error")
                    continue
                timestamp = time.time() - self.start_time
                operations = self._PayloadDecode(payload)
                for operation in operations:
                    operation["time"] = timestamp
                    operation["source"] = source
                    self._OperationProcess(operation)
                continue
            #payload bytes
            elif (index >= 4):
                payload.append(value_uart)
                checksum += value_uart
                index += 1
            #invalid byte
            else:
                index = 0
        self.bus_uart.close()
        print("[Framework] UART Thread stopped")

    def ThreadCAN(self):
        print("[Framework] CAN Thread started")
        while(self.thread_can_running):
            while True:
                message = self.bus_can.recv(0.5)
                if message != None:
                    timestamp = time.time() - self.start_time
                    break
                elif self.thread_can_running:
                    return
            data = list(message.data)
            source = data[0]
            length = data[1]
            operations = self._PayloadDecode(data[2:(length+2)])
            for operation in operations:
                operation["time"] = timestamp
                operation["source"] = source
                self._OperationProcess(operation)
        print("[Framework] CAN Thread stopped")

    def ServiceReadUART(self, address):
        register = self._RegisterGet(address)
        if register is None:
            return None
        payload = self._PayloadEncode([{"time": None, "type": OP_TYPE_READ_REQ, "source": self.cm4_address, "address": address, "value": None}])
        last_time = register["time"]
        self._SendUart(payload)
        start = time.time()
        while (self.thread_uart_running) and ((time.time()-start) < (self.timeout_ms/1000)):
            if(last_time < register["time"]):
                return register["value"]
        return None

    def ServiceWriteUART(self, address, value):
        register = self._RegisterGet(address)
        if register is None:
            return None
        last_time = register["time"]
        payload = self._PayloadEncode([{"time": None, "type": OP_TYPE_WRITE_REQ, "source": self.cm4_address, "address": address, "value": value}])
        self._SendUart(payload)
        start = time.time()
        while (self.thread_uart_running) and ((time.time()-start) < (self.timeout_ms/1000)):
            if(last_time < register["time"]):
                register["value"] = value
                return True
        return None

    def ServiceReadCAN(self, address, target_address):
        register = self._RegisterGet(address)
        if register is None:
            return None
        payload = self._PayloadEncode([{"time": None, "type": OP_TYPE_READ_REQ, "source": self.cm4_address, "address": address, "value": None}])
        last_time = register["time"]
        self._SendCAN(payload, target_address)
        #wait for the register to be updated
        start = time.time()
        while (self.thread_can_running) and ((time.time()-start) < (self.timeout_ms/1000)):
            if(last_time < register["time"]):
                return register["value"]
        return None

    def ServiceWriteCAN(self, address, value, target_address):
        register = self._RegisterGet(address)
        if register is None:
            return None
        payload = self._PayloadEncode([{"time": None, "type": OP_TYPE_WRITE_REQ, "source": self.cm4_address, "address": address, "value": None}])
        last_time = register["time"]
        self._SendCAN(payload, target_address)
        start = time.time()
        while (self.thread_can_running) and ((time.time()-start) < (self.timeout_ms/1000)):
            if(last_time < register["time"]):
                register["value"] = value
                return True
        return None

    # ===== private functions ===== #
    def _RegisterGet(self, address):
        for reg in self.registers:
            if reg["address"] == address:
                return reg
        return None
    
    def _PayloadDecode(self, payload):
        index = 0
        operations = []
        while (index+2) < len(payload):
            #decode the first 2 bytes
            ack = (payload[index]>>7)&0b1
            cmd = (payload[index]>>6)&0b1
            w_r = (payload[index]>>5)&0b1
            if ack == cmd:
                w_r = 0
            op_type = (ack<<2)|(cmd<<1)|(w_r)
            address = ((payload[index]&0b00011111)<<8) | (payload[index+1]&0xFF)
            index += 2
            #retrieve the register size
            reg = self._RegisterGet(address)
            if reg is None:
                if self.verbose: print("[Framework] Decode error, register {0} not found".format(hex(address)))
                return []
            if (op_type == OP_TYPE_READ_RES) or (op_type == OP_TYPE_PUBLISH):
                #decode the register value
                value = self._PayloadDecodeBytes(reg, payload[index:])
                if reg["length"] == 0:
                    index += reg["type"][1]
                else:
                    index += reg["type"][1]*reg["length"]
            else:
                #skip the write acknowledge flag/byte
                value = 0
                index += 1
            operations.append({"time": None, "type": op_type, "source": None, "address": address, "value": value})
        return operations
    
    def _PayloadDecodeBytes(self, reg, raw_bytes):
        type_size = reg["type"][1]
        if reg["length"] == 0:
            return struct.unpack(reg["type"][2], bytes(raw_bytes[:type_size]))[0]
        else:
            return [struct.unpack(reg["type"][2], bytes(raw_bytes[(i*type_size):((i+1)*type_size)]))[0] for i in range(reg["length"])]

    def _PayloadEncode(self, operations):
        payload = []
        for operation in operations:
            reg = self._RegisterGet(operation["address"])
            payload += [((operation["type"]<<5) | ((operation["address"]>>8)&0b11111)), operation["address"]&0xFF]
            if operation["type"] == OP_TYPE_WRITE_REQ:
                payload += self._PayloadEncodeBytes(reg, operation["value"])
        return payload

    def _PayloadEncodeBytes(self, reg, value):
        if reg["length"] == 0:
            return list(struct.pack(reg["type"][2], value))
        else:
            raw_bytes = []
            for i in range(reg["length"]):
                raw_bytes += list(struct.pack(reg["type"][2], value[i]))
            return raw_bytes

    def _SendUart(self, payload):
        packet = [0xC3, 0x3C, self.cm4_address, len(payload)] + payload
        checksum = (~sum(packet) + 1)&0xFF
        packet += [checksum, 0xFF]
        self.bus_uart.write(bytes(packet))

    def _SendCAN(self, payload, target_address):
        packet = [self.cm4_address, len(payload)] + payload
        message = can.Message(arbitration_id=target_address, data=packet, is_fd=True, is_extended_id=False)
        self.bus_can.send(message)

    #Use the received operations to update the local registers
    def _OperationProcess(self, operation):
        register = self._RegisterGet(operation["address"])
        #if the register operation was a write response
        if (operation["type"] == OP_TYPE_WRITE_RES):
            register["time"] = operation["time"]
        #if the register operation was a read response
        elif (operation["type"] == OP_TYPE_READ_RES):
            register["time"] = operation["time"]
            register["value"] = operation["value"]
        #if the operation was a register publish
        elif (operation["type"] == OP_TYPE_PUBLISH):
            #create events if enabled
            if (register["value"] != operation["value"]) and (register["address"] in self.registers_event_update):
                self.queue_event.put(operation)
            elif register["address"] in self.registers_event_always:
                self.queue_event.put(operation)
            #update the local register value if enabled
            if register["address"] in self.registers_subscribe_update:
                register["time"] = operation["time"]
                register["value"] = operation["value"]