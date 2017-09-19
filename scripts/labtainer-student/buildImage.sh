#!/bin/bash
: <<'END'
This software was created by United States Government employees at 
The Center for the Information Systems Studies and Research (CISR) 
at the Naval Postgraduate School NPS.  Please note that within the 
United States, copyright protection is not available for any works 
created  by United States Government employees, pursuant to Title 17 
United States Code Section 105.   This software is in the public 
domain and is not subject to copyright. 
END

# Usage: buildImage.sh <labname> <imagename> <user_name> <force_build> <lab_top>
#        <force_build> is either true or false

lab=$1
imagename=$2
labimage=$lab.$imagename.student
user_name=$3
force_build=$4 
LAB_TOP=$5 
#------------------------------------V
if [ "$#" -eq 6 ]; then
    registry=$6 
elif [ "$#" -eq 5 ]; then
    registry=mfthomps
else
    echo "Usage: buildImage.sh <labname> <imagename> <user_name> <force_build> <LAB_TOP> [registry]"
    echo "   <force_build> is either true or false"
    echo "   <LAB_TOP> is a path to the trunk/labs directory"
    echo "   registry is an optional name of an alternate docker hub registry"
    exit
fi

#------------------------------------^

echo "Labname is $lab with image name $imagename"

LAB_DIR=$LAB_TOP/$lab
if [ ! -d $LAB_DIR ]; then
    echo "$LAB_DIR not found as a lab directory"
    exit
fi
LABIMAGE_DIR=$LAB_TOP/$lab/$imagename/
if [ ! -d $LABIMAGE_DIR ]; then
    echo "$LABIMAGE_DIR not found"
    exit
fi
#------------------------------------V
imagecheck=$(docker search $registry/$labimage | grep $registry/$labimage)

if [ ! -z "$imagecheck" ] && [ $force_build = "False" ]; then
    #create tmp folder
    if [ ! -d "$LAB_DIR/dockerfiles/tmp" ]; then
    	mkdir $LAB_DIR/dockerfiles/tmp
    fi
    #create tmp file
    echo "FROM $registry/$labimage" > $LAB_DIR/dockerfiles/tmp/Dockerfile.$labimage.tmp 
else
    echo "Please wait while the lab is built"
    sleep 3
    ORIG_PWD=`pwd`
    echo $ORIG_PWD
    LAB_TAR=$LAB_DIR/$labimage.tar.gz
    SYS_TAR=$LAB_DIR/sys_$labimage.tar.gz
    TMP_DIR=/tmp/$labimage
    rm -rf $TMP_DIR
    mkdir $TMP_DIR
    mkdir $TMP_DIR/.local
    cp -pr $LAB_DIR/config $TMP_DIR/.local/ 2>>/dev/null
    cp -pr bin/ $TMP_DIR/.local/  2>>/dev/null
    cp -p $LAB_DIR/bin/* $TMP_DIR/.local/bin 2>>/dev/null
    chmod a+x $TMP_DIR/.local/bin/* 2>>/dev/null
    cp -p $LABIMAGE_DIR/_bin/* $TMP_DIR/.local/bin 2>>/dev/null
    chmod a+x $TMP_DIR/.local/bin/*
    cp -pr $LABIMAGE_DIR/. $TMP_DIR 2>>/dev/null
    # ugly!
    rm -fr $TMP_DIR/_bin
    rm -fr $TMP_DIR/_system
    mkdir $TMP_DIR/.local/result
    cd $TMP_DIR
    tar --atime-preserve -zcvf $LAB_TAR .
    if [ -d $LABIMAGE_DIR/_system ]; then
        cd $LABIMAGE_DIR/_system
        tar --atime-preserve -zcvf $SYS_TAR .
    else
        echo nothing at $LABIMAGE_DIR/_system
        mkdir $LABIMAGE_DIR/_system
        cd -p $LABIMAGE_DIR/_system
        tar --atime-preserve -zcvf $SYS_TAR .
    fi
fi
#---------------------------------------------------------------^
cd $LAB_TOP
dfile=Dockerfile.$labimage
#---------------------------------V
if [ ! -z "$imagecheck" ] && [ $force_build = "False" ]; then 
    docker build --pull -f $LAB_DIR/dockerfiles/tmp/$dfile.tmp -t $labimage .
else
    echo "cmd: docker build --build-arg lab=$labimage --build-arg labdir=$lab --build-arg imagedir=$imagename --build-arg user_name=$user_name --pull -f $LAB_DIR/dockerfiles/$dfile -t $labimage ."
    docker build --build-arg lab=$labimage --build-arg labdir=$lab --build-arg imagedir=$imagename --build-arg user_name=$user_name --pull -f $LAB_DIR/dockerfiles/$dfile -t $labimage .
fi
#---------------------------------^
result=$?
echo "removing temporary $dfile, reference original in $LAB_DIR/dockerfiles/$dfile"
#rm $LABIMAGE_DIR
cd $ORIG_PWD
if [ $result != 0 ]; then
    echo "Error in docker build result $result"
    exit 1
fi
