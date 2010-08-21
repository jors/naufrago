#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sqlite3

db_path = os.getenv("HOME") + '/.naufrago/naufrago.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute('SELECT id,nombre FROM feed')
res = cursor.fetchall()
for row in res:
 print str(row[0]) + ', ' + str(row[1])
cursor.close()
