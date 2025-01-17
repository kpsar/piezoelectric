# External imports
from scipy import signal
import numpy as np
import yaml
import matplotlib.pyplot as plt
from tqdm import tqdm

# Internal imports
from config.path_config import *

def delete_offset(data, mean):
    """
    Deletes the offset from the data by subtracting the mean.

    Args:
        data (numpy.ndarray): The input data.
        mean (numpy.ndarray): The mean values to subtract.

    Returns:
        numpy.ndarray: The data with the offset removed.
    """
    data = np.array(data)
    data = data - mean
    return data

if __name__ == "__main__":
    """
    Main routine for processing sensor data and performing system reconstruction.
    """
    # Load parameters of the system from the configuration file
    with open(CONFIG_PATH + CONFIGURATION_FILE, 'r') as f:
        data = yaml.safe_load(f)
        for key, value in data.items():
            globals()[key] = value

    # Create the Laplace domain system
    numerator = np.array([Rf * Cf, 1])
    denominator = np.array([d33 * Rf, 0])
    system = signal.lti(numerator, denominator)

    # Load the data file
    experiment_name = "tapping1"
    data = np.genfromtxt(READINGS_DIR + experiment_name + "/output.csv", delimiter=',')
    
    # Adjust the data by subtracting the mean value
    data = data[1:, :] - 1.6267545977783202

    # Initialize variables for the reconstruction loop
    step = 10
    rec = []
    t = np.linspace(0, step / T, step)
    xout = [0]

    # Perform the reconstruction in steps and collect the output
    for i in tqdm(range(0, len(data), step)):
        tout, yout, xout = signal.lsim(system, data[i:i + step], t, xout[-1])
        rec.extend(yout)
    
    # Perform the full reconstruction for comparison
    tout, yout, xout = signal.lsim(system, data, np.linspace(0, len(data) / T, len(data)), 0)

    # Plot the reconstructed data
    plt.figure()
    plt.plot(rec, label='Step Reconstruction')
    plt.plot(yout, label='Full Reconstruction')
    plt.legend()
    plt.show()
