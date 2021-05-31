#!/bin/bash

FOLDERS=(
    collection-01
#    collection-02
)

echo -e "\n>>> Build base image\n"
docker build -t adamos/dwp-simulator:base .

for coll in "${FOLDERS[@]}"
do
    if [ ! -z "$1" ] && [ ! "$1" == "$coll" ]; then
        echo -e "\n>>> SKIPPING $coll\n"
        continue
    fi

    echo -e "\n>>> Build image $coll\n"
    cd $coll
    docker build -t adamos/dwp-simulator:$coll .
#    docker save adamos/dwp-simulator:$coll > image.tar
#    zip dwp-sim-$coll.zip cumulocity.json image.tar
    cd ..
done

echo -e "\n\n>>> DONE\n"
