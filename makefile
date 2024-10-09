# Makefile for Lidar App Docker Management

# Variables
DOCKER_IMAGE = lidar-app
DOCKER_DEVICE = /dev/ttyUSB0
DOCKER_PORT = 8000:8000
DOCKER_CONTAINER_NAME = lidar-container
LOCAL_APP_DIR = $(PWD)/lidar_files
CONTAINER_APP_DIR = /lidar_files

# Default command: build the Docker image
build:
	docker build -t $(DOCKER_IMAGE) .

# Stop and remove the existing container if it exists
clean-container:
	@if [ $$(docker ps -a -q -f name=$(DOCKER_CONTAINER_NAME)) ]; then \
		docker stop $(DOCKER_CONTAINER_NAME); \
		docker rm $(DOCKER_CONTAINER_NAME); \
	fi

# Stop the running container
stop:
	docker stop $(DOCKER_CONTAINER_NAME)

# Remove the container after stopping it
clean: stop
	docker rm $(DOCKER_CONTAINER_NAME)

# Run Django makemigrations inside the container
makemigrations:
	docker exec -it $(DOCKER_CONTAINER_NAME) python /usr/src/app/lidar_service/manage.py makemigrations

# Run Django migrate inside the container
migrate:
	docker exec -it $(DOCKER_CONTAINER_NAME) python /usr/src/app/lidar_service/manage.py migrate
	
# Run the container in interactive mode with volume mount
run: clean-container
	docker run --name $(DOCKER_CONTAINER_NAME) \
		--device=$(DOCKER_DEVICE):$(DOCKER_DEVICE) \
		-p $(DOCKER_PORT) \
		-v $(LOCAL_APP_DIR):$(CONTAINER_APP_DIR) \
		-it $(DOCKER_IMAGE)

# Run the container in detached mode with volume mount
run-detached: clean-container
	docker run --name $(DOCKER_CONTAINER_NAME) \
		--device=$(DOCKER_DEVICE):$(DOCKER_DEVICE) \
		-p $(DOCKER_PORT) \
		-v $(LOCAL_APP_DIR):$(CONTAINER_APP_DIR) \
		-d $(DOCKER_IMAGE)

shell:
	docker exec -it lidar-container sh 

# Shortcut to build, run, and start the container
build-run: build run

# Rebuild the image, run the container in detached mode, and make migrations
setup-detached: build run-detached makemigrations migrate

