import os
import sys
import csv
import time
import ydlidar
import subprocess
import signal
import threading


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

def generate_csv(file_name, data, timestamp):
    """
    Appends the Lidar scan data to the specified CSV file.
    
    :param file_name: Path to the CSV file.
    :param data: List of Lidar scan points.
    :param timestamp: The timestamp when the scan occurred.
    """
    # Ensure the directory for the file exists
    directory = os.path.dirname(file_name)
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Open the file in append mode and write data
    with open(file_name, mode='a', newline='') as file:
        writer = csv.writer(file)

        # Write each point in the data to the CSV with the corresponding timestamp
        for point in data:
            writer.writerow([timestamp, point.angle, point.range])  # Epoch Time, Angle, Distanc

def start_scanning(lidar, csv_file):
    global stop_event

    lidar.turnOn()

    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Epoch Time", "Angle", "Distance"])  # Header row

    print("Lidar scanning started.")
    
    while not stop_event.is_set():  # Check if stop_event is set to stop the loop
        outscan = ydlidar.LaserScan()  # Create a LaserScan object to store the scan data
        ret = lidar.doProcessSimple(outscan)  # Pass outscan to capture data

        if ret:
            epoch_time = time.time()  # Get current epoch time
            generate_csv(csv_file, outscan.points, epoch_time)
            time.sleep(1)  # Adjust the delay as needed
        else:
            print("Failed to get Lidar data.")

    # Stop the Lidar when stop_event is set
    lidar.turnOff()

def start_lidar(filename="lidar_data.csv"):
    """
    1. init the lidar
    2. create data directory if it doesnt exist
    3. check if the file exists, ret error if it does not
    4. create the thread for the lidar
    5. start the thread for the lidar
    """
    global lidar_process, lidar, stop_event
    print('************************************/nstarting lidar/n******************************')

    if lidar_process or lidar:
        return ERROR(400, 'Lidar is already running')

    lidar = init_lidar()
    print('1.init lidar')
    """
    data_dir = os.path.join('/usr', 'src', 'app','scripts','data')
    if not os.path.isdir(data_dir):
        os.mkdir(data_dir)

    if os.path.isfile(os.path.join(data_dir, filename)):
        return ERROR(400, f"File {filename} already exists")
    """
    csv_file = os.path.join('lidar_files', filename)

    stop_event.clear()

    lidar_process = threading.Thread(target=start_scanning, args=(lidar, csv_file))
    lidar_process.start()

    return SUCCESS(200, "Lidar Scanning Started") 

def stop_lidar():
    global lidar_process, lidar
    if not lidar_process or not lidar:
        return ERROR(400, 'Lidar is not running')

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
