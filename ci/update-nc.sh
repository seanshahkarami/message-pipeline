#!/bin/bash

cleanup() {
  waggle-switch-to-operation-mode
}

unlock() {
  if [ -z "$unlocked"]; then
    trap cleanup EXIT
    waggle-switch-to-safe-mode
    unlocked="unlocked"
  fi
}

cd /wagglerw/pywaggle
git fetch

if ! git status | grep up-to-date; then
  git pull
  pip3 install -U .
fi

cd /wagglerw/message-pipeline
git fetch

if ! git status | grep up-to-date; then
  git pull
  rsync -av /wagglerw/message-pipeline/systemd/node/ /etc/systemd/system
  rsync -av /wagglerw/message-pipeline/systemd/nc/ /etc/systemd/system
  systemd enable $(ls /wagglerw/message-pipeline/systemd/node) \
                 $(ls /wagglerw/message-pipeline/systemd/nc)
fi
