#!/bin/bash

cleanup() {
  waggle-switch-to-operation-mode
}

waggle-switch-to-safe-mode
trap cleanup EXIT

cd /wagglerw/pywaggle
git pull
pip3 install -U .

cd /wagglerw/message-pipeline
git pull
rsync -av /wagglerw/message-pipeline/systemd/node/ /etc/systemd/system
rsync -av /wagglerw/message-pipeline/systemd/ep/ /etc/systemd/system
systemctl enable \
  $(ls /wagglerw/message-pipeline/systemd/node) \
  $(ls /wagglerw/message-pipeline/systemd/ep)

cd /wagglerw/message-pipeline
bin/plugin-manager start \
  plugins/simple.plugin \
  plugins/sysmon.plugin \
  plugins/spl.plugin \
  plugins/image-detector.plugin
