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
