FROM ubuntu:20.04
WORKDIR /

RUN apt update
RUN apt install -y python3 python3-pip

# Install Jetson.GPIO
RUN pip3 install Jetson.GPIO

# Install flask (for the REST API server)
RUN pip3 install Flask

# Copy over the required files
COPY ./jetson-gpio.py .

# Run the daemon
CMD python3 jetson-gpio.py

