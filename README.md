# YDLidar Project

This project reads data from a YDLidar sensor connected to a Raspberry Pi and writes the scanned data to a CSV file. The project is containerized using Docker, and the Lidar control script is executed inside the Docker container.

## Table of Contents

- [Project Overview](#project-overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Project](#running-the-project)
- [Accessing the Data](#accessing-the-data)
- [Troubleshooting](#troubleshooting)

## Project Overview

This project interfaces with a YDLidar sensor using the YDLidar SDK and generates a CSV file containing angle and range data collected from the sensor. The CSV file is saved in a specific directory within the Docker container, which can be accessed from the host machine.

The project is built using:
- **Python** (for the Lidar control script)
- **YDLidar SDK** (for communicating with the Lidar)
- **Docker** (for containerizing the environment)

## Prerequisites

1. **Raspberry Pi**: The Raspberry Pi must be running Docker. You can install Docker by following [this guide](https://docs.docker.com/engine/install/raspberry-pi-os/).
2. **YDLidar Sensor**: The YDLidar must be connected to the Raspberry Pi via USB.
3. **Docker Engine**: Ensure that Docker Engine is installed and running on the Raspberry Pi.

## Installation

1. **Clone the repository** (or copy the necessary files) to your Raspberry Pi:
    ```bash
    git clone <repository-url>
    cd <repository-folder>
    ```

2. **Build the Docker image**:
    ```bash
    docker build -t lidar-app .
    ```

   This command will build the Docker image, install the necessary dependencies, and prepare the environment for running the Lidar control script.

## Running the Project

1. **Run the Docker container**:
    ```bash
    docker run --device=/dev/ttyUSB0:/dev/ttyUSB0 -v /home/pi/lidar-data:/usr/src/app/scripts/data -it lidar-app
    ```

    - `--device=/dev/ttyUSB0:/dev/ttyUSB0`: Maps the YDLidar device (usually connected at `/dev/ttyUSB0`) to the container so the container can access it.
    - `-v /home/pi/lidar-data:/usr/src/app/scripts/data`: Maps the local folder `/home/pi/lidar-data` to the container's `/usr/src/app/scripts/data` directory where the CSV file will be written.
    - `-it`: Runs the container in interactive mode with a terminal attached.
    - `lidar-app`: Name of the Docker image.

2. **Run the Lidar control script** inside the container:
    ```bash
    python /usr/src/app/scripts/lidar_control.py
    ```

    This will start the Lidar, collect data, and write it to `lidar_data.csv` inside the `/usr/src/app/scripts/data` directory.

3. **Stopping the script**: Press `Ctrl+C` to stop the scanning.

## Accessing the Data

Once the script has finished running, the CSV file (`lidar_data.csv`) will be saved to the directory `/home/pi/lidar-data` on the Raspberry Pi, thanks to the volume mapping. You can access it by navigating to that folder:

```bash
cd /home/pi/lidar-data
```
