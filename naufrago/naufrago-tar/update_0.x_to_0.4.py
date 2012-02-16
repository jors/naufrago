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
  print 'Naufrago! 0.1 database found, changes correctly applied :)'
 except:
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
  print 'Naufrago! 0.2 database found, changes correctly applied :)'
 except:
  pass

def v03to04(cursor):
 try:
  cursor.execute('ALTER TABLE config ADD clear_mode integer NOT NULL DEFAULT 0')
  cursor.execute('ALTER TABLE config ADD deep_offline_mode integer NOT NULL DEFAULT 0')
  cursor.execute('ALTER TABLE config ADD http_proxy varchar(1024) NOT NULL DEFAULT \'\'')
  cursor.execute('ALTER TABLE config ADD use_proxy integer NOT NULL DEFAULT 0')
  cursor.execute('CREATE TABLE contenido_offline(id integer PRIMARY KEY, nombre varchar(256) NOT NULL, id_articulo integer NOT NULL);')
  conn.commit()
  print 'Naufrago! 0.3 database found, changes correctly applied :)'
 except:
  pass

app_path = os.getcwd()
db_path = app_path + '/naufrago.db'

if os.path.exists(db_path):
 try:
  conn = sqlite3.connect(db_path)
  cursor = conn.cursor()
  v01to02(cursor)
  v02to03(cursor)
  v03to04(cursor)
  conn.commit()
  cursor.close()
  print 'All done!'
 except:
  print 'Could not find database... Did you forget to move it to the current directory?'
