FROM ubuntu:latest

# Install system dependencies
RUN apt-get update && apt-get install -y \
    cmake \
    pkg-config \
    python3 \
    python3-pip \
    python3-venv \
    swig \
    git \
    libusb-1.0-0-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up the project directory
# Clone the YDLidar SDK and build it
RUN mkdir /usr/src/app \
    && git clone https://github.com/YDLIDAR/YDLidar-SDK.git /usr/src/app/YDLidar-SDK \
    && cmake -B /usr/src/app/YDLidar-SDK/build -S /usr/src/app/YDLidar-SDK \
    && cmake --build /usr/src/app/YDLidar-SDK/build \
    && cmake --install /usr/src/app/YDLidar-SDK/build

# Create a virtual environment in /usr/src/app/venv
RUN python3 -m venv /usr/src/app/venv

# Install Django and other dependencies inside the virtual environment
COPY requirements.txt /usr/src/app/
COPY .env /usr/src/app/
RUN /usr/src/app/venv/bin/pip install --no-cache-dir /usr/src/app/YDLidar-SDK/
RUN /usr/src/app/venv/bin/pip install --no-cache-dir -r /usr/src/app/requirements.txt

# Set the virtual environment's Python and pip to be used by default
ENV PATH="/usr/src/app/venv/bin:$PATH"

# Copy your Django project and other scripts into the container
COPY ./scripts /usr/src/app/scripts
COPY ./lidar_service /usr/src/app/lidar_service

#RUN export PYTHONPATH="$PYTHONPATH:/usr/src/app/scripts"
ENV PYTHONPAT="/usr/src/app/scripts"

# Expose the Django default port (8000)
# EXPOSE 8000

# CMD ["/bin/bash"]
# CMD ["python", "/usr/src/app/lidar_service/manage.py", "runserver", "0.0.0.0:8000"]

