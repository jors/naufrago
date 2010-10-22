#!/usr/bin/env python
# -*- coding: utf-8 -*-
import socket
import sys

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("www.google.es", 80))
s.send("GET / HTTP/1.0\r\n\r\n")
while 1:
 buf = s.recv(1024)
 if not buf:
  break
 sys.stdout.write(buf)
s.close()
