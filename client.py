#!/usr/bin/env python3

import sys
import socket


def loop(s: socket.socket) -> None:
    while True:
        buf = []
        for line in sys.stdin:
            if line == 'Q\n':
                break
            if line == 'bye\n':
                return
            buf.append(line)
        else:
            raise Exception('EOF')

        recvlen = len(buf)
        buf = ['SEND'] + buf + ['RECV']
        s.sendall(''.join(buf).encode())

        while recvlen > 0:
            data = s.recv(1024)
            if not data:
                raise Exception('EOF')
            print(data.decode(), end='')
            recvlen -= data.count(b'\n')


def shutdown(s: socket.socket) -> None:
    s.sendall(b'Echo_CLOSE')

    buf = b''
    while b'Echo_CLOSE' not in buf:
        data = s.recv(1024)
        if not data:
            raise Exception('EOF')
        buf += data


def main() -> None:
    with socket.create_connection(('localhost', 8080)) as s:
        loop(s)
        shutdown(s)


if __name__ == "__main__":
    main()
