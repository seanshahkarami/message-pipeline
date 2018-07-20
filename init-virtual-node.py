#!/usr/bin/env python3
import argparse
import os
import json
import re
import subprocess


def read_certificate_text(path):
    return subprocess.check_output([
        'openssl',
        'x509',
        '-in', certfile,
        '-text'
    ]).decode()


def get_node_id_from_cert(path):
    return re.search(r'CN=node([0-9a-fA-F]+)', read_certificate_text(path)).group(1)


parser = argparse.ArgumentParser()
parser.add_argument('beehive_host')
parser.add_argument('ssl_dir')
args = parser.parse_args()

ssl_dir = os.path.abspath(args.ssl_dir)

cacertfile = os.path.join(ssl_dir, 'cacert.pem')
certfile = os.path.join(ssl_dir, 'cert.pem')
keyfile = os.path.join(ssl_dir, 'key.pem')

node_id = get_node_id_from_cert(certfile)
receiver_id = node_id.rjust(16, '0')

# should design so can be used within vhosts...
# then, i can actually test this on my machine.

beehive_url = 'amqps://{}:23181?auth_mechanism=external&cacertfile={}&certfile={}&keyfile={}&verify=verify_peer'.format(
    args.beehive_host,
    cacertfile,
    certfile,
    keyfile)

subprocess.check_output([
    'rabbitmq-plugins',
    'enable',
    'rabbitmq_management',
    'rabbitmq_shovel',
    'rabbitmq_shovel_management',
])

shovel_config = json.dumps({
    "src-uri": "amqp://localhost",
    "src-queue": "to-beehive",
    "dest-uri": beehive_url,
    "dest-exchange": "messages",
})

subprocess.check_output([
    'rabbitmqctl',
    'set_parameter',
    'shovel',
    'shovel-messages-to-beehive',
    shovel_config])

shovel_config = json.dumps({
    "src-uri": beehive_url,
    "src-queue": "to-node-{}".format(receiver_id),
    "dest-uri": "amqp://localhost",
    "dest-queue": "messages",
})

subprocess.check_output([
    'rabbitmqctl',
    'set_parameter',
    'shovel',
    'shovel-messages-from-beehive',
    shovel_config])
