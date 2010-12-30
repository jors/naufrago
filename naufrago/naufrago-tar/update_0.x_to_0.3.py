#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Script to update sqlite database from Naufrago! version 0.1 to 0.2.
import os
import sqlite3

def v01to02(cursor):
 try:
  cursor.execute('ALTER TABLE config ADD show_trayicon integer NOT NULL DEFAULT 0')
  cursor.execute('ALTER TABLE config ADD toolbar_mode integer NOT NULL DEFAULT 0')
  cursor.execute('ALTER TABLE config ADD show_newentries_notification integer NOT NULL DEFAULT 1')
  cursor.execute('ALTER TABLE config ADD hide_readentries integer NOT NULL DEFAULT 0')
  cursor.execute('UPDATE categoria SET nombre = \'General\' WHERE id = 1')
  conn.commit()
  print 'Naufrago! 0.1 database format found, changes correctly applied :)'
 except:
    print 'Naufrago! 0.1 database format not found, skipping...'
    pass

def v02to03(cursor):
 try:
  cursor.execute('ALTER TABLE config ADD hide_dates integer NOT NULL DEFAULT 0')
  cursor.execute('ALTER TABLE config ADD driven_mode integer NOT NULL DEFAULT 1')
  cursor.execute('ALTER TABLE config ADD update_freq_timemode integer NOT NULL DEFAULT 0')
  cursor.execute('ALTER TABLE config ADD init_check_app_updates integer NOT NULL DEFAULT 1')
  cursor.execute('ALTER TABLE articulo ADD ghost integer NOT NULL DEFAULT 0')
  cursor.execute('UPDATE config SET init_unfolded_tree = 0')
  conn.commit()
  print 'Naufrago! 0.2 database format found, changes correctly applied :)'
 except:
  print 'Naufrago! 0.2 database format not found, skipping...'
  pass

app_path = os.getcwd()
db_path = app_path + '/naufrago.db'

if os.path.exists(db_path):
 try:
  conn = sqlite3.connect(db_path)
  cursor = conn.cursor()
  v01to02(cursor)
  v02to03(cursor)
  conn.commit()
  cursor.close()
  print 'All done!'
 except:
  print 'Could not find database... Did you forget to move it to the current directory?'
