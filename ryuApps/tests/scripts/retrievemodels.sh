#!/bin/bash

echo "Getting model ietf-access-control-list"
sudo wget https://raw.githubusercontent.com/YangModels/yang/master/experimental/ietf-extracted-YANG-modules/ietf-access-control-list%402018-02-02.yang -P /home/laurence/Thesis/proto_mud/ryuApps/yang

echo "Getting model ietf-acldns"
sudo wget https://raw.githubusercontent.com/YangModels/yang/master/experimental/ietf-extracted-YANG-modules/ietf-acldns%402018-02-20.yang -P /home/laurence/Thesis/proto_mud/ryuApps/yang

echo "Getting model ietf-mud"
sudo wget https://raw.githubusercontent.com/YangModels/yang/master/experimental/ietf-extracted-YANG-modules/ietf-mud%402018-02-20.yang -P /home/laurence/Thesis/proto_mud/ryuApps/yang

echo "Getting ietf-yang-types"
sudo wget https://raw.githubusercontent.com/YangModels/yang/master/standard/ietf/RFC/ietf-yang-types%402013-07-15.yang -P /home/laurence/Thesis/proto_mud/ryuApps/yang

echo "Getting ietf-inet-types"
sudo wget https://raw.githubusercontent.com/YangModels/yang/master/standard/ietf/RFC/ietf-inet-types%402013-07-15.yang -P /home/laurence/Thesis/proto_mud/ryuApps/yang

echo "Getting ietf-packet-fields"
sudo wget https://raw.githubusercontent.com/YangModels/yang/master/experimental/ietf-extracted-YANG-modules/ietf-packet-fields%402018-02-02.yang -P /home/laurence/Thesis/proto_mud/ryuApps/yang

echo "Getting ietf-interfaces"
sudo wget https://raw.githubusercontent.com/YangModels/yang/master/experimental/ietf-extracted-YANG-modules/ietf-interfaces%402018-01-09.yang -P /home/laurence/Thesis/proto_mud/ryuApps/yang

echo "Getting ietf-ethertypes"
sudo wget https://raw.githubusercontent.com/YangModels/yang/master/experimental/ietf-extracted-YANG-modules/ietf-ethertypes%402018-02-02.yang

for file in /home/laurence/Thesis/proto_mud/ryuApps/yang/*.yang
do
	mv "$file" "${file%%\@*}.yang"
done
