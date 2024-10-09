from datetime import datetime

import os
import sys
import csv
import time
import ydlidar
import subprocess
import signal
import threading

import h5py
import numpy as np

# track status of lidar
lidar_process = None
lidar = None

ERROR = lambda error_code, message : {'error_code': error_code, 'message': message}
SUCCESS = lambda status, message : {'status': status, 'message': message}
stop_event = threading.Event() 

def init_lidar():
    lidar = ydlidar.CYdLidar()
    lidar.setlidaropt(ydlidar.LidarPropSerialPort, "/dev/ttyUSB0")
    lidar.setlidaropt(ydlidar.LidarPropSerialBaudrate, 128000)
    lidar.setlidaropt(ydlidar.LidarPropLidarType, ydlidar.TYPE_TOF)
    lidar.setlidaropt(ydlidar.LidarPropDeviceType, ydlidar.YDLIDAR_TYPE_SERIAL)
    lidar.setlidaropt(ydlidar.LidarPropScanFrequency, 10.0)
    lidar.setlidaropt(ydlidar.LidarPropSampleRate, 5)
    lidar.setlidaropt(ydlidar.LidarPropSingleChannel, True)

    ret = lidar.initialize()
    if not ret:
        print("Lidar initialization failed.")
        sys.exit(1)

    return lidar

def append_to_hdf5(timestamp_dataset, angle_dataset, distance_dataset, epoch_time, angles, distances):
    """
    Appends data to the HDF5 datasets for the LiDAR readings.
    
    :param timestamp_dataset: The HDF5 dataset for timestamps.
    :param angle_dataset: The HDF5 dataset for angles.
    :param distance_dataset: The HDF5 dataset for distances.
    :param epoch_time: The timestamp for the current scan.
    :param angles: List of angle readings.
    :param distances: List of distance readings.
    """
    # Calculate the number of new entries
    num_new_entries = len(angles)

    # Resize the datasets to accommodate the new data
    timestamp_dataset.resize(timestamp_dataset.shape[0] + num_new_entries, axis=0)
    angle_dataset.resize(angle_dataset.shape[0] + num_new_entries, axis=0)
    distance_dataset.resize(distance_dataset.shape[0] + num_new_entries, axis=0)

    # Append the new data to the end of the datasets
    timestamp_dataset[-num_new_entries:] = np.full(num_new_entries, epoch_time)
    angle_dataset[-num_new_entries:] = angles
    distance_dataset[-num_new_entries:] = distances

def start_scanning(lidar, h5_file):
    global stop_event

    # Turn on the LiDAR sensor
    lidar.turnOn()
    print("LiDAR scanning started.")

    # Open the HDF5 file in append mode to write data
    with h5py.File(h5_file, 'a') as f:
        # Get today's date as the group name
        today_date = datetime.now().strftime('%Y_%m_%d')
        
        # Ensure the group for today exists
        if today_date not in f:
            print(f"Error: Group '{today_date}' not found in the HDF5 file.")
            return

        # Access today's group
        day_group = f[today_date]
        
        # Find the last session created (or any other session as needed)
        existing_sessions = [key for key in day_group.keys() if key.startswith('session_')]
        latest_session = max(existing_sessions, default=None)
        
        if latest_session is None:
            print(f"Error: No session found under '{today_date}' group.")
            return

        # Access the session group
        session_group = day_group[latest_session]

        # Access the datasets for timestamp, angle, and distance
        timestamp_dataset = session_group['readings/timestamp']
        angle_dataset = session_group['readings/angle']
        distance_dataset = session_group['readings/distance']

        while not stop_event.is_set():
            outscan = ydlidar.LaserScan()  # Create a LaserScan object to store the scan data
            ret = lidar.doProcessSimple(outscan)  # Pass outscan to capture data

            if ret:
                epoch_time = time.time()  # Get the current epoch time

                # Extract the angle and distance data from the scan points
                angles = [point.angle for point in outscan.points]
                distances = [point.range for point in outscan.points]

                # Append data to the HDF5 file
                append_to_hdf5(timestamp_dataset, angle_dataset, distance_dataset, epoch_time, angles, distances)

                # Adjust the delay as needed (e.g., for a 1-second interval)
                time.sleep(1)
            else:
                print("Failed to get LiDAR data.")

    # Turn off the LiDAR when `stop_event` is set
    lidar.turnOff()
    print("LiDAR scanning stopped.")


def start_lidar(filename="lidar_data.csv"):
    """
    1. init the lidar
    2. create data directory if it doesnt exist
    3. check if the file exists, ret error if it does not
    4. create the thread for the lidar
    5. start the thread for the lidar
    """
    global lidar_process, lidar, stop_event

    lidar = init_lidar()

    h5_file = os.path.join('lidar_files', filename)
    with h5py.File(h5_file, 'a') as f:
        # Generate today's date as the group name
        today_date = datetime.now().strftime('%Y_%m_%d')
        
        # Check if the day group exists, and create it if not
        if today_date not in f:
            day_group = f.create_group(today_date)
            print(f"Group '{today_date}' created.")
        else:
            day_group = f[today_date]
        
        # Get the existing session subgroups in the day's group
        existing_sessions = [key for key in day_group.keys() if key.startswith('session_')]
        
        next_session_number = len(existing_sessions) + 1
        next_session_name = f'session_{next_session_number:03d}'
        
        session_group = day_group.create_group(next_session_name)
        print(f"Session group '{next_session_name}' created under '{today_date}'.")
        session_group.create_dataset('readings/timestamp', shape=(0,), maxshape=(None,), dtype='float64')
        session_group.create_dataset('readings/angle', shape=(0,), maxshape=(None,), dtype='float32')
        session_group.create_dataset('readings/distance', shape=(0,), maxshape=(None,))
        session_group.attrs['start_time'] = datetime.now().isoformat()
    
    stop_event.clear()

    lidar_process = threading.Thread(target=start_scanning, args=(lidar, h5_file))
    lidar_process.start()

    return SUCCESS(200, "Lidar Scanning Started") 

def stop_lidar():
    global lidar_process, lidar

    stop_event.set()
    lidar_process.join()
    lidar_process = None

    cleanup()
    return SUCCESS(200, 'Lidar stopped successfully')

def cleanup():
    global lidar
    if not lidar:
        return ERROR(400, 'Cleanup called but lidar not initialized.')
    lidar.turnOff()
    lidar.disconnecting()

    lidar = None
    print('Lidar cleanup complete.')
