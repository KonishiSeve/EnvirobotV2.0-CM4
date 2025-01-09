#!/bin/bash
BOOT_PIN=25
RESET_PIN=26
USER_LED=23

#Enable boot mode
raspi-gpio set $BOOT_PIN op dl
#Reset
raspi-gpio set $RESET_PIN op dh
sleep  0.1
raspi-gpio set $RESET_PIN dl

#flasing
sleep  1
stm32flash -m 8e1 -b 115200 -w Envirobot_STM32_Head.hex -v /dev/ttyAMA0
sleep  1

#Disable boot mode
raspi-gpio set $BOOT_PIN op dh
raspi-gpio set $BOOT_PIN ip
#Reset
raspi-gpio set $RESET_PIN op dh
sleep  0.1
raspi-gpio set $RESET_PIN dl
raspi-gpio set $RESET_PIN ip