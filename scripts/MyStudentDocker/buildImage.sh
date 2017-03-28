#!/bin/bash

# Usage: buildImage.sh <labname> [<imagename>]
#        <imagename> is optional for lab that only has one image
lab=$1
has_image=0
if [ "$#" -eq 2 ]; then
    imagename=$2
    labimage=$lab.$imagename
    has_image=1
else
    labimage=$lab
    labimage=$lab.$lab
    has_image=1
fi

if [ $has_image == 1 ]; then
    echo "Labname is $lab with image name $imagename"
else
    echo "Labname is $lab using default image"
fi

LAB_DIR=`realpath ../../labs/$lab/`
if [ ! -d $LAB_DIR ]; then
    echo "$LAB_DIR not found as a lab directory"
    exit
fi
if [ $has_image == 1 ]; then
    LABIMAGE_DIR=`realpath ../../labs/$lab/$imagename/`
    if [ ! -d $LABIMAGE_DIR ]; then
        echo "$LABIMAGE_DIR not found"
        exit
    fi
else
    LABIMAGE_DIR=`realpath ../../labs/$lab/`
fi

ORIG_PWD=`pwd`
echo $ORIG_PWD
LAB_TAR=${ORIG_PWD}/$labimage.student.tar.gz
TMP_DIR=/tmp/$labimage
rm -rf $TMP_DIR
mkdir $TMP_DIR
mkdir $TMP_DIR/.local
cp $LABIMAGE_DIR/* $TMP_DIR 2>>/dev/null
cp -r $LAB_DIR/config $TMP_DIR/.local/ 2>>/dev/null
cp  -r bin/ $TMP_DIR/.local/  2>>/dev/null
cp  $LAB_DIR/bin/* $TMP_DIR/.local/bin 2>>/dev/null
cp  $LABIMAGE_DIR/bin/* $TMP_DIR/.local/bin 2>>/dev/null
mkdir $TMP_DIR/.local/result
cd $TMP_DIR
tar --atime-preserve -zcvf $LAB_TAR .local *
cd $ORIG_PWD
dfile=Dockerfile.$labimage.student
cp $LAB_DIR/dockerfiles/$dfile .
docker build --build-arg lab=$labimage -f ./$dfile -t $labimage:student .
echo "removing temporary $dfile, reference original in $LAB_DIR/dockerfiles/$dfile"
rm ./$dfile
