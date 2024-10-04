### **REST API Service Specification for Lidar Data Collection and Retrieval**

**Role**: Principle Software Engineer  
**Project**: REST API Service for Controlling and Accessing Lidar Data on Raspberry Pi

---

### **Overview**

This service is responsible for managing Lidar sensor data collection from a YDLidar connected to a Raspberry Pi and making this data available via a RESTful API. The service will allow starting and stopping the Lidar data collection, list available data files, and download the data in CSV format.

---

### **Architecture Overview**

1. **Technology Stack**:
   - **Hardware**: YDLidar sensor connected via `/dev/ttyUSB0` on Raspberry Pi.
   - **Backend Framework**: Django with Django Rest Framework (DRF).
   - **Storage**: HDF5 file format for efficient data storage and dynamic conversion to CSV format on demand.
   - **Containerization**: Dockerized service running on Raspberry Pi.
   - **Networking**: Accessible within the home network, bound to all network interfaces on the Raspberry Pi.
   - **Concurrency Control**: Only one Lidar service may be running at any time to prevent conflicts.
  
2. **Core Service Capabilities**:
   - Start and stop Lidar data collection.
   - List available Lidar data files.
   - Download Lidar data as a CSV file.

---

### **API Endpoints**

#### 1. **POST /lidar/start**
   - **Description**: Starts the Lidar service and begins recording data into an HDF5 file.
   - **Request**:
     - **Body**: `{ "filename": "yourfilename.h5" }`
   - **Response**:
     - **Success**: `{ "success": "Lidar started successfully" }`
     - **Error**: `{ "error": "Lidar is already running" }`
   - **Error Handling**:
     - If the Lidar service is already running, an error is returned with status code `400`.
   - **Additional Notes**:
     - A single instance of the Lidar process is permitted at a time. The service tracks the process state and rejects subsequent start requests until the current process is stopped.

#### 2. **GET /lidar/stop**
   - **Description**: Stops the Lidar service and terminates data collection.
   - **Response**:
     - **Success**: `{ "success": "Lidar stopped successfully" }`
     - **Error**: `{ "error": "Lidar is not running" }`
   - **Error Handling**:
     - If no Lidar service is currently running, an error response is returned with status code `400`.
   - **Additional Notes**:
     - This endpoint gracefully terminates the background process running the Lidar data collection.

#### 3. **GET /lidar/files**
   - **Description**: Lists all available Lidar data files.
   - **Response**:
     ```json
     {
       "files": [
         "data_2024_01_01.h5",
         "data_2024_01_02.h5"
       ]
     }
     ```
   - **Additional Notes**:
     - The response includes the filenames of all stored HDF5 files in the storage directory.

#### 4. **GET /lidar/files/{filename}/download**
   - **Description**: Downloads the specified Lidar data file as a CSV.
   - **Parameters**:
     - **URL Path**: `{filename}` (e.g., `/lidar/files/data_2024_01_01/download`)
   - **Response**:
     - A CSV file generated from the requested HDF5 file.
     - If the file does not exist, an error response is returned with status code `404`.
   - **CSV Headers**:
     - `timestamp`, `distance`, `angle`
   - **Error Handling**:
     - If the specified file does not exist, return `{ "error": "File not found" }`.

---

### **Background Process Management**

The Lidar data collection process runs asynchronously in the background using Python's `subprocess` module. It will:
- Write data to the specified HDF5 file in a buffered manner to ensure data integrity and reduce I/O overhead.
- Only allow one active process at a time. A global state or locking mechanism (e.g., a flag or PID tracking) ensures that multiple instances of the Lidar process are not spawned simultaneously.

#### **Subprocess Handling**:
- **Starting the Lidar Service**:
  - Managed via `subprocess.Popen()`.
  - The process should handle file locking to prevent corruption if the Pi crashes during a write.
- **Stopping the Lidar Service**:
  - The process is stopped gracefully via `process.terminate()`.
  - On stopping, the HDF5 file should be closed properly to prevent corruption.

---

### **Data Storage and Reliability**

1. **HDF5 Format**:
   - Lidar data is written to an HDF5 file due to its efficiency in handling large sequential data streams.
   - Data will be written in chunks to the HDF5 file to avoid frequent I/O operations and prevent corruption in case of crashes.
   - Every write operation will be followed by a periodic `flush` to ensure that data is consistently synced to disk.

2. **Conversion to CSV**:
   - On request (`GET /lidar/files/{filename}/download`), the service will read from the HDF5 file and dynamically convert the data to CSV format using **pandas** or Python's `csv` module.

---

### **Concurrency Management**

- **Concurrency Control**: 
   - A global flag (`is_lidar_running`) ensures that no other start requests are processed while the Lidar is running.
   - Only one instance of the Lidar subprocess is allowed to run at a time.
   - This mechanism prevents multiple writes to the same file or process interference.

- **Process Termination**:
   - The Lidar collection process must be stopped explicitly by the `/lidar/stop` endpoint. This ensures the integrity of the data collected and avoids abrupt file termination.

---

### **Error Handling**

1. **Lidar Service Already Running**:
   - If the Lidar process is already running and a new start request is made, the service will return an error response: `{ "error": "Lidar is already running" }`.

2. **File Not Found**:
   - If a file requested for download does not exist, the service will return a `404 Not Found` with a message: `{ "error": "File not found" }`.

3. **Unexpected Errors**:
   - In case of unforeseen errors (e.g., failed subprocess, corrupted data, etc.), the service will return an appropriate `500 Internal Server Error` response with a message indicating the failure reason.

---

### **Performance Considerations**

- **Efficient Data Writes**:
   - Data is written in chunks to HDF5 files to optimize performance and minimize disk I/O operations.
   - The use of HDF5 ensures that data is compressed and stored efficiently, making both writing and reading faster.

- **Data Integrity**:
   - Data writes are periodically flushed to disk to prevent data loss in case of power failure or crashes.
   - The service will ensure that the Lidar data is properly closed and synced on process termination.

---

### **Network Accessibility**

The service will be available within the home network by binding to `0.0.0.0`. Port forwarding can be configured on the router if external access is required. Proper security considerations (e.g., firewall, VPN) should be in place for accessing the service remotely.

---

### **Next Steps**

1. **Implement the Subprocess Management for Lidar**: Implement starting and stopping of the Lidar process using `subprocess.Popen()` with proper concurrency control.
2. **Implement the API Endpoints**: Develop the endpoints using Django Rest Framework and ensure they return appropriate responses.
3. **Test and Deploy**: Test the service on the Raspberry Pi, ensuring data integrity, process management, and that files are correctly stored and downloadable as CSV.

---

