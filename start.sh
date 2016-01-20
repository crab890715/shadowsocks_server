#!/bin/bash
cd $(cd `dirname $0`; pwd)
id ssclient >/dev/null || (useradd ssclient ;chown -R ssclient:ssclient . )
sudo -ussclient python server.py &
