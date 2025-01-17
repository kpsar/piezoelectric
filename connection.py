import ftd2xx as ftd
import numpy as np
import time
import matplotlib.pyplot as plt

class FTDI():
    """
    A class to handle interactions with an FTDI device for reading data.
    """
    
    def __init__(self, id=0):
        """
        Initializes the FTDI device connection.

        Args:
            id (int, optional): The ID of the FTDI device to connect to. Defaults to 0.
        """
        # Open the connection to the FTDI device
        self.device = ftd.open(id)
        # self.device.setBaudRate(baudRate)  # Uncomment to set baud rate if needed
    
    def read(self):
        """
        Reads data from the FTDI device.

        Returns:
            list: The data read from the device.
        """
        # Get the number of bytes in the receive queue
        self.queue = self.device.getQueueStatus()
        # Read the data from the queue
        read = self.device.read(self.queue)
        data = []
        for char in read:
            data.append(char)
        return data
    
    def close(self):
        """
        Closes the connection to the FTDI device.
        """
        self.device.close()

def process_FTDI_readings(Obuff, Channels=15):
    """
    Processes the readings from the FTDI device.

    Args:
        Obuff (numpy.ndarray): The buffer of readings from the FTDI device.
        Channels (int, optional): The number of channels. Defaults to 15.

    Returns:
        numpy.ndarray: The processed readings.
    """
    vector = np.arange(48)
    # Reshape the vector to match the firmware design for 48 channels
    Channels = vector.reshape(3, 16, order='F').flatten()
    
    # Find the index of the starting sequence in the buffer
    ind = np.where(Obuff == 0)[0]
    for i in range(len(ind) - 100):
        if (Obuff[ind[i]] == 0 and Obuff[ind[i] + 3] == 16 and 
            Obuff[ind[i] + 6] == 32 and Obuff[ind[i] + 9] == 1):
            break

    # Delete the initial portion of the buffer before the start sequence
    Obuff = np.delete(Obuff, slice(0, ind[i]))
    Obuff = Obuff.astype(np.uint16)
    
    # Process the buffer to get the desired channels' data
    if len(Obuff[4::9] << 8) == len(Obuff[5::9]):
        Ocode1 = (Obuff[4::9] << 8) + Obuff[5::9]
    else:
        Ocode1 = (Obuff[4::9] << 8)[:-1] + Obuff[5::9]
    
    # Adjust the length to be a multiple of 16 and reshape the result
    Ocode1 = Ocode1[:-(len(Ocode1) % 16)]
    result = np.reshape(Ocode1, (16, int(len(Ocode1) / 16)), order='F') * 3.3 / 4096
    result = np.roll(result, -2, axis=0)
    return result

if __name__ == '__main__':
    # Initialize the FTDI device
    device = FTDI()
    readings = [0]
    # Get the current time
    start_time = time.time()
    # Read data for 3 seconds
    while time.time() - start_time < 3:
        data = device.read()
        if data:
            readings = np.concatenate([readings, data])
    
    # Process the readings
    proces = process_FTDI_readings(np.array(readings).flatten().astype(int))
    # Plot the results
    plt.figure()
    plt.plot(proces[13, :])
    
    # Close the FTDI device
    device.close()
    # Show the plot
    plt.show()
