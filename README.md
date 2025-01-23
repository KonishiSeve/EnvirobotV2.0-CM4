# Envirobot V2.0 Raspberry PI CM4 Software
## config.txt
Should be placed in the /boot folder. It is used to add device tree overlays

## cm4client.service
Should be placed in the /etc/systemd/system folder.
This service is used to start the CM4Client.py script at startup. It can be enabled with the "sudo systemctl enable cm4client" command.

The Python script is actually ran inside a screen session with the name "cm4client".
After startup, it is possible to connect to the CM4 through SSH and attach to the screen session with this command: "screen -r cm4client". This allows to gain access to the shell interface given by the Python script as if it was started from the current terminal.
The screen sessions can be listed with this command: "screen -list"

This autostart functionnality does work correctly but around 5-10% of the time, the CM4 will not initialize the CANFD1 interface properly and the Python script will not work as expected. The user must manually reboot the CM4 from SSH.

## framework.py

## LogLib.py

## flash_stm.sh

## reset_stm.sh