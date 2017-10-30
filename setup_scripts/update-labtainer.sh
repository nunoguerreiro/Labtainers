#!/bin/bash
wget https://my.nps.edu/documents/107523844/109121513/labtainer.tar/6fc80410-e87d-4e47-ae24-cbb60c7619fa -O labtainer.tar
cd ..
tar xf labtainer/labtainer.tar
docker pull mfthomps/labtainer.base
docker pull mfthomps/labtainer.network
docker pull mfthomps/labtainer.centos