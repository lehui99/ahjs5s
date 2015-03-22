import sys
import json
from common import *

class SocksPipe(object):
    def __call__(self, config, first_packet_processor, sock_in, sock_out):
        sock_in_fileno = sock_in.fileno()
        sock_out_fileno = sock_out.fileno()
        config['logger'].debug('Start piping socket %d => socket %d'
                                    , sock_in_fileno, sock_out_fileno)
        try:
            first_packet_processor()
            while True:
                buf = sock_in.recv(config['recv_packet_size'])
                if not buf:
                    return
                config['logger'].debug('Received %d bytes from socket %d', len(buf), sock_in_fileno)
                sock_out.sendall(buf)
        except Exception as e:
            config['logger'].debug('Pipe(%d => %d) end with: %s', sock_in_fileno, sock_out_fileno, str(e))
        finally:
            config['logger'].debug('Closing socket pair %d and %d...'
                                        , sock_in_fileno, sock_out_fileno)
            sock_in.close()
            sock_out.close()

class SocksPeer(object):
    def __call__(self, config, sock_peer):
        sock_peer_fileno = sock_peer.fileno()
        sock_remote = None
        sock_remote_fileno = -1
        try:
            eof_empty(sock_peer.recv(1))  # VER
            nmethods = bytearray(eof_empty(sock_peer.recv(1)))[0]  # NMETHODS
            for i in iter(range(nmethods)):  # METHODS
                eof_empty(sock_peer.recv(1))
            sock_peer.sendall(b'\x05\x00')  # VER+METHOD
            eof_empty(sock_peer.recv(1))  # VER
            cmd = bytearray(eof_empty(sock_peer.recv(1)))[0]  # CMD
            if cmd != 1:  # not a CONNECT CMD
                config['logger'].warning('Not a CONNECT CMD')
                return
            eof_empty(sock_peer.recv(1))  # RSV
            atyp = bytearray(eof_empty(sock_peer.recv(1)))[0]  # ATYP
            dst_addrs = bytearray()
            if atyp == 1:  # IP V4 address
                for i in iter(range(4)):
                    dst_addrs.append(bytearray(eof_empty(sock_peer.recv(1)))[0])
                dst_addrs = [(socket.AF_INET, 0, 0, '', ('%d.%d.%d.%d' % tuple(dst_addrs), 0))]
            elif atyp == 3:  # DOMAINNAME
                addr_len = bytearray(eof_empty(sock_peer.recv(1)))[0]
                while len(dst_addrs) != addr_len:
                    dst_addrs.extend(bytearray(eof_empty(sock_peer.recv(addr_len - len(dst_addrs)))))
                dst_hostname = dst_addrs.decode('iso-8859-1')
                dst_addrs = config['dns_client'].getaddrinfo(dst_hostname, 0)
                config['logger'].debug('Resolved hostname %s: %s', dst_hostname, str(dst_addrs))
            elif atyp == 4:  # IP V6 address
                for i in iter(range(16)):
                    dst_addrs.append(bytearray(eof_empty(sock_peer.recv(1)))[0])
                dst_addrs = [(socket.AF_INET6, 0, 0, '', (':'.join(['%02x%02x'] * 8) % tuple(dst_addrs), 0))]
            else:  # unknown ATYP
                config['logger'].error('Unknown ATYP %d', atyp)
                return
            dst_port = bytearray(eof_empty(sock_peer.recv(1)))[0] << 8
            dst_port |= bytearray(eof_empty(sock_peer.recv(1)))[0]
            for dst_addr in dst_addrs:
                try:
                    sock_remote = socket.socket(dst_addr[0])
                    sock_remote.bind((config['bind_addr'][dst_addr[0]], 0))
                    sock_remote.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, config['recv_sep_size'])
                    # Maybe no use if already set SO_RCVBUF for the packets after the first package.
                    # Because SO_RCVBUF will set the window size on both client and server when
                    # connecting(the behavior is different between Windows and Linux), and TCP/IP stack
                    # won't process the data in the send buf if window is full.  Then the whole data in
                    # the send buf will be sent though one packet after remaining window size is
                    # increased by ACK:
                    sock_remote.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    # The  minimum  (doubled) value for this option is 2048 on Linux:
                    # So no use for this operation on Linux:
                    sock_remote.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, config['send_sep_size'])
                    config['logger'].debug('Connecting to %s:%d for socket pair(sock_peer, sock_remote):(%d, %d)...', dst_addr[4][0], dst_port, sock_peer.fileno(), sock_remote.fileno())
                    sock_remote.connect((dst_addr[4][0], dst_port))
                    sock_remote_fileno = sock_remote.fileno()
                    break
                except Exception as e:
                    config['logger'].debug('Error while connecting %s:%d for socks client %d: %s'
                                                , dst_addr[4][0], dst_port, sock_peer.fileno(), str(e))
                    sock_remote.close()
                    sock_remote = None
            if not sock_remote:
                return
            sock_peer.sendall(b'\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00')
            def pipe_cs_first_packet():  # self.sock => sock
                buf = sock_peer.recv(config['recv_packet_size'])
                if not buf:
                    raise EOFError()
                idx = 0
                while idx < len(buf):
                    sock_remote.sendall(buf[idx : idx + config['send_packet_size']])
                    idx += config['send_packet_size']
                sock_remote.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, config['recv_sep_size'])
                sock_remote.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, config['tcp_nodelay'])
                # The  minimum  (doubled) value for this option is 2048 on Linux:
                # So no use for this operation on Linux:
                sock_remote.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, config['so_sndbuf'])
            def pipe_sc_first_packet():  # sock => self.sock
                buf = sock_remote.recv(config['recv_packet_size'])
                if not buf:
                    raise EOFError()
                sock_peer.sendall(buf)
                sock_remote.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, config['so_rcvbuf'])
            Concurrent(target=SocksPipe(), args=(config, pipe_cs_first_packet, sock_peer, sock_remote)).start()
            SocksPipe()(config, pipe_sc_first_packet, sock_remote, sock_peer)
        except EOFError:
            config['logger'].debug('EOFError')
        except Exception as e:
            logging.info('Exception when process socks protocol: %s', str(e))
        finally:
            config['logger'].debug('Closing socket %d and %d...', sock_peer_fileno, sock_remote_fileno)
            sock_peer.close()
            if sock_remote:
                sock_remote.close()

class SocksServer(Server):
    def __init__(self, config):
        Server.__init__(self, config)
    def start(self):
        if not gevent:
            self.config['logger'].info('Cannot find gevent, using threading')
        Server.start(self)
    def start_peer(self, peer_sock, peer_info):
        Concurrent(target=SocksPeer(), args=(self.config, peer_sock)).start()

class SocksServerConfig(ServerConfig):
    def __init__(self, config):
        ServerConfig.__init__(self, config)
        tmp_sock = socket.socket()
        if not 'tcp_nodelay' in self:
            self['tcp_nodelay'] = tmp_sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY)
        if not 'so_sndbuf' in self:
            self['so_sndbuf'] = tmp_sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
        if not 'so_rcvbuf' in self:
            self['so_rcvbuf'] = tmp_sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
        tmp_sock.close()
        if not 'send_sep_size' in self:
            self['send_sep_size'] = self['so_sndbuf']
        if not 'send_packet_size' in self:
            self['send_packet_size'] = 1
        if not 'recv_sep_size' in self:
            self['recv_sep_size'] = self['so_rcvbuf']
        if not 'recv_packet_size' in self:
            self['recv_packet_size'] = 65536
        bind_addr = dict()
        if 'bind_addr' in self:
            for family_type in self['bind_addr']:
                bind_addr[getattr(socket, family_type)] = self['bind_addr'][family_type]
        if not socket.AF_INET in bind_addr:
            bind_addr[socket.AF_INET] = '0.0.0.0'
        if not socket.AF_INET6 in bind_addr:
            bind_addr[socket.AF_INET6] = '::'
        self['bind_addr'] = bind_addr
        if 'dns_client' in self:
            dns_client = __import__(self['dns_client']['name'])
            dns_client.init(self['dns_client']['config'])
            if not 'timeout' in self['dns_client']['config']:
                self['dns_client']['config']['timeout'] = 2
            for i, dns_server_addr in enumerate(self['dns_client']['config']['servers']):
                self['dns_client']['config']['servers'][i] = tuple(dns_server_addr)
            self['dns_client'] = dns_client
        else:
            class dns_client:
                pass
            dns_client = dns_client()
            dns_client.getaddrinfo = socket.getaddrinfo
            self['dns_client'] = dns_client
        self['logger'].debug('Config is "%s"', str(self))

def main(config_filename):
    with open(config_filename) as config_file:
        config = json.loads(config_file.read())
    SocksServer(SocksServerConfig(config)).start()

if __name__ == '__main__':
    main(sys.argv[1])
