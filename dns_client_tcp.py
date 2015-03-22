import random
import json
from common import *

class DnsClient(object):
    def __init__(self, config):
        self.config = config
        self.socks = []
    def req_result(self, sock, host, port):
        req = bytearray(json.dumps((host, port)).encode('iso-8859-1'))
        req_len = len(req)
        sock.sendall(bytearray((req_len >> 8, req_len & 0xff)))
        sock.sendall(req)
        resp_len = bytearray(eof_empty(sock.recv(1)))[0] << 8
        resp_len |= bytearray(eof_empty(sock.recv(1)))[0]
        resp = bytearray()
        while len(resp) != resp_len:
            resp.extend(eof_empty(sock.recv(resp_len - len(resp))))
        return json.loads(resp.decode('iso-8859-1'))
    def getaddrinfo(self, host, port):
        self.socks = [sock for sock in self.socks if sock != None]
        self.socks.sort(key = lambda x: random.randint(-1, 1))
        for sock in enumerate(self.socks):
            try:
                return self.req_result(sock[1], host, port)
            except Exception:
                self.socks[sock[0]] = None
        self.config['servers'].sort(key = lambda x: random.randint(-1, 1))
        for server in self.config['servers']:
            try:
                sock = socket.socket()
                sock.settimeout(self.config['timeout'])
                sock.connect(server)
                self.socks.append(sock)
                return self.req_result(sock, host, port)
            except Exception:
                pass

_dns_client = None

def init(config):
    global _dns_client
    _dns_client = DnsClient(config)

def getaddrinfo(host, port):
    return _dns_client.getaddrinfo(host, port)
