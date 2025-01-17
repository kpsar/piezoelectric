# Internal imports
from file_handler import name_handler, Data_Handler
import matplotlib.pyplot as plt
from config import *
from connection import *

# External imports
import pandas as pd
import numpy as np
import os
import time
import yaml

if __name__ == '__main__':
    """
    Main routine for collecting and processing sensor data.
    """
    # Allocate offset data array
    offsets = np.zeros([16, 1])
    
    # Load calibration parameters from the YAML file
    with open(CONFIG_PATH + 'calibration_params.yaml', 'r') as file:
        calibration_parameters = yaml.safe_load(file)
        channel_no = 0
        for entry in calibration_parameters['channels']:
            offsets[entry["number"] - 1] = entry['offset_mean']

    # Initialize sensor and reading parameters
    start_time = time.time()
    duration = 120  # Duration for data collection in seconds
    sensor = FTDI()
    readings = [0]
    print("Begin readings")
    c_time = 0  # Counter for tracking time elapsed

    # Collect sensor readings for the specified duration
    while time.time() - start_time < duration:
        data = sensor.read()
        if data:
            readings = np.concatenate((readings, data))
        if time.time() - start_time > c_time:
            print("Time: " + str(c_time) + "s")
            c_time += 1

    # Process the readings and save the data
    name = "idle2"
    processed_readings = process_FTDI_readings(readings[1:])

    # Create a Data_Handler object for saving the data
    DH = Data_Handler(name, np.transpose(processed_readings))
    fs = 3124  # Sampling frequency
    meta_description = "Experiment to validate the reconstruction. Piezosensor in the incision in skin. Sensor 13."
    
    # Save the response data, metadata, and configuration
    DH.save_response()
    # DH.save_reconstruction(np.transpose(FE.F))  # Uncomment if reconstruction data is available
    DH.save_metadata(meta_description)
    DH.save_configuration()
