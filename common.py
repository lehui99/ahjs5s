import time
import threading
import logging
try:
    import gevent
    Concurrent = gevent.Greenlet
    socket = gevent.socket
    util = gevent
    import gevent.queue as queue
except ImportError:
    gevent = None
    Concurrent = threading.Thread
    import socket
    util = time
    try:
        import queue
    except ImportError:
        import Queue as queue

def eof_empty(b):
    if b:
        return b
    raise EOFError()

class Config(dict):
    def __init__(self, config):
        dict.__init__(self, config)
        if 'log_level' in self:
            self['log_level'] = getattr(logging, self['log_level'])
        else:
            self['log_level'] = logging.WARNING
        self['logger'] = logging.getLogger()
        self['logger'].setLevel(self['log_level'])
        if 'log_file' in self:
            log_handler = logging.FileHandler(self['log_file'])
        else:
            log_handler = logging.StreamHandler()
        if 'log_format' in self:
            log_handler.setFormatter(logging.Formatter(self['log_format']))
        self['logger'].addHandler(log_handler)

class BaseServerConfig(dict):
    def __init__(self, config):
        dict.__init__(self, config)
        if 'server_sockfamily' in self:
            self['server_sockfamily'] = getattr(socket, self['server_sockfamily'])
        else:
            self['server_sockfamily'] = socket.AF_INET
        if not 'server_addr' in self or not self['server_addr']:
            if self['server_sockfamily'] == socket.AF_INET:
                self['server_addr'] = '0.0.0.0'
            elif self['server_sockfamily'] == socket.AF_INET6:
                self['server_addr'] = '::'
        if not 'backlog' in self:
            self['backlog'] = 50

class ServerConfig(BaseServerConfig, Config):
    def __init__(self, config):
        Config.__init__(self, config)
        BaseServerConfig.__init__(self, config)

class Server(object):
    def __init__(self, config):
        self.config = config
    def start_peer(self, peer_sock, peer_info):
        raise NotImplementedError()
    def start(self):
        try:
            sock = socket.socket(self.config['server_sockfamily'])
            sock.bind((self.config['server_addr'], self.config['server_port']))
            sock.listen(self.config['backlog'])
        except Exception as e:
            self.config['logger'].error('Exception when starting: %s', str(e))
            return
        while True:
            try:
                self.start_peer(*sock.accept())
            except Exception as e:
                self.config['logger'].info('Exception when accept socks client: %s', str(e))
