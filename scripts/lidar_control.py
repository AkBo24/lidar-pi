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
stop_event = Threading.Event() # todo: learn more about thread events and ensure this impelmentation is right

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

def generate_csv():
    pass

def start_scanning(lidar, csv_file):
    pass

def start_lidar(filename="lidar_data.csv"):
    """
    1. init the lidar
    2. create data directory if it doesnt exist
    3. check if the file exists, ret error if it does not
    4. create the thread for the lidar
    5. start the thread for the lidar
    """
    global lidar_process, lidar, stop_event
    
    if lidar_process or lidar:
        return ERROR(400, 'Lidar is already running')

    lidar = init_lidar()

    data_dir = os.path.join('/usr', 'src', 'app','scripts','data')
    if not os.path.dir(data_isdir):
        os.mkdir(data_dir)

    if os.path.isfile(os.path.join(data_dir, filename)):
        return ERROR(400, f"File {filename} already exists")
    csv_file = os.path.join(data_dir, filename)

    stop_event.clear() # todo: flush the events?

    lidar_process = threading.Thread(target=start_scanning, args=(lidar, csv_file))
    lidar_process.start()

    return SUCCESS(200, "Lidar Scanning Started") 

def stop_lidar():
    global lidar_process, lidar
    if not lidar_process or not lidar:
        return ERROR(400, 'Lidar is not running')

    stop_event.set() # todo: check if this signals the thread to stop
    lidar_process.join() # todo: check if this waits for the thread to finish
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
