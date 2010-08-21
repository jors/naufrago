#!/usr/bin/env python

import os
import sqlite3

db_path = os.getenv("HOME") + '/.naufrago/naufrago2.db'
feed_ids = '1,2,3'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
q = 'DELETE FROM articulo WHERE id_feed IN (' + feed_ids+ ')'
cursor.execute(q)
conn.commit()
cursor.close()
