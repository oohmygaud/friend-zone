#!/usr/bin/env bash

docker run -it --rm -p 2015:2015 -v $PWD:/db --name websql acttaiwan/phpliteadmin
