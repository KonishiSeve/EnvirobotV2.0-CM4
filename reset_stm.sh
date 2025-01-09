#!/bin/bash
RESET_PIN=26

raspi-gpio set $RESET_PIN op dh
sleep  0.1
raspi-gpio set $RESET_PIN dl
raspi-gpio set $RESET_PIN ip
