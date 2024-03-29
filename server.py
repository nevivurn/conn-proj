#!/usr/bin/env python3

import socket


def handle(s: socket.socket) -> None:
    buf = b''
    while True:
        while b'SEND' not in buf:
            data = s.recv(1024)
            if not data:
                raise Exception('EOF')
            buf += data
            if b'Echo_CLOSE' in buf:
                s.sendall(b'Echo_CLOSE')
                return
        buf = buf.partition(b'SEND')[2]

        while b'RECV' not in buf:
            data = s.recv(1024)
            if not data:
                raise Exception('EOF')
            buf += data
        data, _, buf = buf.partition(b'RECV')

        print(data.decode(), end='')
        s.sendall(data)


def loop(s: socket.socket) -> None:
    while True:
        client, _ = s.accept()
        with client:
            handle(client)


def main() -> None:
    with socket.create_server(('localhost', 8080), reuse_port=True) as s:
        loop(s)


if __name__ == '__main__':
    main()
