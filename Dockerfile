FROM ubuntu:latest

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
	
# download, build, & install YDLidar-SDK
RUN mkdir /usr/src/app \
	&& git clone https://github.com/YDLIDAR/YDLidar-SDK.git /usr/src/app/YDLidar-SDK \
	&& mkdir /usr/src/app/YDLidar-SDK/build

RUN cmake -B /usr/src/app/YDLidar-SDK/build -S /usr/src/app/YDLidar-SDK \
    && cmake --build /usr/src/app/YDLidar-SDK/build \
    && cmake --install /usr/src/app/YDLidar-SDK/build
    
# install the python api
RUN python3 -m venv /usr/src/app/venv
COPY requirements.txt /usr/src/app/YDLidar-SDK/
RUN /usr/src/app/venv/bin/pip install --no-cache-dir /usr/src/app/YDLidar-SDK/
RUN /usr/src/app/venv/bin/pip install --no-cache-dir -r /usr/src/app/YDLidar-SDK/requirements.txt

# Set environment variable to use the virtual environment Python by default
ENV PATH="/usr/src/app/venv/bin:$PATH"

COPY ./scripts /usr/src/app/scripts

CMD ["bin/bash"]
