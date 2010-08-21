#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Script to update sqlite database from Naufrago! version 0.1 to 0.2.
import sqlite3

db_path = '/put/here/your/path/to/file/naufrago.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute('ALTER TABLE config ADD show_trayicon integer NOT NULL DEFAULT 0')
cursor.execute('ALTER TABLE config ADD toolbar_mode integer NOT NULL DEFAULT 0')
cursor.execute('ALTER TABLE config ADD show_newentries_notification integer NOT NULL DEFAULT 1')
cursor.execute('ALTER TABLE config ADD hide_readentries integer NOT NULL DEFAULT 0')
cursor.execute('UPDATE categoria SET nombre = \'General\' WHERE id = 1')
conn.commit()
cursor.close()
