# Envirobot V2.0 Raspberry PI CM4 Software
## SSH access
The Raspberry PI CM4 mounted on the “head” PCB runs a headless 32-bits Lite Debian version 11 (bullseye) Raspberry Pi operating system. It was originally setup by Dorian to be accessible by SSH through the EPFL wifi but due to certificate problems it could not be reached anymore. The Envirobot V2.0 Head PCB also has an HDMI port but the trace layout made the signal too noisy to be working. The CM4 had to be removed from the PCB and put into a breakout board to have HDMI access and reconfigure it. Due to the past certificate problems and for simplicity the CM4 was configured to be accessible from the “biorob-local” wifi network from the lab. The IP address can be found by scanning the network with tools such as “Advanced IP scanner” from another PC. Remote access to the command line interface of the CM4 can be done through SSH with programs such as “Putty” and file transfers can be done with SFTP with programs such as “FileZilla”. A setup with VisualStudioCode with an SFTP extension can provide the same functionalities as both of these programs in addition to a proper IDE. However, it does take more processing power from the CM4 and can sometimes make it significantly slow.

## Content
### config.txt
Should be placed in the /boot folder. It is used to add device tree overlays and properly configure the CM4 peripherals.
### cm4client.service
Should be placed in the /etc/systemd/system folder.
This service is used to start the **CM4Client.py** script at startup. It can be enabled with the "sudo systemctl enable cm4client" command.

The Python script is actually ran inside a screen session with the name "cm4client".
After startup, it is possible to connect to the CM4 through SSH and attach to the screen session with this command: "screen -r cm4client". This allows to gain access to the shell interface given by the Python script as if it was started from the current terminal.
The screen sessions can be listed with this command: "screen -list"

This autostart functionnality does work correctly but around 5% of the time, the CM4 will not initialize the CANFD1 interface properly and the Python script will not work as expected. The user must manually reboot the CM4 from SSH to fix the issue.

### CM4Client.py
This Python script can be ran to start logging the setpoints of the CPG, power consumption, energy consumption and CPG parameter changes happening on the robot. It also gives access to a shell where the user can modify CPG parameters and access all the registers of the robot through the UART and CANFD1 interfaces.
The “help” command can be used to print all the commands supported by the shell.
### framework.py
This Python library is used by **CM4Client.py** to deal with the low level communication with the robot and implements the framework protocol.
### LogLib.py
This Python library is used by **CM4Client.py** to create the log files. The Python Envirobot V2.0 plotter uses the same file format.
### flash_stm.sh
This bash script can be used to flash the “head” STM32 through UART.
Command: **bash flash_stm.sh filename.hex**
The compiled file must be a .hex file. The .elf files outputed by STM32CubeIDE have some gaps that are dealt with differently depending on the flashing program. SMT32CubeProgrammer presented the same problems as the “stm32flash” program that is used in this script. The option to also compile a .hex file must be enabled in STM32CubeIDE by right clicking on the project → “properties” → “C/C++ Build” → “Settings” → “Tool Settings” tab → “MCU/MPU Post build outputs” → tick the “Convert to Intel Hex file (-O ihex)” box.
### reset_stm.sh
This bash script can be used to assert a reset on the NRST pin of the “head” STM32.
Command: **bash reset_stm.sh**
