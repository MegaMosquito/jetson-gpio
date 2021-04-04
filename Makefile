DOCKERHUB_ID:=ibmosquito
NAME:=jetson-gpio
VERSION:=1.0.0
PORT:=6667

all: build run

build:
	docker build -t $(DOCKERHUB_ID)/$(NAME):$(VERSION) .

dev: build stop
	-docker rm -f $(NAME) 2> /dev/null || :
	docker run -it --privileged --name $(NAME) -p $(PORT):$(PORT) -v /sys/class/gpio:/sys/class/gpio -v /sys/devices:/sys/devices -v /sys/class/pwm:/sys/class/pwm --device /dev/spidev0.0:/dev/spidev0.0:rw --device /dev/gpiochip0:/dev/gpiochip0 --device /dev/gpiochip1:/dev/gpiochip1 --volume `pwd`:/outside $(DOCKERHUB_ID)/$(NAME):$(VERSION) /bin/sh

run: stop
	-docker rm -f $(NAME) 2>/dev/null || :
	docker run -d --privileged --name $(NAME) -p $(PORT):$(PORT) -v /sys/class/gpio:/sys/class/gpio -v /sys/devices:/sys/devices -v /sys/class/pwm:/sys/class/pwm --device /dev/spidev0.0:/dev/spidev0.0:rw $(DOCKERHUB_ID)/$(NAME):$(VERSION)

test:
	curl -X POST -sS localhost:$(PORT)/gpio/v1/mode/board
	curl -X POST -sS localhost:$(PORT)/gpio/v1/configure/40/out
	curl -X POST -sS localhost:$(PORT)/gpio/v1/40/1
	sleep 1
	curl -X POST -sS localhost:$(PORT)/gpio/v1/40/0
	sleep 1
	curl -X POST -sS localhost:$(PORT)/gpio/v1/40/1
	sleep 1
	curl -X POST -sS localhost:$(PORT)/gpio/v1/40/0

exec:
	docker exec -it $(NAME) /bin/sh

push:
	docker push $(DOCKERHUB_ID)/$(NAME):$(VERSION)

stop:
	-docker rm -f $(NAME) 2>/dev/null || :

clean: stop
	-docker rmi $(DOCKERHUB_ID)/$(NAME):$(VERSION) 2>/dev/null || :

.PHONY: all build dev run test exec stop clean