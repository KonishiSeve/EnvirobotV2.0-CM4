# Created on Jan 21 2025 , Severin Konishi
import re
import numpy as np

#class to read and write logfiles for Envirobot V2.0
class LogFile:
    def __init__(self):
        self.file_operation = False

    def __del__(self):
        if self.file_operation:
            self.file.close()
            self.file_operation = False

    def close(self):
        if self.file_operation:
            self.file.close()
            self.file_operation = False

    #call to open and read an existing file
    def open(self, file_path):
        if not self.file_operation:
            self.file = open(file_path, "r")
            self.file_operation = "r"
            line = (self.file.readline()).replace("\n", "")
            line = re.split(r';|,', line)
            self.state_keys = []
            self.event_keys = []
            #recover the keys from the file header
            if line[0] == "time": #check that the first key is time
                for key in line:
                    #event key
                    if key[-1] == "@":
                        self.event_keys.append(key[:-1])
                    #state key
                    else:
                        self.state_keys.append(key)
    
    #read the next entry
    def read(self):
        #check that the "open" method was called first
        if self.file_operation == "r":
            data = {}
            line = (self.file.readline()).replace("\n", "")
            if len(line) == 0:
                return None #end of file
            values = re.split(r';|,', line)
            #read the timestamp
            data["time"] = values[0]
            values = values[1:]
            #read the states
            for i in range(len(self.state_keys)):
                data[self.state_keys[i]] = values[i]
            values = values[(len(self.state_keys)-1):]
            #read the events
            for i in range(len(self.event_keys)):
                if(len(values[i]) > 0):
                    data[self.event_keys[i]] = values[i]
            return data



    #call to create a new file to write to
    def new(self, file_path, state_keys, event_keys):
        if not self.file_operation:
            self.file = open(file_path, "w")
            self.file_operation = "w"
            self.state_keys = state_keys[:]
            self.event_keys = event_keys[:]
            self.states = {}
            #write the header of the csv file (the event names have an @ symbol at the end for the reader to recognize them)
            self.file.write(";".join(["time"] + self.state_keys + [i+"@" for i in self.event_keys]) + "\n")

    #write a new entry
    def write(self, data):
        #check that the "new" method was called first
        if self.file_operation == "w":
            #update the states, check if there is a change and if there is an event
            new_entry = False
            for key in data:
                #update variable if already initialized and new value
                if key in self.states:
                    if self.states[key] != data[key]:
                        self.states[key] = data[key]
                        new_entry = True
                #initialize variable
                elif key in self.state_keys:
                    self.states[key] = data[key]
                    new_entry = True
                #check if it is an event
                elif key in self.event_keys:
                    if not data[key] is None:
                        new_entry = True

            #write to file only when the "time" key is present, all states are initialized and (a state was updated or there was an event)
            if ("time" in data) and (len(self.states) == len(self.state_keys)) and (new_entry):
                #write the time
                self.file.write(str(data["time"]) + ";")
                #write the states
                for key in self.state_keys:
                    self.file.write(str(self.states[key]) + ";")
                #write the events
                for key in self.event_keys:
                    if (key in data) and (not data[key] is None):
                        self.file.write(str(data[key]))
                    self.file.write(";")
                self.file.write("\n")