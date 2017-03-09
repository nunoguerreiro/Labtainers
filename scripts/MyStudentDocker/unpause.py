#!/usr/bin/env python

# Filename: unpause.py
# Description:
# This is the script to be run by the student to unpause container(s).
# Note:
# 1. It needs 'start.config' file, where
#    <labname> is given as a parameter to the script.
#

import glob
import json
import md5
import os
import re
import subprocess
import sys
import time
import zipfile
from netaddr import *
import ParseStartConfig

LABS_ROOT = os.path.abspath("../../labs/")

# Error code returned by docker inspect
SUCCESS=0
FAILURE=1

def isalphadashscore(name):
    # check name - alphanumeric,dash,underscore
    return re.match(r'^[a-zA-Z0-9_-]*$', name):

# Check to see if my_container_name container has been created or not
def IsContainerCreated(mycontainer_name):
    command = "docker inspect -f {{.Created}} %s 2> /dev/null" % mycontainer_name
    #print "Command to execute is (%s)" % command
    result = subprocess.call(command, shell=True)
    #print "Result of subprocess.call IsContainerCreated is %s" % result
    return result

def DoUnpause(start_config, mycwd, labname):
    host_home_xfer = start_config.host_home_xfer
    lab_master_seed = start_config.lab_master_seed
    #print "Do: Moreterm Multiple Containers and/or multi-home networking"

    # Reach here - Everything is OK - unpause the container
    for name, container in start_config.containers.items():
        mycontainer_name       = container.full_name
        mycontainer_image_name = container.image_name
        container_user         = container.user

        command = "docker unpause %s" % mycontainer_name
        #print "command is (%s)" % command
        os.system(command)

    return 0


# Usage: unpause.py <labname>
# Arguments:
#    <labname> - the lab to start
def main():
    #print "unpause.py -- main"
    num_args = len(sys.argv)
    if num_args < 2:
        sys.stderr.write("Usage: unpause.py <labname>\n")
        sys.exit(1)

    labname = sys.argv[1]
    mycwd = os.getcwd()
    myhomedir = os.environ['HOME']
    #print "current working directory for %s" % mycwd
    #print "current user's home directory for %s" % myhomedir
    #print "ParseStartConfig for %s" % labname
    lab_path          = os.path.join(LABS_ROOT,labname)
    config_path       = os.path.join(lab_path,"config")
    start_config_path = os.path.join(config_path,"start.config")

    start_config = ParseStartConfig.ParseStartConfig(start_config_path, labname, "student")

    DoUnpause(start_config, mycwd, labname)

    return 0

if __name__ == '__main__':
    sys.exit(main())

