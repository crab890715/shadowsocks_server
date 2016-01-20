#!/bin/bash
basepath=$(cd `dirname $0`; pwd)
cd $basepath
bash stop.sh
sleep 1
bash start.sh
