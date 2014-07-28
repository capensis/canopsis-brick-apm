#!/bin/bash

if [ "x-$1" == "x--d" ]; then
	rm -rf bin include lib lib64 *.pyc 
	rm -rf jmeter*
	rm -rf apache*
else
	python virtualenv.py .
	./bin/pip install amqp anyjson importlib kombu python-daemon
	mkdir -p ./jmx
	wget http://wwwftp.ciril.fr/pub/apache//jmeter/binaries/apache-jmeter-2.11.tgz -O jmeter.tgz 
	tar xf jmeter.tgz 
	ln -s apache-jmeter-2.11 jmeter 
	rm -f jmeter.tgz
	if [ ! -f config.json ]; then
		cp config.exemple.json config.json
	fi
fi
