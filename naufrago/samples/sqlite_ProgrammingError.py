#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sqlite3

local_file = open('/home/jors/Desktop/test.html', 'r')
read = local_file.read()
local_file.close()

conn = sqlite3.connect('sqlite_ProgrammingError.db')
cursor = conn.cursor()
cursor.execute('CREATE TABLE articulo(id integer PRIMARY KEY, contenido text);')
cursor.execute('INSERT INTO articulo VALUES(null, ?)', [read.decode("utf-8")])
cursor.execute('SELECT * FROM articulo')
row = cursor.fetchall()
if (row is not None) and (len(row)>0):
 for item in row:
  print item
cursor.close()
