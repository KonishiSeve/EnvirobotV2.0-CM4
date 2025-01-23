#!/bin/bash
# Created on Jan 21 2025 , Severin Konishi

#used to reset the "head" STM32
#command: sh reset_stm.sh

RESET_PIN=26

raspi-gpio set $RESET_PIN op dh
sleep  0.1
raspi-gpio set $RESET_PIN dl
raspi-gpio set $RESET_PIN ip
