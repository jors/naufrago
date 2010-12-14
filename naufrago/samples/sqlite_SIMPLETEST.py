#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sqlite3

db_path = '/home/jors/.config/naufrago/naufrago.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute('SELECT id,titulo FROM articulo WHERE id_feed = 1 AND importante = 0 ORDER BY fecha ASC')
row = cursor.fetchall()
for id,titulo in row:
 print `id` + ', ' + titulo
cursor.close()
