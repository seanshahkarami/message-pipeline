#!/bin/sh

rabbitmq-plugins enable rabbitmq_management rabbitmq_shovel rabbitmq_shovel_management

rabbitmqctl add_vhost beehive
rabbitmqctl add_vhost node

rabbitmqctl add_user guest guest
rabbitmqctl set_permissions -p beehive guest ".*" ".*" ".*"
rabbitmqctl set_permissions -p node guest ".*" ".*" ".*"

rabbitmqctl add_user node000000000001 testing
rabbitmqctl set_permissions -p beehive node000000000001 "^to-node-0000000000000001$" "^messages$" "^to-node-0000000000000001$"

rabbitmqctl set_parameter -p node shovel shovel-messages-to-beehive '{
"src-uri": "amqp://localhost/node",
"src-queue": "to-beehive",
"dest-uri": "amqp://localhost/beehive",
"dest-queue": "messages"
}'

rabbitmqctl set_parameter -p node shovel shovel-messages-from-beehive '{
"src-uri": "amqp://localhost/beehive",
"src-queue": "to-node-0000000000000001",
"dest-uri": "amqp://localhost/node",
"dest-queue": "messages"
}'

bin/pluginctl --vhost node enable plugins/*
