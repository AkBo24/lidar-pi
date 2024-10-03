import os
import sys
import csv
import time
import ydlidar

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
    with open(file_name, mode='a', newline='') as file:  # 'a' for appending to the file
        writer = csv.writer(file)
        for point in data:
            writer.writerow([timestamp, point.angle, point.range])  # Epoch Time, Angle, Distance

def start_scanning(lidar, csv_file):
    lidar.turnOn()
    
    # Write the header only once, at the start of the CSV file
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Epoch Time", "Angle", "Distance"])  # Header row

    print("Lidar scanning... Press Ctrl+C to stop.")

    try:
        while True:
            outscan = ydlidar.LaserScan()  # Create a LaserScan object to store the scan data
            ret = lidar.doProcessSimple(outscan)  # Pass outscan to capture data

            if ret:
                # Get current epoch time
                epoch_time = time.time()
                
                # Append data to the CSV with epoch time
                generate_csv(csv_file, outscan.points, epoch_time)
                
                time.sleep(1)  # Adjust the delay as needed
            else:
                print("Failed to get Lidar data.")

    except KeyboardInterrupt:
        print("Stopping scan.")
        lidar.turnOff()

def main():
    # Initialize the Lidar
    lidar = init_lidar()

    # Create the /scripts/data directory if it doesn't exist
    data_dir = "/usr/src/app/scripts/data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created directory: {data_dir}")

    # Start scanning and generate the CSV file in the /scripts/data directory
    csv_file = os.path.join(data_dir, "lidar_data.csv")
    start_scanning(lidar, csv_file)

    # Deinitialize the Lidar after use
    lidar.turnOff()
    lidar.disconnecting()


if __name__ == "__main__":
    main()

