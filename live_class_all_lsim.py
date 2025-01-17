# Live visualisation routine for sensor readings

# Internal imports
from config.path_config import *
from file_handler import Data_Handler
from connection import *
from reconstruction import delete_offset

# External imports
from scipy import signal
import numpy as np
import yaml
import time
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
from PyQt6 import QtWidgets

import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, 
                             QComboBox, QSpinBox, QLabel, QLineEdit, QSizePolicy, 
                             QCheckBox)

class MyWindow(QWidget):
    """
    A class to create a GUI for real-time visualization of piezoelectric sensor readings.
    """
    
    def __init__(self, reconstruct: bool):
        """
        Initializes the GUI window and its components.

        Args:
            reconstruct (bool): Flag to indicate whether to perform reconstruction.
        """
        super().__init__()  
        self.reconstruct = reconstruct  # Flag for reconstruction 0 - don't reconstruct, 1 - reconstruct

        # Load parameters from configuration file
        with open(CONFIG_PATH + CONFIGURATION_FILE, 'r') as f:
            data = yaml.safe_load(f)
            for key, value in data.items():
                setattr(self, key, value)
        
        self.c = self.Rf * self.Cf
        self.tau = self.d33 / self.Cf

        # Initialize parameters
        self.unlocked = 1  # Flag for locking the readings
        self.current_channel = 0  # The default channel for readings
        self.additional_channels = []  # Allocation for array storing additional channels
        self.candidate_channel = 1  # The channel to be added as an additional channel
        self.roll_duration = 10000  # Length of the shown signal
        self.offsets = np.zeros([15 + 1, 1])  # Allocation for offset data
        self.sim_init = [0]

        # Load calibration data from YAML file
        with open(CONFIG_PATH + 'calibration_params.yaml', 'r') as file:
            self.calibration_parameters = yaml.safe_load(file)
        channel_no = 0
        for entry in self.calibration_parameters['channels']:
            self.offsets[entry["number"] - 1] = entry['offset_mean']
            if entry["number"] == 13:
                self.a = entry['a']
            channel_no += 1  # Count how many channels there are in the config file

        # Additional parameters for collecting data in real time
        self.sample_count = 0
        self.force = np.array([0])
        self.sample_data = [0]
        self.reading_data = np.ones((channel_no + 1, 1)) * self.offsets

        # Customize window
        self.setWindowTitle('Piezoelectric readings')

        # Create plot
        self.plot = pg.PlotWidget()
        self.vb = self.plot.getViewBox()
        self.plot.setYRange(-0.3, 3.5, padding=0)
        self.plot.showGrid(x=False, y=True, alpha=0.5)
        y_ticks = [(i, str("{:.2f}".format(i))) for i in np.arange(-0.3, 3.6, 0.1)]
        self.plot.getAxis('left').setTicks([y_ticks])
        self.curve = self.plot.plot(pen='g')
        self.curve2 = self.plot.plot(pen='r')
        self.curves = []
        for i in range(16):
            self.curves.append(self.plot.plot(pen='g'))

        # Create buttons
        self.reset_button = QPushButton('Reset')
        self.lock_button = QPushButton('Lock')
        self.save_button = QPushButton('Save')
        self.mean_button = QPushButton('Get Mean')
        self.addchannel_button = QPushButton('Add channel')
        self.delchannel_button = QPushButton('Del channel')
        self.calibrate_offset_button = QPushButton('Calibrate offset')
        self.calibrate_trend_button = QPushButton('Calibrate trend')

        # Create checkbox
        self.checkbox_GT = QCheckBox('Enable GT', self)
        self.checkbox_trend = QCheckBox('Disable trend', self)
        
        # Customize buttons
        self.lock_button.setCheckable(True)

        # Create label
        self.mean_label = QLabel("0")

        # Create QLineEdit to enter a name
        self.name_edit = QLineEdit()

        # Create Combo list
        self.list = QComboBox()
        self.list.addItems(['1', '2', '3','4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16'])

        # Create Spin Box
        self.spin_box_roll = QSpinBox()
        self.spin_box_channels = QSpinBox()
        # Customize Spin Boxes
        self.spin_box_roll.setMinimum(2000)  # Set minimum value (optional)
        self.spin_box_roll.setMaximum(400000)  # Set maximum value (optional)
        self.spin_box_roll.setSingleStep(10000)  # Set the increment to 1000

        self.spin_box_channels.setMinimum(1)  # Set minimum value (optional)
        self.spin_box_channels.setMaximum(16)  # Set maximum value (optional)
        
        # Connect the button's clicked signal to a slot (function)
        self.reset_button.clicked.connect(self._reset_button_clicked)
        self.lock_button.clicked.connect(self._lock_button_clicked)
        self.save_button.clicked.connect(self._save_button_clicked)
        self.mean_button.clicked.connect(self._mean_button_clicked)
        self.addchannel_button.clicked.connect(self._addchannels_clicked)
        self.delchannel_button.clicked.connect(self._delchannels_clicked)
        self.calibrate_offset_button.clicked.connect(self.calibrate_offset)
        self.calibrate_trend_button.clicked.connect(self.calibrate_trend)

        self.checkbox_GT.stateChanged.connect(self.GT_state_change)
        self.checkbox_trend.stateChanged.connect(self.trend_state_change)

        self.list.activated.connect(self._change_channel)

        self.spin_box_roll.valueChanged.connect(self._roll_change)
        self.spin_box_channels.valueChanged.connect(self._candidate_channel)
        self.name_edit.textChanged.connect(self._update_file_name)

        # Set the initial channel for the combo box
        self.list.setCurrentIndex(self.current_channel)
        self.spin_box_roll.setValue(10000)

        # Create a layout and add the button to it
        layout = QtWidgets.QGridLayout()
        # Add objects to the layout
        layout.addWidget(self.reset_button, 0, 0)
        layout.addWidget(self.lock_button, 1, 0)
        layout.addWidget(self.save_button, 2, 0)
        layout.addWidget(self.name_edit, 3, 0)
        layout.addWidget(self.mean_button, 4, 0)
        layout.addWidget(self.mean_label, 5, 0)
        self.mean_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.list, 6, 0)
        layout.addWidget(self.spin_box_roll, 7, 0)
        layout.addWidget(self.spin_box_channels, 8, 0)
        layout.addWidget(self.addchannel_button, 9, 0)
        layout.addWidget(self.delchannel_button, 10, 0)
        layout.addWidget(self.calibrate_offset_button, 11, 0)
        layout.addWidget(self.calibrate_trend_button, 12, 0)
        layout.addWidget(self.checkbox_GT, 13, 0)        
        layout.addWidget(self.checkbox_trend, 14, 0)
        layout.addWidget(self.plot, 0, 1, 20, 1)

        # Set the layout for the main window
        layout.setColumnStretch(1, 1)  # Allow column 1 to stretch horizontally

        # If reconstruction is enabled, add reconstruction-specific components
        if self.reconstruct:
            # Reset force button
            self.reset_force_button = QPushButton('Reset Force')
            self.reset_force_button.clicked.connect(self._reset_force_button_clicked)
            layout.addWidget(self.reset_force_button, 15, 0)

            # Plot widget for reconstructed force
            self.plot_force = pg.PlotWidget()
            numerator = np.array([self.Rf * self.Cf, 1])
            denominator = np.array([self.Rf * self.d33, 0])
            self.system = signal.lti(numerator, denominator)
            self.r_curve = self.plot_force.plot(pen='g')
            layout.addWidget(self.plot_force, 0, 2, 20, 2)
            self.vb2 = self.plot_force.getViewBox()

        self.setLayout(layout)

    def _reset_force_button_clicked(self):
        """
        Resets the force values and initial values for reconstruction.
        """
        self.force = np.zeros(np.shape(self.force))
        self.sim_init = [0]

    def _reset_button_clicked(self):
        """
        Resets the auto-range of the plot view boxes.
        """
        self.vb.enableAutoRange(axis='x')
        if self.reconstruct:
            self.vb2.enableAutoRange(axis='x')

    def _lock_button_clicked(self):
        """
        Toggles the lock state for reading updates.
        """
        if self.lock_button.isChecked():
            self.unlocked = 0
        else:
            self.unlocked = 1
    
    def _save_button_clicked(self):
        """
        Saves the current reading data, reconstruction, and metadata.
        """
        if hasattr(self, 'file_name'):
            file_name = self.file_name
        else:
            file_name = "live_reading"
        meta_description = "Investigating the time constant for the 13th sensor"

        DH = Data_Handler(file_name, np.transpose(self.reading_data))
        DH.save_response()
        if hasattr(self, 'force'):
            DH.save_reconstruction(self.force)
        DH.save_metadata(meta_description)
        DH.save_configuration()
        DH.save_figures(self.current_channel)

    def _addchannels_clicked(self):
        """
        Adds a candidate channel to the list of additional channels.
        """
        self.additional_channels.append(self.candidate_channel)

    def _delchannels_clicked(self):
        """
        Removes a candidate channel from the list of additional channels.
        """
        self.additional_channels.remove(self.candidate_channel)
        self.curves[self.candidate_channel].clear()

    def _roll_change(self, value):
        """
        Updates the roll duration for the plot.

        Args:
            value (int): The new roll duration.
        """
        self.roll_duration = value

    def _candidate_channel(self, value):
        """
        Updates the candidate channel for additional channels.

        Args:
            value (int): The new candidate channel.
        """
        self.candidate_channel = value - 1
        print(self.candidate_channel)

    def _change_channel(self):
        """
        Updates the current channel for the plot.
        """
        self.current_channel = self.list.currentIndex()
        for i in range(16):
            self.curves[i].clear()

    def _mean_button_clicked(self):
        """
        Calculates and displays the mean of the current channel's data.
        """
        data = self.reading_data[:, -self.roll_duration:]
        data = data[self.current_channel]
        mean = np.mean(data)
        self.mean_label.setText(str(mean))

    def _update_file_name(self, text):
        """
        Updates the file name for saving data.

        Args:
            text (str): The new file name.
        """
        setattr(self, "file_name", text)

    def GT_state_change(self, state):
        """
        Handles the state change of the GT checkbox.

        Args:
            state (int): The state of the checkbox (checked/unchecked).
        """
        if state == 2:  # Checked
            self.label.setText('Checkbox is checked')
        else:  # Unchecked
            self.label.setText('Checkbox is unchecked')

    def trend_state_change(self, state):
        """
        Handles the state change of the trend checkbox.

        Args:
            state (int): The state of the checkbox (checked/unchecked).
        """
        print(state)

    def connection(self):
        """
        Establishes the connection to the piezoelectric sensor.
        """
        self.piezoE_sensor = FTDI()
        start_time = time.time()
        # Start gathering data to get a clear stream
        while time.time() - start_time < 1:
            pass
        print("Readings beginning!")

    def calibrate_offset(self):
        """
        Calibrates the offset for each channel based on current readings.
        """
        for entry in self.calibration_parameters['channels']:
            entry['offset_mean'] = np.mean(self.reading_data[entry["number"] - 1]).item()

        # Write updated data back to YAML file
        with open(CONFIG_PATH + 'calibration_params.yaml', 'w') as file:
            yaml.dump(self.calibration_parameters, file)
        
        for entry in self.calibration_parameters['channels']:
            self.offsets[entry["number"] - 1] = entry['offset_mean']

    def calibrate_trend(self):
        """
        Calibrates the trend for the reconstruction.
        """
        if self.reconstruct:
            x = np.linspace(0, len(self.force), len(self.force))
            self.a, self.b = np.polyfit(x, self.force, 1)
            print(self.a)
        for entry in self.calibration_parameters['channels']:
            entry['a'] = self.a.item()
            entry['b'] = self.b.item()

        # Write updated data back to YAML file
        with open(CONFIG_PATH + 'calibration_params.yaml', 'w') as file:
            yaml.dump(self.calibration_parameters, file)

    def update_reconstruct_plot(self):
        """
        Updates the plot with reconstructed force data.
        """
        readings = []
        data = self.piezoE_sensor.read()
        if data:
            readings.extend(data)
            if self.unlocked:
                readings = np.array(readings).flatten().astype(int)
                processed_readings = process_FTDI_readings(readings)
                self.reading_data = np.concatenate((self.reading_data, processed_readings), 1)
                self.reading_data = self.reading_data[:, -self.roll_duration:]

                processed_readings = delete_offset(processed_readings, self.offsets)
                t = np.linspace(0, np.size(processed_readings, 1) / self.T, np.size(processed_readings, 1))
                tout, new_force, self.sim_init = signal.lsim(self.system, processed_readings[self.current_channel, :], t, self.sim_init[-1])
                self.force = np.concatenate((self.force, new_force))
                self.force = self.force[-self.roll_duration:]
                trend = np.linspace(0, len(self.force), len(self.force)) * self.a
                if self.checkbox_trend.isChecked():
                    print(signal.find_peaks(self.force, threshold=30))
                self.r_curve.setData(self.force - trend)
                self.curves[self.current_channel].setData(delete_offset(self.reading_data[self.current_channel], self.offsets[self.current_channel]))

    def update_plot(self):
        """
        Updates the plot with current sensor readings.
        """
        readings = []
        data = self.piezoE_sensor.read()
        if data:
            readings.extend(data)
            if self.unlocked:
                readings = np.array(readings).flatten().astype(int)
                processed_readings = process_FTDI_readings(readings)
                self.reading_data = np.concatenate((self.reading_data, processed_readings), 1)
                self.reading_data = self.reading_data[:, -self.roll_duration:]

                self.curves[self.current_channel].setData(self.reading_data[self.current_channel])
                for i in self.additional_channels:
                    self.curves[i].setData(self.reading_data[i])

if __name__ == '__main__':
    app = QApplication(sys.argv)
    reconstruction = 0
    if reconstruction == 0:
        window = MyWindow(0)
        window.connection()
        timer = QtCore.QTimer()
        timer.timeout.connect(window.update_plot)
        timer.start(1)
    elif reconstruction == 1:
        window = MyWindow(1)
        window.connection()
        timer = QtCore.QTimer()
        timer.timeout.connect(window.update_reconstruct_plot)
        timer.start(1)
    window.show()
    sys.exit(app.exec())
