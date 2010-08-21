#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Script to update sqlite database from Naufrago! version 0.1 to 0.2.
import os
import sqlite3

if os.path.exists(os.getenv("HOME")+ '/.naufrago/'):
 os.rename(os.getenv("HOME")+ '/.naufrago', os.getenv("HOME") + '/.config/naufrago')

conn = sqlite3.connect(os.getenv("HOME") + '/.config/naufrago/naufrago.db')
cursor = conn.cursor()
cursor.execute('ALTER TABLE config ADD show_trayicon integer NOT NULL DEFAULT 0')
cursor.execute('ALTER TABLE config ADD toolbar_mode integer NOT NULL DEFAULT 0')
cursor.execute('ALTER TABLE config ADD show_newentries_notification integer NOT NULL DEFAULT 1')
cursor.execute('ALTER TABLE config ADD hide_readentries integer NOT NULL DEFAULT 0')
cursor.execute('UPDATE categoria SET nombre = \'General\' WHERE id = 1')
conn.commit()
cursor.close()
