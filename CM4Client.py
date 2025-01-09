from LogLib import LogFile
from framework import *
from datetime import datetime
import traceback

#number of modules (=number of motors/joints, the head is not counted as module)
MOD_NUM = 4

# Base Registers
REG_TIMESTAMP =      		0x0000
REG_COM_ID_PROPAGATION = 	0x0001
REG_COM_ADDRESS =           0x0002

# CPG Registers
REG_CPG_SETPOINTS =  0x0500
REG_CPG_ENABLED =    0x0501
REG_CPG_RESET =      0x0502

REG_CPG_FREQUENCY =         0x0510
REG_CPG_DIRECTION =         0x0511
REG_CPG_AMPLC =             0x0512
REG_CPG_AMPLH =             0x0513
REG_CPG_NWAVE =             0x0514
REG_CPG_COUPLING_STRENGTH = 0x0515
REG_CPG_A_R =               0x0516

REG_CPG_DIRECTION_MAX =     0x0520
REG_CPG_AMPLC_MAX =         0x0521
REG_CPG_AMPLH_MAX =         0x0522

# Remote registers
REG_REMOTE_MODE = 			0x0600
REG_REMOTE_ELT_NB = 		0x0601
REG_REMOTE_SPEED = 			0x0602
REG_REMOTE_FREQUENCY = 		0x0603
REG_REMOTE_DIRECTION = 		0x0604
REG_REMOTE_LAST_RX = 		0x0610

# MOTOR Registers
REG_MOTOR_POWER = 			0x022A
REG_MOTOR_ENERGY_FLOAT = 	0x022C

# Alert Registers
REG_ALERT_WATER = 			0x0700

# Commands
favourite_registers = [ {"address": REG_REMOTE_MODE, "name": "remote mode"},
                        {"address": REG_CPG_ENABLED, "name": "cpg enabled"},
                        {"address": REG_CPG_FREQUENCY, "name": "cpg frequency"},
                        {"address": REG_CPG_DIRECTION, "name": "cpg direction"},
                        {"address": REG_CPG_AMPLC, "name": "cpg amplc"},
                        {"address": REG_CPG_AMPLH, "name": "cpg amplh"},
                        {"address": REG_CPG_NWAVE, "name": "cpg nwave"},
                        {"address": REG_CPG_COUPLING_STRENGTH, "name": "cpg coupling"},
                        {"address": REG_CPG_A_R, "name": "cpg ar"}
]

help_print = [{"command": "exit", "description":"Close the shell"},
              {"command": "uartr ADDRESS", "description":"Read a register through UART"},
              {"command": "uartw ADDRESS VALUE", "description":"Write a register through UART"},
              {"command": "canr ADDRESS DEVICE_ADDRESS", "description":"Read a register through CANFD1"},
              {"command": "canw ADDRESS VALUE DEVICE_ADDRESS", "description":"Write a register through CANFD1"},
              {"command": "cpg  freq VALUE", "description": "set the frequency cpg parameter"},
              {"command": "cpg  dir VALUE", "description": "set the direction cpg parameter"},
              {"command": "cpg  amplc VALUE", "description": "set the amplc cpg parameter"},
              {"command": "cpg  amplh VALUE", "description": "set the amplh cpg parameter"},
              {"command": "cpg  nwave VALUE", "description": "set the nwave cpg parameter"},
              {"command": "cpg  cs VALUE", "description": "set the coupling strength cpg parameter"},
              {"command": "cpg  ar VALUE", "description": "set the ar cpg parameter"},
              {"command": "cpg  dirmax VALUE", "description": "set the direction max parameter"},
              {"command": "cpg  amplcmax VALUE", "description": "set the amplc max parameter"},
              {"command": "cpg  amplhmax VALUE", "description": "set the amplh max parameter"},
]


framework = Framework()

# === Base Registers === #
framework.RegisterAdd(REG_TIMESTAMP, REG_TYPE_UINT32, 0)
framework.RegisterAdd(REG_COM_ID_PROPAGATION, REG_TYPE_UINT8, 0)
framework.RegisterAdd(REG_COM_ADDRESS, REG_TYPE_UINT8, 0)

# === CPG Registers === #
framework.RegisterAdd(REG_CPG_SETPOINTS, REG_TYPE_INT8, MOD_NUM, event_type=EVENT_TYPE_UPDATE)
framework.RegisterAdd(REG_CPG_ENABLED, REG_TYPE_UINT8, 0, event_type=EVENT_TYPE_UPDATE)
framework.RegisterAdd(REG_CPG_RESET, REG_TYPE_UINT8, 0)

framework.RegisterAdd(REG_CPG_FREQUENCY, REG_TYPE_FLOAT, 0, event_type=EVENT_TYPE_UPDATE)
framework.RegisterAdd(REG_CPG_DIRECTION, REG_TYPE_FLOAT, 0, event_type=EVENT_TYPE_UPDATE)
framework.RegisterAdd(REG_CPG_AMPLC, REG_TYPE_FLOAT, 0, event_type=EVENT_TYPE_UPDATE)
framework.RegisterAdd(REG_CPG_AMPLH, REG_TYPE_FLOAT, 0, event_type=EVENT_TYPE_UPDATE)
framework.RegisterAdd(REG_CPG_NWAVE, REG_TYPE_FLOAT, 0, event_type=EVENT_TYPE_UPDATE)
framework.RegisterAdd(REG_CPG_COUPLING_STRENGTH, REG_TYPE_FLOAT, 0, event_type=EVENT_TYPE_UPDATE)
framework.RegisterAdd(REG_CPG_A_R, REG_TYPE_FLOAT, 0, event_type=EVENT_TYPE_UPDATE)

framework.RegisterAdd(REG_CPG_DIRECTION_MAX, REG_TYPE_FLOAT, 0)
framework.RegisterAdd(REG_CPG_AMPLC_MAX, REG_TYPE_FLOAT, 0)
framework.RegisterAdd(REG_CPG_AMPLH_MAX, REG_TYPE_FLOAT, 0)

# === Remote registers === #
framework.RegisterAdd(REG_REMOTE_MODE, REG_TYPE_UINT8, 0, event_type=EVENT_TYPE_UPDATE)
framework.RegisterAdd(REG_REMOTE_ELT_NB, REG_TYPE_UINT8, 0)
framework.RegisterAdd(REG_REMOTE_SPEED, REG_TYPE_UINT8, 0)
framework.RegisterAdd(REG_REMOTE_FREQUENCY, REG_TYPE_UINT8, 0)
framework.RegisterAdd(REG_REMOTE_DIRECTION, REG_TYPE_UINT8, 0)
framework.RegisterAdd(REG_REMOTE_LAST_RX, REG_TYPE_UINT32, 0)

# === MOTOR Registers === #
framework.RegisterAdd(REG_MOTOR_POWER, REG_TYPE_FLOAT, 0, subscribe_update=False, event_type=EVENT_TYPE_ALWAYS)
framework.RegisterAdd(REG_MOTOR_ENERGY_FLOAT, REG_TYPE_FLOAT, 0, subscribe_update=False, event_type=EVENT_TYPE_ALWAYS)

# === Alert Registers === #
framework.RegisterAdd(REG_ALERT_WATER, REG_TYPE_UINT8, 0)

# === Log file === #
log_cpg = LogFile()
joint_keys = ["joint{0}".format(i) for i in range(MOD_NUM)]
energy_keys = ["energy{0}".format(i) for i in range(MOD_NUM)]
power_keys = ["power{0}".format(i) for i in range(MOD_NUM)]
#For easier log file initialization
log_data_init = {}
for key in (joint_keys + energy_keys + power_keys):
    log_data_init[key] = 0.0

# === UART thread === #
def ThreadUart():
    framework.ThreadUART()

# === CAN Thread === #
def ThreadCan():
    framework.ThreadCAN()

# === Log Thread === #
thread_log_run = True
def ThreadLog():
    #read the inital cpg parameters (will be updated automatically by the STM publisher)
    print("[LOG] Reading CPG parameters")
    results = []
    results.append(framework.ServiceReadUART(REG_CPG_FREQUENCY))
    results.append(framework.ServiceReadUART(REG_CPG_DIRECTION))
    results.append(framework.ServiceReadUART(REG_CPG_AMPLC))
    results.append(framework.ServiceReadUART(REG_CPG_AMPLH))
    results.append(framework.ServiceReadUART(REG_CPG_NWAVE))
    results.append(framework.ServiceReadUART(REG_CPG_COUPLING_STRENGTH))
    results.append(framework.ServiceReadUART(REG_CPG_A_R))
    if None in results:
        print("[LOG] Error while reading CPG parameters")
    else:
        print("[LOG] CPG Parameters reading done")

    #Logging Loop
    while thread_log_run:
        #wait for the robot to be activated
        while thread_log_run:
            if not framework.queue_event.empty():
                operation = framework.queue_event.get()
                if operation["address"] == REG_REMOTE_MODE and operation["value"] == 1:
                    break
        if thread_log_run:
            #create a new log file when the remote is turned on
            print("Logging started")
            now = datetime.now()
            log_cpg.new(now.strftime("logs/cpg_%d_%m_%Y_%H_%M_%S.csv"), joint_keys + energy_keys + power_keys, ["print"])
            log_data = log_data_init.copy()
            log_data["time"] = int(operation["time"]*1000)
            log_data["print"] = "freq {0} - dir {1} - amplc {2} - amplh {3} - nwave {4} - coupling {5} - a_r {6}".format(
                round(framework.RegisterRead(REG_CPG_FREQUENCY),2),
                round(framework.RegisterRead(REG_CPG_DIRECTION),2),
                round(framework.RegisterRead(REG_CPG_AMPLC),2),
                round(framework.RegisterRead(REG_CPG_AMPLH),2),
                round(framework.RegisterRead(REG_CPG_NWAVE),2),
                round(framework.RegisterRead(REG_CPG_COUPLING_STRENGTH),2),
                round(framework.RegisterRead(REG_CPG_A_R),2)
            )
            log_cpg.write(log_data)
        #Log the activity (setpoint publishing or CPG parameter change)
        while thread_log_run:
            while(framework.queue_event.empty()): pass
            operation = framework.queue_event.get()
            log_data["time"] = int(operation["time"]*1000)
            log_data["print"] = None
            if operation["address"] == REG_CPG_SETPOINTS:
                for i in range(len(operation["value"])):
                    log_data[joint_keys[i]] = operation["value"][i]
                log_cpg.write(log_data)
            elif operation["address"] == REG_CPG_ENABLED:
                log_data["print"] = "[Radio] enabled {0}".format(operation["value"])
                log_cpg.write(log_data)
            elif operation["address"] == REG_CPG_FREQUENCY:
                log_data["print"] = "[Radio] frequency {0}".format(operation["value"])
                log_cpg.write(log_data)
            elif operation["address"] == REG_CPG_DIRECTION:
                log_data["print"] = "[Radio] direction {0}".format(operation["value"])
                log_cpg.write(log_data)
            elif operation["address"] == REG_CPG_AMPLC:
                log_data["print"] = "[Radio] amplc {0}".format(operation["value"])
                log_cpg.write(log_data)
            elif operation["address"] == REG_CPG_AMPLH:
                log_data["print"] = "[Radio] amplh {0}".format(operation["value"])
                log_cpg.write(log_data)
            elif operation["address"] == REG_CPG_NWAVE:
                log_data["print"] = "[Radio] nwave {0}".format(operation["value"])
                log_cpg.write(log_data)
            elif operation["address"] == REG_CPG_COUPLING_STRENGTH:
                log_data["print"] = "[Radio] coupling {0}".format(operation["value"])
                log_cpg.write(log_data)
            elif operation["address"] == REG_CPG_A_R:
                log_data["print"] = "[Radio] ar {0}".format(operation["value"])
                log_cpg.write(log_data)
            elif operation["address"] == REG_MOTOR_ENERGY_FLOAT:
                log_data["energy{0}".format(operation["source"]-2)] = round(operation["value"],2)
            elif operation["address"] == REG_MOTOR_POWER:
                log_data["power{0}".format(operation["source"]-2)] = round(operation["value"],2)
            elif operation["address"] == REG_REMOTE_MODE:
                if operation["value"] == 0:
                    log_data["print"] = "[Radio] remote {0}".format(operation["value"])
                    log_cpg.write(log_data)
                    log_cpg.close()
                    print("Logging stopped")
                    break

            if not log_data["print"] is None:
                #print(log_data["print"])
                pass



thread_uart_handle = threading.Thread(target=ThreadUart)
thread_can_handle = threading.Thread(target=ThreadCan)
thread_log_handle = threading.Thread(target=ThreadLog)

thread_uart_handle.start()
thread_can_handle.start()
thread_log_handle.start()

time.sleep(1)

try:
    shell_run = True
    print('Shell started, type "help" to get a list of supported commands')
    while(shell_run):
        command = input("> ")
        command = command.split(" ")
        #Shell specific commands
        if(command[0] == "exit"):
            shell_run = False
        elif(command[0] == "help"):
            max_len = 0
            for i in help_print:
                max_len = max(max_len, len(i["command"]))
            for i in help_print:
                print("{0} : {1}".format(i["command"].ljust(max_len, " "), i["description"]))

        #Low level framework commands
        elif(command[0] == "canr"):
            value = framework.ServiceReadCAN(int(command[1],0), int(command[2],0))
            print("{0} ({1})".format("Error" if value is None else value, "Error" if value is None else hex(value)))
        elif(command[0] == "canw"):
            framework.ServiceWriteCAN(int(command[1],0), int(command[2],0), int(command[3],0))
        elif(command[0] == "uartr"):
            value = framework.ServiceReadUART(int(command[1],0))
            if framework._RegisterGet(int(command[1],0))["type"] == REG_TYPE_FLOAT:
                print("{0}".format("Error" if value is None else value))
            else:
                print("{0} ({1})".format("Error" if value is None else value, "Error" if value is None else hex(value)))
        elif(command[0] == "uartw"):
            if framework._RegisterGet(int(command[1],0))["type"] == REG_TYPE_FLOAT:
                framework.ServiceWriteUART(int(command[1],0), float(command[2]))
            else:
                framework.ServiceWriteUART(int(command[1],0), int(command[2],0))
        elif(command[0] == "uartall"):
            for i in favourite_registers:
                value = framework.ServiceReadUART(i["address"])
                value = "Error" if value is None else value
                print("{0} ({1}): {2}".format(i["name"], hex(i["address"]), value))

        #CPG commands
        elif(command[0] == "cpg"):
            if(command[1] == "freq"):
                framework.ServiceWriteUART(REG_CPG_FREQUENCY, float(command[2]))
            elif(command[1] == "dir"):
                framework.ServiceWriteUART(REG_CPG_DIRECTION, float(command[2]))
            elif(command[1] == "amplc"):
                framework.ServiceWriteUART(REG_CPG_AMPLC, float(command[2]))
            elif(command[1] == "amplh"):
                framework.ServiceWriteUART(REG_CPG_AMPLH, float(command[2]))
            elif(command[1] == "nwave"):
                framework.ServiceWriteUART(REG_CPG_NWAVE, float(command[2]))
            elif(command[1] == "coupling"):
                framework.ServiceWriteUART(REG_CPG_COUPLING_STRENGTH, float(command[2]))
            elif(command[1] == "ar"):
                framework.ServiceWriteUART(REG_CPG_A_R, float(command[2]))
            elif(command[1] == "dirmax"):
                framework.ServiceWriteUART(REG_CPG_DIRECTION_MAX, float(command[2]))
            elif(command[1] == "amplcmax"):
                framework.ServiceWriteUART(REG_CPG_AMPLC_MAX, float(command[2]))
            elif(command[1] == "amplhmax"):
                framework.ServiceWriteUART(REG_CPG_AMPLH_MAX, float(command[2]))
            else:
                print("Command not recognized")

except Exception as e:
    pass
    print(e)
    print(traceback.print_exc())
framework.stop()
thread_log_run = False
print("[Shell] Stopped")