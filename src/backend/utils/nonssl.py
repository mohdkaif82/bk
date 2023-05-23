import ssl
import urllib2
import socket
from httplib import HTTPSConnection


class HTTPSConnectionNonECDH(HTTPSConnection):
    """This class allows communication via SSL."""

    default_port = 443

    def connect(self):
        """Connect to a host on a given (SSL) port."""

        sock = socket.create_connection((self.host, self.port),
                                        self.timeout, self.source_address)
        if self._tunnel_host:
            self.sock = sock
            self._tunnel()
        self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file, ssl_version=ssl.PROTOCOL_SSLv23, ciphers='DEFAULT:!ECDH')


class HTTPSHandlerNonECDH(urllib2.HTTPSHandler):
    def https_open(self, req):
        return self.do_open(HTTPSConnectionNonECDH, req)


def urlopen_nonECDH(*args, **kwargs):
    # install opener
    urllib2.install_opener(urllib2.build_opener(HTTPSHandlerNonECDH()))
    return urllib2.urlopen(*args, **kwargs)
