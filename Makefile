
DOCKERHUB_ID:=ibmosquito
NAME:=jetson-gpio
VERSION:=1.0.0
PORT:=6667

all: build run

build:
	docker build -t $(DOCKERHUB_ID)/$(NAME):$(VERSION) .

dev: build stop
	-docker rm -f $(NAME) 2> /dev/null || :
	docker run -it --privileged --name $(NAME) -p $(PORT):$(PORT) --volume `pwd`:/outside $(DOCKERHUB_ID)/$(NAME):$(VERSION) /bin/bash

run: stop
	-docker rm -f $(NAME) 2>/dev/null || :
	docker run -d --privileged --name $(NAME) -p $(PORT):$(PORT) $(DOCKERHUB_ID)/$(NAME):$(VERSION)

test:
	./test.sh

exec:
	docker exec -it $(NAME) /bin/sh

push:
	docker push $(DOCKERHUB_ID)/$(NAME):$(VERSION)

stop:
	-docker rm -f $(NAME) 2>/dev/null || :

clean: stop
	-docker rmi $(DOCKERHUB_ID)/$(NAME):$(VERSION) 2>/dev/null || :

.PHONY: all build dev run test exec stop clean
