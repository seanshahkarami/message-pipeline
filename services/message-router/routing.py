import re
import subprocess
import sqlite3


class MockRoutingTable:

    def __init__(self, rules):
        self.rules = rules

    def is_message_routable(self, message):
        if self.rules is True:
            return True
        if self.rules is False:
            return False
        raise NotImplementedError('General rules not implemented yet.')

    def get_message_route(self, message):
        return 'to-node-{}'.format(message['receiver_id'].decode())


class SqliteRoutingTable:

    def __init__(self, filename):
        self.conn = sqlite3.connect(filename)

    def is_message_routable(self, message):
        return False

    def get_message_route(self, message):
        return 'to-node-{}'.format(message['receiver_id'].decode())


class NodeRoutingTable:

    def is_message_routable(self, message):
        return True

    def get_message_route(self, message):
        return 'to-device-{}'.format(message['receiver_sub_id'].decode())


# def get_node_id():
#     output = subprocess.check_output(['ip', 'link', 'show', 'eth0']).decode()
#     match = re.search(r'ether\s+(\S+)', output)
#     return match.group(1).replace(':', '')
