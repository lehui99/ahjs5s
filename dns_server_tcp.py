import sys
import json
from common import *

class DnsPeer(Concurrent):
    def __init__(self, config, sock):
        Concurrent.__init__(self)
        self.config = config
        self.sock = sock
    def _run(self):
        try:
            while True:
                req_len = bytearray(eof_empty(self.sock.recv(1)))[0] << 8
                req_len |= bytearray(eof_empty(self.sock.recv(1)))[0]
                req = bytearray()
                while len(req) != req_len:
                    req.extend(eof_empty(self.sock.recv(req_len - len(req))))
                req = json.loads(req.decode('iso-8859-1'))
                resp = json.dumps(socket.getaddrinfo(req[0], req[1]))
                resp_len = len(resp)
                self.sock.sendall(bytearray((resp_len >> 8, resp_len & 0xff)))
                self.sock.sendall(resp.encode('iso-8859-1'))
        except Exception as e:
            self.config['logger'].debug('DnsPeer end with: %s', str(e))
    def run(self):
        return self._run()

class DnsServer(Server):
    def __init__(self, config):
        Server.__init__(self, config)
    def start_peer(self, peer_sock, peer_info):
        peer_sock.settimeout(self.config['timeout'])
        DnsPeer(self.config, peer_sock).start()

def main(config_filename):
    with open(config_filename) as config_file:
        config = json.loads(config_file.read())
    if not 'timeout' in config:
        config['timeout'] = 2
    DnsServer(ServerConfig(config)).start()

if __name__ == '__main__':
    main(sys.argv[1])
