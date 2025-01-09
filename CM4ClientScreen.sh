#!/bin/bash
# Check if a screen session named "cm4client" is running
if screen -list | grep -q "\.cm4client"; then
    echo "Screen session 'cm4client' is already running."
else
    echo "Screen session 'cm4client' is not running. Starting it now..."
    screen -S cm4client -d -m python CM4Client.py
    if [ $? -eq 0 ]; then
        echo "Screen session 'cm4client' started successfully."
    else
        echo "Failed to start screen session 'cm4client'."
    fi
fi
