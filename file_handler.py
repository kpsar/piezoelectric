# External imports
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import json
from datetime import datetime
import shutil
import yaml

# Internal imports
from config.path_config import *

class Data_Handler():
    """
    A class to handle data related to readings and their metadata, 
    including saving responses, reconstructions, and metadata, 
    as well as creating plots.
    """
    
    def __init__(self, name, response):
        """
        Initializes the Data_Handler object.

        Args:
            name (str): The name of the reading.
            response (numpy.ndarray): The response data to be handled.
        """
        # Load configuration from YAML file
        with open(CONFIG_PATH + CONFIGURATION_FILE, 'r') as f:
            data = yaml.safe_load(f)
            for key, value in data.items():
                setattr(self, key, value)
        
        self.current_datetime = datetime.now()
        self.name = name
        self.newpath = READINGS_DIR + self.name
        self.response = response
        self._create_folder()

    def _create_folder(self):
        """
        Creates a new directory for storing the reading data 
        if it does not already exist.
        """
        if not os.path.exists(self.newpath):
            os.makedirs(self.newpath)

    def save_response(self):
        """
        Saves the response data to a CSV file.
        """
        data = pd.DataFrame(self.response)
        data.to_csv(self.newpath + "/output.csv", index=False) 

    def save_reconstruction(self, reconstruction):
        """
        Saves the reconstruction data to a CSV file.

        Args:
            reconstruction (numpy.ndarray): The reconstructed data to be saved.
        """
        setattr(self, "reconstruction", reconstruction)
        data = pd.DataFrame(self.reconstruction)
        data.to_csv(self.newpath + "/reconstruction.csv", index=False) 

    def save_metadata(self, description):
        """
        Saves metadata related to the reading to a JSON file.

        Args:
            description (str): Description of the reading.
        """
        duration = max(np.shape(self.response))/self.T
        metadata = {
            "reading name": self.name,
            "length of signal": str(duration) + " seconds",
            "sampling frequency": str(self.T) + "Hz",
            "description": description,
            "threshold range": "-0.02 to 0.02",
            "capacitator values": "Cs = 2nF and Cf = 220pF. Signal amplification of approx 10",
            "date and time": self.current_datetime.strftime("%Y-%m-%d_%H-%M-%S"),
            "author": "Kajetan Sarnowski"
        }
        with open(self.newpath + '/metadata.json', 'w') as json_file:
            json.dump(metadata, json_file, indent=4)

    def save_configuration(self):
        """
        Saves the configuration files to the new directory.
        """
        shutil.copy(CONFIG_PATH + CALIBRATION_FILE, self.newpath)
        shutil.copy(CONFIG_PATH + CONFIGURATION_FILE, self.newpath)
    
    def save_figures(self, channel):
        """
        Saves figures of the response and reconstruction data to files.

        Args:
            channel (int): The channel number to plot.
        """
        # Create the time vector for the response plot
        time_res = np.linspace(0, len(self.response[:,channel])/self.T, len(self.response[:,channel]))
        # Create the figure and subplots
        fig, (ax_res, ax_rec) = plt.subplots(2, sharex=True)
        
        # Plot the response
        ax_res.plot(time_res, self.response[:,channel])
        ax_res.set_ylabel('Response [V]')
        ax_res.set_ylim(0, 3.3)
        ax_res.set_title('Raw piezoelectric response')
        
        # Plot the reconstruction if it exists
        if hasattr(self, 'reconstruction'):
            time_rec = np.linspace(0, len(self.reconstruction[:,channel])/self.T, len(self.reconstruction[:,channel]))
            ax_rec.plot(time_rec, self.reconstruction[:,channel])
            ax_rec.set_xlabel('time [s]')
            ax_rec.set_ylabel('Force [N]')
            ax_rec.set_ylim(-5, 10)
            ax_rec.set_title('Reconstructed force')
        
        # Adjust layout and save the plots
        plt.tight_layout()
        plt.savefig(self.newpath + "/figure.pdf")
        plt.savefig(self.newpath + "/figure.eps")
        plt.close()

def name_handler(name):
    """
    Handles naming conflicts by appending a number to the file name if it already exists.

    Args:
        name (str): The original name of the file.

    Returns:
        str: The new name of the file, with a number appended if there was a conflict.
    """
    if os.path.exists(READINGS_DIR + name):
        i = 2
        print(f"The file '{name}' already exists.")
        while True:
            if os.path.exists(READINGS_DIR + name + str(i) + ".csv"):
                i += 1
            else:
                break
        name = name + str(i) + ".csv"
        print(f"Saving file as '{name}'.")   
    return name
