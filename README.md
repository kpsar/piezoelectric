# Piezoelectric Sensor Data Collection and Analysis

This repository contains code for collecting, processing, and visualizing data from piezoelectric sensors. The project uses FTDI devices to read data, process the readings, and perform real-time visualization and analysis.

## Table of Contents

1. [Introduction](#introduction)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
    - [Data Collection](#data-collection)
    - [Real-Time Visualization](#real-time-visualization)
    - [Data Processing](#data-processing)

## Introduction

It is becoming more evident that the data about environment that can be derived from visual sensors is limited. For safe and efficient of robotic manipulation, new tactile solutions need to be developed. This project focuses on the enabling the use of piezoelectric sensors as a way to retrieve static force readings from the dynamic piezoelectric sensor readings. 

Piezoelectric sensors provide many advantages compared to conventionally used force and pressure sensors. They are more robust, dynamic, easier to manufacture and can be used in flexible solutions. To make them more useful it is important to enable the extraction of absolute force values from the sensor readings. 

## Requirements

- Python 3.x
- `ftd2xx`
- `numpy`
- `pandas`
- `matplotlib`
- `scipy`
- `pyqtgraph`
- `PyQt6`
- `yaml`
- `tqdm`

## Installation

```sh
# $ conda create --name <env> --file <this file>
```
## Configuration

Ensure that the configuration files are correctly set up in the `config` directory. The configuration files include:

- `path_config.py`: Contains paths for configuration files and reading directories.
- `setup_configuration.yaml`: Contains system parameters such as sampling frequency, capacitance values, and other important parameters required for data collection and processing.
- `calibration_params.yaml`: Contains calibration parameters for the sensors, including the mean offset values for each sensor channel.

### path_config.py

This file should define paths to various configuration files and directories used in the project. An example content might look like:

```python
CONFIG_PATH = '/path/to/config/'
READINGS_DIR = '/path/to/readings/'
```

### setup_configuration.yaml
This YAML file contains the system parameters needed for data collection and processing. An example content might look like:

### calibration_params.yaml
This YAML file contains the calibration parameters for each sensor channel. An example content might look like:

## Usage

### Data Collection
To collect data from the FTDI device, run the main.py script. This script initializes the sensor, reads data for a specified duration, processes the readings, and saves the results. The collected data is saved along with metadata and configuration details.

### Real-Time Visualization
To visualize the data in real-time, run the live_class_all_lsim.py script. This script sets up a PyQt window with real-time plotting using pyqtgraph. The GUI window allows for live updates of sensor readings and supports various functionalities such as resetting the view, locking the readings, saving data, and more.

### Data Processing
For offline data processing, use the reconstruction.py script. This script processes the collected data and performs system reconstruction, which can be visualized using matplotlib.
