#!/usr/bin/env python
# -*- coding: utf-8 -*-

#############################################################################
#                                                                           #
# Naufrago! RSS Reader                                                      #
#                                                                           #
# Copyright (C) 2010 Jordi Oliveras Palacios ( worbynet at gmail dot com )  #
#                                                                           #
# This program is free software; you can redistribute it and/or modify      #
# it under the terms of the GNU General Public License as published by      #
# the Free Software Foundation; either version 3 of the License, or         #
# (at your option) any later version.                                       #
#                                                                           #
# This program is distributed in the hope that it will be useful,           #
# but WITHOUT ANY WARRANTY; without even the implied warranty of            #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             #
# GNU General Public License for more details.                              #
#                                                                           #
# You should have received a copy of the GNU General Public License         #
# along with this program; if not, write to the Free Software               #
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA #
#                                                                           #
#############################################################################

try:
 import sys
 import pygtk
 pygtk.require('2.0')
 import gtk
 import gobject
 gobject.threads_init()
 import os
 import sqlite3
 import feedparser
 import time
 import datetime
 import webkit
 import threading
 import webbrowser
 import pango
 import urllib2
 import re
 from xml.etree import ElementTree
 from xml.sax import saxutils
 import htmlentitydefs
 import hashlib
 import locale
 import gettext
 import socket
 import pynotify
except ImportError:
 print _('Error importing modules: ') + `sys.exc_info()[1]`
 sys.exit(1)

APP_VERSION = '0.3'
ABOUT_PAGE = ''
PUF_PAGE = ''
distro_package = True
window_visible = True

# Global socket timeout stuff
if hasattr(socket, 'setdefaulttimeout'):
 socket.setdefaulttimeout(5)

# Locale stuff
APP = 'naufrago'
if distro_package: DIR = '/usr/share/naufrago/locale'
else: DIR = os.getcwd() + '/locale'

try:
 locale.setlocale(locale.LC_ALL, '')
 locale = locale.getdefaultlocale()[0]
 gettext.bindtextdomain(APP, DIR)
 gettext.textdomain(APP)
 _ = gettext.gettext
except:
 locale = ['en']
 _ = gettext.gettext

if distro_package: # We're running on 'Distro-mode' (intended for distribution packages)
 app_path = '/usr/share/naufrago/'
 media_path = app_path + 'media/'
 db_path = os.getenv("HOME") + '/.config/naufrago/naufrago.db'
 favicon_path = os.getenv("HOME") + '/.config/naufrago/favicons'
 images_path = os.getenv("HOME") + '/.config/naufrago/imagenes'
 if "es" in locale:
  index_path = app_path + 'content/index_es.html'
  puf_path = app_path + 'content/puf_es.html'
 elif "ca" in locale:
  index_path = app_path + 'content/index_ca.html'
  puf_path = app_path + 'content/puf_ca.html'
 elif "pl" in locale:
  index_path = app_path + 'content/index_pl.html'
  puf_path = app_path + 'content/puf.html'
 elif "it" in locale:
  index_path = app_path + 'content/index_it.html'
  puf_path = app_path + 'content/puf.html'
 elif "fr" in locale:
  index_path = app_path + 'content/index_fr.html'
  puf_path = app_path + 'content/puf_fr.html'
 else:
  index_path = app_path + 'content/index.html'
  puf_path = app_path + 'content/puf.html'
else: # We're running on 'tarball-mode' (unpacked from tarball)
 current_path = os.getcwd()
 app_path = current_path + '/'
 media_path = current_path + '/media/'
 db_path = current_path + '/naufrago.db'
 favicon_path = current_path + '/favicons'
 images_path = current_path + '/imagenes'
 if "es" in locale:
  index_path = current_path + '/content/index_es.html'
  puf_path = current_path + '/content/puf_es.html'
 elif "ca" in locale:
  index_path = current_path + '/content/index_ca.html'
  puf_path = current_path + '/content/puf_ca.html'
 elif "pl" in locale:
  index_path = current_path + '/content/index_pl.html'
  puf_path = current_path + '/content/puf.html'
 elif "it" in locale:
  index_path = current_path + '/content/index_it.html'
  puf_path = current_path + '/content/puf.html'
 elif "fr" in locale:
  index_path = current_path + '/content/index_fr.html'
  puf_path = current_path + '/content/puf_fr.html'
 else:
  index_path = current_path + '/content/index.html'
  puf_path = current_path + '/content/puf.html'

class Naufrago:

 def delete_event(self, event=None, data=None):
  """Closes the app through window manager signal"""
  # Si estamos en un proceso de update, no salir de la app hasta alcanzar un estado estable.
  if self.on_a_feed_update:
   self.stop_feed_update()
   self.t.join()
  # Finalmente, salida efectiva
  self.save_config()
  gtk.main_quit()
  return False

 def tree_key_press_event(self, widget, event):
  """Tells which keyboard button was pressed"""
  key = gtk.gdk.keyval_name(event.keyval)
  if(key == 'Delete'): # ARBOL DE FEEDS
   (model, iter) = self.treeselection.get_selected()
   if(iter is not None): # Si hay algún nodo seleccionado...
    if(model.iter_depth(iter) == 0): # Si es un nodo padre...
     self.delete_category()
    elif(model.iter_depth(iter) == 1): # Si es un nodo hijo...
     self.delete_feed()
  elif(key == 'Return'): # LISTA DE ENTRIES
   self.abrir_browser()

 def make_pb(self, tvcolumn, cell, model, iter):
  """Renders the parameter received icons"""
  stock = model.get_value(iter, 1)
  pb = self.treeview.render_icon(stock, gtk.ICON_SIZE_MENU, None)
  cell.set_property('pixbuf', pb)
  return

 def toggle_importante(self, cell, path, model):
  """Sets the toggled state on the toggle button to true or false"""

  # Si el marcado/desmarcado del importante está sin leer, cabe actualizar su nodo.
  if self.clear_mode == 0:
   (model2, iter) = self.treeselection.get_selected()
   dest_iter = self.treeindex[9998]
   nombre_feed_destino = model2.get_value(dest_iter, 0)
   (nombre_feed_destino, no_leidos) = self.less_simple_name_parsing(nombre_feed_destino)
   feed_label = nombre_feed_destino
   font_style = 'bold'

  model[path][1] = not model[path][1]
  if model[path][1]:
   self.eb.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("pink")) # Entry title bg glow
   if self.clear_mode == 0: # NEW
    if model[path][3] == 'bold':
     if no_leidos is not None:
      no_leidos = int(no_leidos) + 1
      feed_label = nombre_feed_destino + ' [' + `no_leidos` + ']'
     else:
      feed_label = nombre_feed_destino + ' [1]'
     model2.set(dest_iter, 0, feed_label, 3, font_style)
  else:
   self.eb.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#EDECEB")) # Entry title bg normalize
   if self.clear_mode == 0: # NEW
    if model[path][3] == 'bold':
     if no_leidos is not None:
      no_leidos = int(no_leidos) - 1
      if no_leidos == 0:
       feed_label = nombre_feed_destino
       font_style = 'normal'
      else:
       feed_label = nombre_feed_destino + ' [' + `no_leidos` + ']'
     else:
      feed_label = nombre_feed_destino
      font_style = 'normal'
     model2.set(dest_iter, 0, feed_label, 3, font_style)

  cursor = self.conn.cursor()
  self.lock.acquire()
  cursor.execute('UPDATE articulo SET importante = ? WHERE id = ?', [model[path][1],model[path][4]])
  self.conn.commit()
  self.lock.release()
  cursor.close()
  return

 def simple_name_parsing(self, nombre_feed):
  """Parses & returns the proper name of the feed on the tree."""
  rgxp = r''' \[.*\]$'''
  m = re.search(rgxp, nombre_feed)
  if m is not None:
   nombre_feed = nombre_feed.split(' ')
   nombre_feed = ' '.join(nombre_feed[0:len(nombre_feed)-1])
  return nombre_feed

 def less_simple_name_parsing(self, nombre_feed):
  """Parses & returns a tuple with the proper name of the feed and unread items, if any."""
  rgxp = r''' \[.*\]$'''
  m = re.search(rgxp, nombre_feed)
  if m is not None:
   nombre_feed = nombre_feed.split(' ')
   no_leidos = nombre_feed[len(nombre_feed)-1]
   if ('[' in no_leidos) and (']' in no_leidos):
    no_leidos = no_leidos.replace('[','').replace(']','').strip()
   else:
    no_leidos = None
   nombre_feed = ' '.join(nombre_feed[0:len(nombre_feed)-1])
  else:
   no_leidos = None
  return nombre_feed, no_leidos

 def toggle_category_bold_all(self):
  """Toggles bold or unbold in ALL category folders."""
  (model, useless_iter) = self.treeselection.get_selected() # We only want the model here...
  iter = model.get_iter_root() # Magic
  while (iter is not None):
   if(model.iter_depth(iter) == 0): # Si es padre
    id_cat = model.get_value(iter, 2)
    if (id_cat != 9998) and (id_cat != 9999):
     self.toggle_category_bold(id_cat, True)
   iter = self.treestore.iter_next(iter) # Pasamos al siguiente Padre..

 def toggle_category_bold(self, id_cat=None, special_folder=False):
  """Toggles bold or unbold in category folders."""
  id_cat_aux = id_cat
  if id_cat == 'all':
   (model, useless_iter) = self.treeselection.get_selected() # We only want the model here...
   iter = model.get_iter_root() # Magic
   while (iter is not None):
    if(model.iter_depth(iter) == 0): # Si es padre
     model.set(iter, 3, 'normal')
    iter = self.treestore.iter_next(iter) # Pasamos al siguiente Padre..
   return

  elif (special_folder is True) and (id_cat != '9998') and (id_cat != '9999'):
   (model, useless_iter) = self.treeselection.get_selected() # We only want the model here...
   iter = self.treeindex_cat[id_cat]
   id_cat_aux = None

  elif id_cat is None:
   (model, iter) = self.treeselection.get_selected()
   if(model.iter_depth(iter) == 1): # Si es hijo...
    iter = model.iter_parent(iter) # ...queremos el padre
   id_cat = model.get_value(iter, 2)

  cursor = self.conn.cursor()
  q = 'SELECT count(articulo.id) FROM articulo, feed, categoria WHERE articulo.leido=0 AND articulo.ghost=0 AND categoria.id='+`id_cat`+' AND articulo.id_feed=feed.id AND feed.id_categoria=categoria.id'
  self.lock.acquire()
  cursor.execute(q)
  row = cursor.fetchone()
  self.lock.release()
  cursor.close()
  if row[0] == 0:
   if id_cat_aux is None:
    model.set(iter, 3, 'normal')
   return 'normal' # Sometimes we don't need return values, but.. life goes on
  else:
   if id_cat_aux is None:
    model.set(iter, 3, 'bold')
   return 'bold' # Sometimes we don't need return values, but.. life goes on

 def mark_all_as_read(self, data=None):
  """Marks all feed items as read."""
  response = self.yes_no_message(_('¿Seguro que quieres <b>marcarlo TODO como leído</b>?'))
  if response == gtk.RESPONSE_ACCEPT:
   (model, useless_iter) = self.treeselection.get_selected() # We only want the model here...
   iter = self.treestore.get_iter_root() # Magic
   while iter is not None:
    if self.clear_mode == 0:
     id_cat = model.get_value(iter, 2)
     font_style = model.get_value(iter, 3)
     if (id_cat is not 9998 or id_cat is not 9999) and font_style == 'bold':
      model.set(iter, 3, 'normal') # CATEGORIA
      iter2 = model.iter_children(iter)
      while iter2:
       label = model.get_value(iter2, 0)
       if '[' in label and ']' in label:
        label = self.simple_name_parsing(label)
        model.set(iter2, 0, label, 3, 'normal') # FEED
       iter2 = self.treestore.iter_next(iter2)
     # Fold category (if applies).
     if (self.driven_mode == 1):
      self.treeview.collapse_row(model.get_path(iter))
    else:
     self.treestore.clear()
     break
    iter = self.treestore.iter_next(iter)

   cursor = self.conn.cursor()
   self.lock.acquire()
   cursor.execute('UPDATE articulo SET leido = 1')
   self.conn.commit()
   self.lock.release()
   cursor.close()

   if self.clear_mode == 0:
    # Must update special folders...
    self.update_special_folder(9999)
    self.update_special_folder(9998)

 def toggle_leido(self, event, data=None):
  """Toggle entries between read/non-read states."""
  cursor = self.conn.cursor()
  
  if(data == 'tree'): # La petición de toggle proviene del ARBOL DE FEEDS
   (model, iter) = self.treeselection.get_selected()

   if(iter is not None): # Hay algún nodo seleccionado
    id_feed = self.treestore.get_value(iter, 2)

    # OLD: if(model.iter_depth(iter) == 1) or (id_feed == 9998) or (id_feed == 9999): # Si es HOJA...
    # Si es HOJA...
    if(model.iter_depth(iter) == 1) or (id_feed == 9998) or (id_feed == 9999) or (model.iter_depth(iter) == 0 and self.clear_mode == 1):

     # NEW
     if self.clear_mode == 1 and self.treeindex.has_key(id_feed):
      self.treestore.remove(iter)
      del self.treeindex[id_feed] # Update feeds dict
     else:
     # NEW
      # 1º vamos a por el label del feed...
      # START NAME PARSING (nodo origen) #
      nombre_feed = model.get_value(iter, 0)
      nombre_feed = self.simple_name_parsing(nombre_feed)
      model.set(iter, 0, nombre_feed, 3, 'normal')
      # END NAME PARSING (nodo origen) #

     # 2º vamos a por las entries del feed...
     (model2, iter2) = self.treeselection2.get_selected()
     iter2 = model2.get_iter_root() # Magic
     count = 0
     entry_ids = ''
     while iter2:
      self.liststore.set_value(iter2, 3, 'normal')
      id_articulo = self.liststore.get_value(iter2, 4)
      entry_ids += `id_articulo` + ','
      iter2 = self.liststore.iter_next(iter2)
     entry_ids = entry_ids[0:-1]

     # ...y 3º a por los datos
     q = 'UPDATE articulo SET leido = 1 WHERE id IN (' + entry_ids + ')'
     self.lock.acquire()
     cursor.execute(q)
     self.conn.commit()
     self.lock.release()

     if self.clear_mode == 0: # NEW
      # START NAME PARSING (nodo destino) #
      if nombre_feed == _("Unread"):
       #print 'Destino: feed normal'
       q = 'SELECT DISTINCT id_feed FROM articulo WHERE id IN (' + entry_ids + ')'
       self.lock.acquire()
       cursor.execute(q)
       row = cursor.fetchall()
       self.lock.release()
       if (row is not None) and (len(row)>0):
        for feed in row:
         dest_iter = self.treeindex[feed[0]]
         nombre_feed_destino = model.get_value(dest_iter, 0)
         nombre_feed_destino = self.simple_name_parsing(nombre_feed_destino)
         feed_label = nombre_feed_destino
         font_style = 'normal'
         model.set(dest_iter, 0, feed_label, 3, font_style)
        ### START: ¡También cabe actualizar su compañero de batallas!
        self.update_special_folder(9998) # Actualizamos Important
        ### END: ¡También cabe actualizar su compañero de batallas!
        # Bold/unbold de TODAS las categorias
        self.toggle_category_bold('all')
        # Y si aplica, fold de TODAS las categorias
        if (self.driven_mode == 1):
         self.treeview.collapse_all() # Fold de todo!

      elif nombre_feed == _("Important"):
       #print 'Destino: feed normal'
       q = 'SELECT DISTINCT id_feed FROM articulo WHERE id IN (' + entry_ids + ')'
       self.lock.acquire()
       cursor.execute(q)
       row = cursor.fetchall()
       self.lock.release()
       if (row is not None) and (len(row)>0):
        for feed in row:
         dest_iter = self.treeindex[feed[0]]
         nombre_feed_destino = model.get_value(dest_iter, 0)
         nombre_feed_destino = self.simple_name_parsing(nombre_feed_destino)
         q = 'SELECT count(id) FROM articulo WHERE id_feed = ' + `feed[0]` + ' AND leido = 0 AND ghost = 0'
         self.lock.acquire()
         cursor.execute(q)
         count = cursor.fetchone()[0]
         self.lock.release()
         if count is not None:
          if count > 0:
           feed_label = nombre_feed_destino + ' [' + `count` + ']'
           font_style = 'bold'
          else:
           feed_label = nombre_feed_destino
           font_style = 'normal'
         else:
          feed_label = nombre_feed_destino
          font_style = 'normal'
         model.set(dest_iter, 0, feed_label, 3, font_style)
        ### START: ¡También cabe actualizar su compañero de batallas!
        self.update_special_folder(9999) # Actualizamos Unread
        ### END: ¡También cabe actualizar su compañero de batallas!
        # Bold/unbold de ALGUNAS categorias
        self.toggle_category_bold_all()
        # Y si aplica, fold de ALGUNAS categorias (las que no tengan feeds con entries por leer)
        if (self.driven_mode == 1):
         self.driven_mode_action() # Fold de lo que esté 'vacio'

      else:
       # Bold/unbold de la categoria
       self.toggle_category_bold()
       # Y si aplica, fold de la categoria
       if (self.driven_mode == 1):
        self.driven_mode_action()
       # Destino: No leídos
       self.update_special_folder(9999)
       # Destino: Importantes
       self.update_special_folder(9998)
      # END NAME PARSING (nodo destino) #

     # Limpieza de la GUI
     if self.hide_readentries:
      self.liststore.clear() # Limpieza de tabla de entries/articulos
      self.scrolled_window2.set_size_request(0,0)
      self.scrolled_window2.hide()
      (model_tmp, iter_tmp) = self.treeselection.get_selected()
      if type(iter_tmp) is gtk.TreeIter:
       if(model_tmp.iter_depth(iter_tmp) == 1) or (self.clear_mode == 1 and model_tmp.iter_depth(iter_tmp) == 0): # Si es hoja
        if self.clear_mode == 0:
         self.webview.load_string("<h2>"+_("Feed")+": "+model_tmp.get_value(iter_tmp, 0)+"</h2>", "text/html", "utf-8", "valid_link")
        else:
         self.webview.load_string(ABOUT_PAGE, "text/html", "utf-8", "file://"+index_path)
       else: # Si es padre
        self.webview.load_string("<h2>"+_("Category")+": "+model_tmp.get_value(iter_tmp, 0)+"</h2>", "text/html", "utf-8", "valid_link")
      else:
       self.webview.load_string(ABOUT_PAGE, "text/html", "utf-8", "file://"+index_path)
      self.eb.hide()
      self.eb_image_zoom.hide()

    # OLD: elif(model.iter_depth(iter) == 0): # Si es PADRE...
    elif(model.iter_depth(iter) == 0) and (self.clear_mode == 0): # Si es PADRE...

     # 1º vamos a por el label de los feeds...
     feed_ids = ''
     feed_ids_list = []
     iter2 = model.iter_children(iter)
     while iter2:
      id_feed = self.treestore.get_value(iter2, 2)
      feed_ids += `id_feed` + ','
      feed_ids_list.append(`id_feed`)
      # START NAME PARSING (nodo origen) #
      nombre_feed = model.get_value(iter2, 0)
      nombre_feed = self.simple_name_parsing(nombre_feed)
      model.set(iter2, 0, nombre_feed, 3, 'normal')
      # END NAME PARSING (nodo origen) #
      iter2 = self.treestore.iter_next(iter2)
     feed_ids = feed_ids[0:-1]

     # 2º vamos a por las entries de los feeds...
     (model2, iter2) = self.treeselection2.get_selected()
     iter2 = model2.get_iter_root() # Magic
     while iter2:
      self.liststore.set_value(iter2, 3, 'normal')
      iter2 = self.liststore.iter_next(iter2)

     # ...y 3º a por los datos
     q = 'UPDATE articulo SET leido=1 WHERE id_feed IN (' + feed_ids + ')'
     self.lock.acquire()
     cursor.execute(q)
     self.conn.commit()
     self.lock.release()

     # START NAME PARSING (nodo destino) #
     # Destino: No leídos
     self.update_special_folder(9999)
     # Destino: Importantes
     self.update_special_folder(9998)
     # END NAME PARSING (nodo destino) #

     # Unbold category...
     model.set(iter, 3, 'normal')
     # ... and fold category (if applies).
     if (self.driven_mode == 1):
      self.treeview.collapse_row(model.get_path(iter))

    cursor.close()


  else: # La petición de toggle proviene de la LISTA DE ENTRIES DE UN FEED
   (model, iter) = self.treeselection2.get_selected()
   if(iter is not None): # Hay alguna fila de la lista seleccionada
    id_articulo = self.liststore.get_value(iter, 4)
    liststore_font_style = font_style = model.get(iter, 3)[0]

    if(data == 'single'):
     if(font_style == 'normal'):
      # 1º vamos a por la entry del feed...
      self.liststore.set_value(iter, 3, 'bold')

      # 2º a por los datos...
      self.lock.acquire()
      cursor.execute('UPDATE articulo SET leido = 0 WHERE id = ?', [id_articulo])
      self.conn.commit()
      self.lock.release()

      # Y actualizar el modelo de datos.
      (model, iter) = self.treeselection.get_selected()

      # 3º vamos a por el label del feed...
      # START NAME PARSING (nodo origen) #
      # Little hack for being able to mark read/unread the entries found on a search.
      try:
       nombre_feed = model.get_value(iter, 0)
       id_feed = model.get_value(iter, 2)
       (nombre_feed, no_leidos) = self.less_simple_name_parsing(nombre_feed)
       add_unit = True
      except:
       self.lock.acquire()
       cursor.execute('SELECT id_feed FROM articulo WHERE id = ' + `id_articulo`)
       id_feed = cursor.fetchone()[0]
       cursor.execute('SELECT nombre FROM feed WHERE id = ' + `id_feed`)
       nombre_feed = cursor.fetchone()[0]
       cursor.execute('SELECT count(id) FROM articulo WHERE id_feed = ' + `id_feed` + ' AND leido = 0 AND ghost = 0')
       no_leidos = cursor.fetchone()[0]
       self.lock.release()
       add_unit = False

      if no_leidos is not None:
       if add_unit is True:
        no_leidos = int(no_leidos) + 1
       feed_label = nombre_feed + ' [' + `no_leidos` + ']'
      else:
       feed_label = nombre_feed + ' [1]'
      # NEW
      if self.clear_mode == 1 and self.treeindex.has_key(id_feed) is False:
       if os.path.exists(favicon_path + '/' + `id_feed`):
        useless_iter, feed_iter = self.alphabetical_node_insertion(feed_label, [feed_label, `id_feed`, id_feed, 'bold'])
       else:
        useless_iter, feed_iter = self.alphabetical_node_insertion(feed_label, [feed_label, 'rss-image', id_feed, 'bold'])
       self.treeindex[id_feed] = feed_iter
      else:
      # NEW
       iter = self.treeindex[id_feed]
       model.set(iter, 0, feed_label, 3, 'bold')
      # END NAME PARSING (nodo origen) #

      if self.clear_mode == 0: # NEW
       # START NAME PARSING (nodo destino) #
       if nombre_feed == _("Important") or nombre_feed == _("Unread"):
        self.lock.acquire()
        cursor.execute('SELECT id_feed FROM articulo WHERE id = ?', [id_articulo])
        id_feed = cursor.fetchone()[0]
        self.lock.release()
        cursor.close()
        dest_iter = self.treeindex[id_feed] # dictionary to the rescue!
        nombre_feed_destino = model.get_value(dest_iter, 0)
        (nombre_feed_destino, no_leidos) = self.less_simple_name_parsing(nombre_feed_destino)
        if no_leidos is not None:
         no_leidos = int(no_leidos) + 1
         feed_label = nombre_feed_destino + ' [' + `no_leidos` + ']'
        else:
         feed_label = nombre_feed_destino + ' [1]'
        model.set(dest_iter, 0, feed_label, 3, 'bold')
        ### START: ¡También cabe actualizar su compañero de batallas!
        if nombre_feed == _("Important"):
         # Actualizamos Unread
         self.update_special_folder(9999)
        elif nombre_feed == _("Unread"):
         # Actualizamos Important
         self.update_special_folder(9998)
        ### END: ¡También cabe actualizar su compañero de batallas!
       else:
        # Destino: No leídos
        self.update_special_folder(9999)
        # Destino: Importantes
        self.update_special_folder(9998)
       # END NAME PARSING (nodo destino) #
       

     else: # if(font_style == 'bold')
      # 1º vamos a por la entry del feed...
      self.liststore.set_value(iter, 3, 'normal')

      # 2º a por los datos...
      self.lock.acquire()
      cursor.execute('UPDATE articulo SET leido = 1 WHERE id = ?', [id_articulo])
      self.conn.commit()
      self.lock.release()

      # Y actualizar el modelo de datos.
      (model, iter) = self.treeselection.get_selected()

      # 3º vamos a por el label del feed...
      # START NAME PARSING (nodo origen) #
      # Little hack for being able to mark read/unread the entries found on a search.
      #try: # Feed seleccionado en el tree
      # nombre_feed = model.get_value(iter, 0)
      # id_feed = model.get_value(iter, 2)
      #except: # Busqueda
      q = 'SELECT id_feed FROM articulo WHERE id = ' + `id_articulo`
      self.lock.acquire()
      cursor.execute(q)
      id_feed = cursor.fetchone()[0]
      self.lock.release()
      iter = self.treeindex[id_feed]
      nombre_feed = model.get_value(iter, 0)

      (nombre_feed, no_leidos) = self.less_simple_name_parsing(nombre_feed)
      if (no_leidos is not None) and (no_leidos > 0):
       no_leidos = int(no_leidos) - 1
       if no_leidos <= 0:
        font_style = 'normal'
        feed_label = nombre_feed
       else:
        font_style = 'bold'
        feed_label = nombre_feed + ' [' + `no_leidos` + ']'
      else:
       feed_label = nombre_feed
       font_style = 'normal'
      # NEW
      if self.clear_mode == 1 and self.treeindex.has_key(id_feed) and ('[' not in feed_label and ']' not in feed_label):
       self.treestore.remove(iter)
       del self.treeindex[id_feed] # Update feeds dict
      else:
      # NEW
       model.set(iter, 0, feed_label, 3, font_style)
      # END NAME PARSING (nodo origen) #

      if self.clear_mode == 0: # NEW
       # START NAME PARSING (nodo destino) #
       if nombre_feed == _("Important") or nombre_feed == _("Unread"):
        self.lock.acquire()
        cursor.execute('SELECT id_feed FROM articulo WHERE id = ?', [id_articulo])
        id_feed = cursor.fetchone()[0]
        self.lock.release()
        cursor.close()
        dest_iter = self.treeindex[id_feed] # dictionary to the rescue!
        nombre_feed_destino = model.get_value(dest_iter, 0)
        (nombre_feed_destino, no_leidos) = self.less_simple_name_parsing(nombre_feed_destino)
        if (no_leidos is not None) and (no_leidos > 0):
         no_leidos = int(no_leidos) - 1
         if no_leidos <= 0:
          font_style = 'normal'
          feed_label = nombre_feed_destino
         else:
          font_style = 'bold'
          feed_label = nombre_feed_destino + ' [' + `no_leidos` + ']'
        else:
         feed_label = nombre_feed_destino
         font_style = 'normal'
        model.set(dest_iter, 0, feed_label, 3, font_style)
        ### START: ¡También cabe actualizar su compañero de batallas!
        if nombre_feed == _("Important"):
         # Actualizamos Unread
         self.update_special_folder(9999)
        elif nombre_feed == _("Unread"):
         # Actualizamos Important
         self.update_special_folder(9998)
        ### END: ¡También cabe actualizar su compañero de batallas!
       else:
        # Destino: No leídos
        self.update_special_folder(9999)
        # Destino: Importantes
        self.update_special_folder(9998)
       # END NAME PARSING (nodo destino) #


    elif(data == 'all'):
     leido = 0
     if(font_style == 'normal'):
      font_style = 'bold'
     else:
      font_style = 'normal'
      leido = 1
     iter = model.get_iter_root() # Magic
     entry_ids = ''
     count = 0
     while iter:
      count += 1
      self.liststore.set_value(iter, 3, font_style)
      id_articulo = self.liststore.get_value(iter, 4)
      entry_ids += `id_articulo` + ','
      iter = self.liststore.iter_next(iter)
     entry_ids = entry_ids[0:-1]

     # La actualización en BD del nodo origen se deja para el final...
     q = 'UPDATE articulo SET leido = ' + `leido` + ' WHERE id IN (' + entry_ids + ')'
     self.lock.acquire()
     cursor.execute(q)
     self.conn.commit()
     self.lock.release()

     # Y actualizar el modelo de datos.
     (model, iter) = self.treeselection.get_selected()
     # START NAME PARSING (nodo origen) #
     # Little hack -slightly different- for being able to mark read/unread the entries found on a search.
     nombre_feeds = []
     id_feeds = []
     ###on_a_search = False
     try: # Feed seleccionado en el tree
      nombre_feeds.append(model.get_value(iter, 0))
      id_feeds.append(model.get_value(iter, 2))
      id_feed = id_feeds[0]
     except: # Busqueda o clear_mode?
      ###on_a_search = True # OLD
      q = 'SELECT DISTINCT id_feed FROM articulo WHERE id IN (' + entry_ids + ')'
      self.lock.acquire()
      cursor.execute(q)
      id_feeds = cursor.fetchall()
      self.lock.release()
      id_feed = id_feeds[0][0]
      ###if len(id_feeds) > 1: # NEW (Dirty hack!!! Puede fallar con busquedas con 1 solo feed como resultado!)
      ### on_a_search = True # NEW
      for id_feed_tmp in id_feeds:
       try: # NEW
        iter = self.treeindex[id_feed_tmp[0]]
        nombre_feeds.append(model.get_value(iter, 0))
       except: # NEW
        self.lock.acquire() # NEW
        cursor.execute('SELECT nombre FROM feed WHERE id = ' + `id_feed_tmp[0]`) # NEW
        nombre_feed = cursor.fetchone()[0] # NEW
        nombre_feeds.append(nombre_feed) # NEW
        self.lock.release() # NEW

     ###id_feed = id_feeds[0]
     nombre_feed = nombre_feeds[0]
     ###if not on_a_search:
     if self.on_a_search == False:
      font_style = ''
      if liststore_font_style == 'bold': # Si antes era bold...
       nombre_feed = self.simple_name_parsing(nombre_feed)
       feed_label = nombre_feed
       font_style = 'normal'
       # NEW
       # TODO: Borrar el feed de la lista #
       if self.clear_mode == 1 and self.treeindex.has_key(id_feed):
        self.treestore.remove(iter) # <-- es el iter que queremos u otro? xD
        del self.treeindex[id_feed]
       else:
        model.set(iter, 0, feed_label, 3, font_style)
       # NEW
      elif liststore_font_style == 'normal': # Si antes era normal...
       nombre_feed = self.simple_name_parsing(nombre_feed)
       if nombre_feed == _("Important") or nombre_feed == _("Unread"):
        q = 'SELECT count(id) FROM articulo WHERE leido=0 AND ghost=0'
       else:
        if self.hide_readentries:
         q = 'SELECT count(id) FROM articulo WHERE id_feed = (SELECT id_feed FROM articulo WHERE id='+`id_articulo`+') AND ghost=0 AND leido=0'
        else:
         q = 'SELECT count(id) FROM articulo WHERE id_feed = (SELECT id_feed FROM articulo WHERE id='+`id_articulo`+') AND ghost=0'
       self.lock.acquire()
       cursor.execute(q)
       count = cursor.fetchone()
       self.lock.release()
       if count is not None:
        if count[0] > 0:
         feed_label = nombre_feed + ' [' + `count[0]` + ']'
         font_style = 'bold'
        else:
         feed_label = nombre_feed
         font_style = 'normal'
       else:
        feed_label = nombre_feed
        font_style = 'normal'
       # NEW
       # TODO: Añadir el feed a la lista #
       if font_style == 'bold':
        if self.clear_mode == 1 and self.treeindex.has_key(id_feed) is False:
         if os.path.exists(favicon_path + '/' + `id_feed`):
          useless_iter, feed_iter = self.alphabetical_node_insertion(feed_label, [feed_label, `id_feed`, id_feed, 'bold'])
         else:
          useless_iter, feed_iter = self.alphabetical_node_insertion(feed_label, [feed_label, 'rss-image', id_feed, 'bold'])
         self.treeindex[id_feed] = feed_iter
        else:
         model.set(iter, 0, feed_label, 3, font_style)
       # TODO: Eliminar el feed de la lista #
       else:
        if self.clear_mode == 1 and self.treeindex.has_key(id_feed) and ('[' not in feed_label and ']' not in feed_label):
         self.treestore.remove(iter)
         del self.treeindex[id_feed]
        else:
         model.set(iter, 0, feed_label, 3, font_style)
       # NEW
       ###model.set(iter, 0, feed_label, 3, font_style)
     # END NAME PARSING (nodo origen) #

     if self.clear_mode == 0: # NEW
      # START NAME PARSING (nodo destino) #
      if nombre_feed == _("Important") or nombre_feed == _("Unread"):
       #print 'Destino: feed normal'
       if liststore_font_style == 'bold':
        q = 'SELECT DISTINCT id_feed FROM articulo WHERE id IN (' + entry_ids + ')'
        self.lock.acquire()
        cursor.execute(q)
        row = cursor.fetchall()
        self.lock.release()
        if (row is not None) and (len(row)>0):
         for feed in row:
          q = 'SELECT count(id) FROM articulo WHERE id_feed = ' + `feed[0]` + ' AND leido=0 AND ghost=0'
          self.lock.acquire()
          cursor.execute(q)
          count = cursor.fetchone()
          self.lock.release()
          dest_iter = self.treeindex[feed[0]]
          nombre_feed_destino = model.get_value(dest_iter, 0)
          nombre_feed_destino = self.simple_name_parsing(nombre_feed_destino)
          if count[0] is not None:
           if count[0] > 0:
            feed_label = nombre_feed_destino + ' [' + `count[0]` + ']'
            font_style = 'bold'
           else:
            feed_label = nombre_feed_destino
            font_style = 'normal'
          else:
           feed_label = nombre_feed_destino
           font_style = 'normal'
          model.set(dest_iter, 0, feed_label, 3, font_style)
          ### START: ¡También cabe actualizar su compañero de batallas!
          if nombre_feed == _("Important"):
           # Actualizamos Unread
           self.update_special_folder(9999)
          elif nombre_feed == _("Unread"):
           # Actualizamos Important
           self.update_special_folder(9998)
          ### END: ¡También cabe actualizar su compañero de batallas!
       elif liststore_font_style == 'normal':
        q = 'SELECT DISTINCT id_feed FROM articulo WHERE id IN (' + entry_ids + ')'
        self.lock.acquire()
        cursor.execute(q)
        row = cursor.fetchall()
        self.lock.release()
        if row is not None:
         for feed in row:
          q = 'SELECT count(id) FROM articulo WHERE id_feed = ' + `feed[0]` + ' AND leido=0 AND ghost=0'
          self.lock.acquire()
          cursor.execute(q)
          count = cursor.fetchone()
          self.lock.release()
          dest_iter = self.treeindex[feed[0]]
          nombre_feed_destino = model.get_value(dest_iter, 0)
          nombre_feed_destino = self.simple_name_parsing(nombre_feed_destino)
          if count[0] is not None:
           if count[0] > 0:
            feed_label = nombre_feed_destino + ' [' + `count[0]` + ']'
            font_style = 'bold'
           else:
            feed_label = nombre_feed_destino
            font_style = 'normal'
          else:
           feed_label = nombre_feed_destino
           font_style = 'normal'
          model.set(dest_iter, 0, feed_label, 3, 'bold')
          ### START: ¡También cabe actualizar su compañero de batallas!
          if nombre_feed == _("Important"):
           # Actualizamos Unread
           self.update_special_folder(9999)
          elif nombre_feed == _("Unread"):
           # Actualizamos Important
           self.update_special_folder(9998)
          ### END: ¡También cabe actualizar su compañero de batallas!
      else:
       # Destino: No leídos
       self.update_special_folder(9999)
       # Destino: Importantes
       self.update_special_folder(9998)

       ###if on_a_search:
       if self.on_a_search:
        # Actualizar todos los feeds!!!
        i = 0
        font_style = ''
        if liststore_font_style == 'bold': # Si antes era bold...
         for nombre_feed in nombre_feeds:
          feed_label = self.simple_name_parsing(nombre_feed)
          iter = self.treeindex[id_feeds[i][0]]
          model.set(iter, 0, feed_label, 3, 'normal')
          i += 1
        elif liststore_font_style == 'normal': # Sino, si antes era normal...
         for nombre_feed in nombre_feeds:
          nombre_feed = self.simple_name_parsing(nombre_feed)
          q = 'SELECT count(id) FROM articulo WHERE id_feed = ' + `id_feeds[i][0]` + ' AND leido=0 AND ghost=0'
          self.lock.acquire()
          cursor.execute(q)
          count = cursor.fetchone()
          self.lock.release()
          if count[0] is not None:
           if count[0] > 0:
            feed_label = nombre_feed + ' [' + `count[0]` + ']'
            font_style = 'bold'
           else:
            feed_label = nombre_feed
            font_style = 'normal'
          else:
           feed_label = nombre_feed
           font_style = 'normal'
          iter = self.treeindex[id_feeds[i][0]]
          model.set(iter, 0, feed_label, 3, font_style)
          i += 1
      # END NAME PARSING (nodo destino) #
     cursor.close()

     # Limpieza de la GUI
     if liststore_font_style == 'bold':
      if self.hide_readentries:
       self.liststore.clear() # Limpieza de tabla de entries/articulos
       self.scrolled_window2.set_size_request(0,0)
       self.scrolled_window2.hide()
       (model_tmp, iter_tmp) = self.treeselection.get_selected()
       if type(iter_tmp) is gtk.TreeIter:
        if(model_tmp.iter_depth(iter_tmp) == 1): # Si es hoja
         self.webview.load_string("<h2>"+_("Feed")+": "+nombre_feed+"</h2>", "text/html", "utf-8", "valid_link")
        elif(model.iter_depth(iter) == 0): # Si es padre
         self.webview.load_string("<h2>"+_("Category")+": "+model_tmp.get_value(iter_tmp, 0)+"</h2>", "text/html", "utf-8", "valid_link")
       self.eb.hide()
       self.eb_image_zoom.hide()

    if self.clear_mode == 0: # NEW
     # Unbold categories (if needed).
     self.toggle_category_bold_all()

 def abrir_browser(self, event=None, data=None):
  """Opens a given url in the user sensible web browser."""
  (model, iter) = self.treeselection2.get_selected()
  if(iter is not None): # Hay alguna fila de la lista seleccionada
   if data is not None:
    link = data
   else:
    id_articulo = self.liststore.get_value(iter, 4)
    cursor = self.conn.cursor()
    self.lock.acquire()
    cursor.execute('SELECT enlace FROM articulo WHERE id = ?', [id_articulo])
    link = cursor.fetchone()[0]
    self.lock.release()
    cursor.close()
   webbrowser.open_new(link) # New win!

 def copiar_al_portapapeles(self, event=None, data=None):
  """Copies the entry's URL to the system clipboard."""
  (model, iter) = self.treeselection2.get_selected()
  if(iter is not None): # Hay alguna fila de la lista seleccionada
   if data is not None:
    link = data
   else:
    id_articulo = self.liststore.get_value(iter, 4)
    cursor = self.conn.cursor()
    self.lock.acquire()
    cursor.execute('SELECT enlace FROM articulo WHERE id = ?', [id_articulo])
    link = cursor.fetchone()[0]
    self.lock.release()
    cursor.close()
   clipboard = gtk.clipboard_get()
   clipboard.set_text(link.encode("utf8"))
   clipboard.store()

 def htmlentitydecode(self, text):
  """Escapes htmlentities. Thanks to Fredrik Lundh!"""
  def fixup(m):
   text = m.group(0)
   if text[:2] == "&#": # character reference
    try:
     if text[:3] == "&#x":
      return unichr(int(text[3:-1], 16))
     else:
      return unichr(int(text[2:-1]))
    except ValueError: pass
   else: # named entity
    try:
     text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
    except KeyError: pass
   return text # leave as is
  return re.sub("&#?\w+;", fixup, text)

 def list_row_selection(self, event):
  """List row change detector"""

  (model, iter) = self.treeselection2.get_selected()
  if(iter is not None): # Hay alguna fila de la lista seleccionada
   self.on_a_search = False # NEW (Resets the on_a_search flag)
   flag_importante = self.liststore.get_value(iter, 1)
   titulo = self.liststore.get_value(iter, 2)
   id_articulo = self.liststore.get_value(iter, 4)
   liststore_font_style = self.liststore.get_value(iter, 3)
   if liststore_font_style == 'bold':
    model.set(iter, 3, 'normal')

   # NEW: live feed item removal!
   if self.hide_readentries:
    iter_tmp = self.liststore.get_iter_root() # Magic
    while iter_tmp:
     font_style_tmp = self.liststore.get_value(iter_tmp, 3)
     id_articulo_tmp = self.liststore.get_value(iter_tmp, 4)
     if (id_articulo != id_articulo_tmp) and (font_style_tmp == 'normal'):
      # Quitamos item de la lista
      self.liststore.remove(iter_tmp)
     if self.liststore.iter_is_valid(iter_tmp):
      iter_tmp = self.liststore.iter_next(iter_tmp) # Pasamos al siguiente
     else:
      break
   # NEW

   # Coloración de la barra del título de la entry caso de ser importante
   if flag_importante:
    self.eb.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("pink"))
   else:
    self.eb.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#EDECEB"))

   # This prevents htmlentities from doing weird things to the headerlink!
   self.headerlink.set_markup('<b><u><span foreground="blue">'+saxutils.escape(self.htmlentitydecode(titulo))+'</span></u></b>')
   self.headerlink.set_justify(gtk.JUSTIFY_CENTER)
   self.headerlink.set_ellipsize(pango.ELLIPSIZE_END)
   self.eb.show()
   self.eb_image_zoom.show()

   cursor = self.conn.cursor()
   self.lock.acquire()
   cursor.execute('SELECT leido,contenido FROM articulo WHERE id = ?', [id_articulo])
   row = cursor.fetchone()
   self.lock.release()
   contenido = row[1]

   # Offline mode image retrieving
   if self.offline_mode == 1:
    # Reemplazar los tags img para que apunten a local...
    self.lock.acquire()
    cursor.execute('SELECT nombre,url FROM imagen WHERE id_articulo = ?', [id_articulo])
    row2 = cursor.fetchall()
    self.lock.release()
    if (row2 is not None) and (len(row2)>0):
     for img in row2:
      # Sustituir los paths de imagenes remotas por los locales!
      contenido = contenido.replace(img[1], images_path + '/' + `img[0]`)
     # Turno de webkit...
     self.valid_links.append('file://'+images_path+'/'+`img[0]`) # Valid link for now...
     self.webview.load_string(contenido, "text/html", "utf-8", 'file://'+images_path+'/'+`img[0]`)
     self.valid_links.pop() # ...and invalid link again!
    else:
     self.webview.load_string(contenido, "text/html", "utf-8", "valid_link")
   else:
    self.webview.load_string(contenido, "text/html", "utf-8", "valid_link")

   if(row[0] == 0):
    # Si no estaba leído, marcarlo como tal.
    self.lock.acquire()
    cursor.execute('UPDATE articulo SET leido=1 WHERE id = ?', [id_articulo])
    self.conn.commit()
    self.lock.release()
   cursor.close()

   # Y actualizar el modelo de datos.
   (model, iter) = self.treeselection.get_selected()
   # START NAME PARSING (nodo origen) #
   if liststore_font_style == 'bold': # Si la entry era bold, cabe actualizar el nodo del feed
    feed_label = ''
    # Little hack for being able to mark read/unread the entries found on a search.
    #try:
    # nombre_feed = model.get_value(iter, 0)
    # id_feed = model.get_value(iter, 2)
    #except:
    q = 'SELECT id_feed FROM articulo WHERE id = ' + `id_articulo`
    self.lock.acquire()
    cursor.execute(q)
    id_feed = cursor.fetchone()[0]
    self.lock.release()
    iter = self.treeindex[id_feed]
    nombre_feed = model.get_value(iter, 0)

    (nombre_feed, no_leidos) = self.less_simple_name_parsing(nombre_feed)
    if (no_leidos is not None) and (no_leidos > 0):
     no_leidos = int(no_leidos) - 1
     if no_leidos <= 0:
      font_style = 'normal'
      feed_label = nombre_feed
     else:
      font_style = 'bold'
      feed_label = nombre_feed + ' [' + `no_leidos` + ']'
    else:
     feed_label = nombre_feed
     font_style = 'normal'
    # NEW
    if self.clear_mode == 1 and self.treeindex.has_key(id_feed) and ('[' not in feed_label and ']' not in feed_label):
     self.treestore.remove(iter)
     del self.treeindex[id_feed] # Update feeds dict
    else:
    # NEW
     model.set(iter, 0, feed_label, 3, font_style)
   # END NAME PARSING (nodo origen) #
    if self.clear_mode == 0: # NEW
     # START NAME PARSING (nodo destino) #
     if nombre_feed == _("Important") or nombre_feed == _("Unread"):
      #print 'Destino: feed normal'
      self.lock.acquire()
      cursor.execute('SELECT id_feed FROM articulo WHERE id = ?', [id_articulo])
      id_feed = cursor.fetchone()[0]
      self.lock.release()
      dest_iter = self.treeindex[id_feed] # dictionary to the rescue!
      nombre_feed_destino = model.get_value(dest_iter, 0)
      (nombre_feed_destino, no_leidos) = self.less_simple_name_parsing(nombre_feed_destino)
      if no_leidos is not None:
       no_leidos = int(no_leidos) - 1
       if no_leidos == 0: # Si no quedan entries del feed por leer...
        font_style = 'normal'
        feed_label = nombre_feed_destino
       else: # Y si todavía quedan...
        font_style = 'bold'
        feed_label = nombre_feed_destino + ' [' + `no_leidos` + ']'
       model.set(dest_iter, 0, feed_label, 3, font_style)
      ### START: ¡También cabe actualizar su compañero de batallas!
      if nombre_feed == _("Important"):
       # Actualizamos Unread
       self.update_special_folder(9999)
      elif nombre_feed == _("Unread"):
       # Actualizamos Important
       self.update_special_folder(9998)
       # ESTO ES ABSOLUTAMENTE NECESARIO para que 'Important' no actúe si no tenemos el flag_importante.
       # Aplicarlo en los demás sitios que falte.
       if nombre_feed == _("Important") or (nombre_feed == _("Unread") and flag_importante is True):
        model.set(dest_iter, 0, feed_label, 3, font_style)
      ### END: ¡También cabe actualizar su compañero de batallas!
      # Unbold categories (if needed).
      self.toggle_category_bold_all()
     else:
      # Destino: No leídos
      self.update_special_folder(9999)
      # Destino: Importantes
      if flag_importante:
       self.update_special_folder(9998)
     # END NAME PARSING (nodo destino) #
     # Unbold category if needed.
     self.toggle_category_bold()

 def tree_row_selection(self, event):
  """Feed row change detector; triggers entry visualization on the list."""
  (model, iter) = self.treeselection.get_selected()
  if(iter is not None): # Hay algún nodo seleccionado
   row_name = self.treestore.get_value(iter, 0)
   id_feed = self.treestore.get_value(iter, 2)
   if (id_feed == 9998) or (id_feed == 9999):
    self.populate_entries(id_feed)
    self.treeview2.scroll_to_point(0,0) # Reposition entry list at the top.
    nombre_feed = self.simple_name_parsing(row_name)
    self.webview.load_string("<h2>" + _("Special folder") + ": "+nombre_feed+"</h2>", "text/html", "utf-8", "valid_link")
   # OLD: elif(model.iter_depth(iter) == 1): # Si es hoja, presentar entradas
   elif(model.iter_depth(iter) == 1) or (model.iter_depth(iter) == 0 and self.clear_mode == 1): # Si es hoja, presentar entradas
    self.populate_entries(id_feed)
    self.treeview2.scroll_to_point(0,0) # Reposition entry list at the top.
    cursor = self.conn.cursor()
    self.lock.acquire()
    cursor.execute('SELECT url FROM feed WHERE id = ?', [id_feed])
    url = cursor.fetchone()[0]
    self.lock.release()
    cursor.close()
    # START NAME PARSING #
    row_name = self.simple_name_parsing(row_name)
    # END NAME PARSING #
    FEED_PAGE = "<h2>Feed: " + row_name + "</h2><p>" + _("Source") + ": <a href='" + url + "'>" + url + "</a></p>"
    self.webview.load_string(FEED_PAGE, "text/html", "utf-8", "valid_link")
   # OLD: elif(model.iter_depth(iter) == 0): # Si es padre, limpliar 
   elif(model.iter_depth(iter) == 0 and self.clear_mode == 0): # Si es padre, limpliar
    self.liststore.clear() # Limpieza de tabla de entries/articulos
    self.scrolled_window2.set_size_request(0,0)
    self.scrolled_window2.hide()
    self.webview.load_string("<h2>" + _("Category") + ": "+row_name+"</h2>", "text/html", "utf-8", "valid_link")
   # This is usefull to store an URI (in case of reloads):
   #self.webview.load_string(ABOUT_PAGE, "text/html", "utf-8", "file://"+index_path)
   self.eb.hide()
   self.eb_image_zoom.hide()

 def tree_row_activated(self, treeview, iter, path):
  """Toggles expansion of a tree node when double clicking on it."""
  (model, iter) = self.treeselection.get_selected()
  path = model.get_path(iter)
  if(treeview.row_expanded(path)):
   treeview.collapse_row(path)
  else:
   treeview.expand_row(path, open_all=False)

 def tree_row_collapsed(self, treeview, iter, path):
  """Changes category icon to gtk.STOCK_DIRECTORY."""
  (model, useless_iter) = self.treeselection.get_selected()
  model.set(iter, 1, gtk.STOCK_DIRECTORY)

 def tree_row_expanded(self, treeview, iter, path):
  """Changes category icon to gtk.STOCK_OPEN."""
  (model, useless_iter) = self.treeselection.get_selected()
  model.set(iter, 1, gtk.STOCK_OPEN)

 def statusicon_activate(self, data=None):
  """Activates the tray icon."""
  global window_visible # Global since we need to modify it

  # Deactivates tray icon blinking
  if self.show_trayicon == 1:
   self.statusicon.set_blinking(False)

  if(window_visible):
   self.window.hide()
   (self.x, self.y) = self.window.get_position()
   window_visible = False
  else:
   self.window.move(self.x, self.y)
   self.window.show()
   window_visible = True

 def yes_no_message(self, str):
  """Shows a custom yes/no message dialog."""
  dialog = gtk.MessageDialog(self.window, (gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT), gtk.MESSAGE_WARNING, gtk.BUTTONS_NONE, None)
  dialog.set_title(_('Warning!'))
  dialog.set_markup(str)
  dialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
  dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT)
  dialog.set_default_response(gtk.RESPONSE_REJECT) # Sets default response
  response = dialog.run()
  dialog.destroy()
  return response

 def warning_message(self, str):
  """Shows a custom warning message dialog"""
  dialog = gtk.MessageDialog(self.window, (gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT), gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, None)
  dialog.set_title(_('Warning!'))
  dialog.set_markup(str)
  dialog.run()
  dialog.destroy()

 def load_puf(self, data=None):
  """Shows the PUF/FAQ on the browser window."""
  self.scrolled_window2.set_size_request(0,0)
  self.scrolled_window2.hide()
  self.eb.hide()
  self.eb_image_zoom.hide()
  self.webview.load_string(PUF_PAGE, "text/html", "utf-8", "file://"+puf_path)

 def check_app_updates(self, action=None):
  """Launches the corresponding core function threaded."""
  t = threading.Thread(target=self.check_app_updates_helper, args=(action, ))
  t.setDaemon(True) # This allows some kind of 'killable' threads... be careful!
  t.start()

 def check_app_updates_helper(self, action=None):
  """Check if a new version of the application exists."""
  global APP_VERSION
  try:
   gtk.gdk.threads_enter()
   web_file = urllib2.urlopen('http://enchufado.com/proyectos/naufrago/app_version')
   read = web_file.read().rstrip()
   web_file.close()
   gtk.gdk.threads_leave()
   if APP_VERSION == read:
    if type(action) is gtk.Action:
     dialog = gtk.Dialog(_("Upgrade checker"), self.window, (gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT), None)
     dialog.set_size_request(350,75)
     dialog.set_has_separator(False)
     dialog.add_button(_("Close"), gtk.RESPONSE_ACCEPT)
     label = gtk.Label(_("No updates available."))
     dialog.vbox.pack_start(label)
     dialog.show_all()
     dialog.run()
     dialog.destroy()
   else:
    dialog = gtk.Dialog(_("Upgrade checker"), self.window, (gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT), None)
    dialog.set_size_request(350,100)
    dialog.set_has_separator(False)
    dialog.add_button(_("Close"), gtk.RESPONSE_ACCEPT)
    label = gtk.Label("")
    label.set_markup("Naufrago! version <b>"+read+"</b> is available! Get it at:")
    download_url = 'http://sourceforge.net/projects/naufrago/files/'
    url_button = gtk.LinkButton(download_url, download_url)
    dialog.vbox.pack_start(label)
    dialog.vbox.pack_start(url_button)
    dialog.show_all()
    dialog.run()
    dialog.destroy()
  except:
   if type(action) is gtk.Action:
    dialog = gtk.Dialog(_("Upgrade checker"), self.window, (gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT), None)
    dialog.set_size_request(350,75)
    dialog.set_has_separator(False)
    dialog.add_button(_("Close"), gtk.RESPONSE_ACCEPT)
    label = gtk.Label(_("Coult not contact server. Try again later!"))
    dialog.vbox.pack_start(label)
    dialog.show_all()
    dialog.run()
    dialog.destroy()

 def help_about(self, action):
  """Shows the about message dialog"""
  global APP_VERSION
  LICENSE = """   
        This program is free software: you can redistribute it and/or modify
        it under the terms of the GNU General Public License as published by
        the Free Software Foundation, either version 3 of the License, or
        (at your option) any later version.

        This program is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        GNU General Public License for more details.

        You should have received a copy of the GNU General Public License
        along with this program.  If not, see <http://www.gnu.org/licenses/>.
        """
  about = gtk.AboutDialog()
  about.set_transient_for(self.window)
  about.set_program_name("Naufrago!")
  about.set_version(APP_VERSION)
  about.set_copyright("(c) 2010 Jordi Oliveras Palacios")
  about.set_license(LICENSE)
  about.set_comments(_("Naufrago! is a simple RSS reader"))
  about.set_website("http://www.enchufado.com/")
  about.set_logo(gtk.gdk.pixbuf_new_from_file(media_path + 'Viking_Longship.svg'))
  about.run()
  about.destroy()

 def create_ui(self, window):
  """Creates the menubar"""
  ui_string = """<ui>
               <menubar name='Menubar'>
                <menu action='ArchiveMenu'>
                 <menuitem action='New feed'/>
                 <menuitem action='New category'/>
                 <menuitem action='Delete feed'/>
                 <menuitem action='Delete category'/>
                 <separator/>
                 <menuitem action='Import feeds'/>
                 <menuitem action='Export feeds'/>
                 <separator/>
                 <menuitem action='Quit'/>
                </menu>
                <menu action='EditMenu'>
                 <menuitem action='Edit'/>
                 <menuitem action='Search'/>
                 <menuitem action='Read all'/>
                 <menuitem action='Preferences'/>
                </menu>
                <menu action='NetworkMenu'>
                 <menuitem action='Update'/>
                 <menuitem action='Update all'/>
                </menu>
                <menu action='HelpMenu'>
                 <menuitem action='FAQ'/>
                 <menuitem action='Check updates'/>
                 <menuitem action='About'/>
                </menu>
               </menubar>
               <toolbar name='Toolbar'>
                <toolitem name='New feed' action='New feed'/>
                <toolitem name='New category' action='New category'/>
                <separator name='sep1'/>
                <toolitem name='Update all' action='Update all'/>
                <toolitem name='Stop update' action='Stop update'/>
                <toolitem name='Read all' action='Read all'/>
                <separator name='sep2'/>
                <toolitem name='Search' action='Search'/>
                <toolitem name='Preferences' action='Preferences'/>
               </toolbar>
              </ui>"""

  # Generate a stock image from a file (http://faq.pygtk.org/index.py?req=show&file=faq08.012.htp)
  factory = gtk.IconFactory()
  pixbuf = gtk.gdk.pixbuf_new_from_file(media_path + 'SRD_RSS_Logo_mini.png')
  iconset = gtk.IconSet(pixbuf)
  factory.add('rss-image', iconset)
  factory.add_default()

  factory = gtk.IconFactory()
  pixbuf = gtk.gdk.pixbuf_new_from_file(media_path + 'cross_out.png')
  iconset = gtk.IconSet(pixbuf)
  factory.add('crossout-image', iconset)
  factory.add_default()

  # Una opción para que se muestren los iconos en los menus (a contracorriente de Gnome):
  # gconf-editor: Desktop -> Gnome -> Interface -> menus_have_icons (y buttons_have_icons)
  ag = gtk.ActionGroup('WindowActions')
  actions = [
            ('ArchiveMenu', None, _('_Archive')),
            ('New feed', 'rss-image', _('_New feed'), '<control>N', _('Adds a feed'), self.add_feed),
            ('New category', gtk.STOCK_DIRECTORY, _('New _category'), '<alt>C', _('Adds a category'), self.add_category),
            ('Delete feed', gtk.STOCK_CLEAR, _('Delete feed'), None, _('Deletes a feed'), self.delete_feed),
            ('Delete category', gtk.STOCK_CANCEL, _('Delete category'), None, _('Deletes a category'), self.delete_category),
            ('Import feeds', gtk.STOCK_REDO, _('Import feeds'), None, _('Imports a feedlist'), self.import_feeds),
            ('Export feeds', gtk.STOCK_UNDO, _('Export feeds'), None, _('Exports a feedlist'), self.export_feeds),
            ('Quit', gtk.STOCK_QUIT, _('_Quit'), '<control>Q', _('Quits'), self.delete_event),
            ('EditMenu', None, _('E_dit')),
            ('Edit', gtk.STOCK_EDIT, _('_Edit'), '<control>E', _('Edits the selected element'), self.edit),
            ('Search', gtk.STOCK_FIND, _('Search'), '<control>F', _('Searchs for a term in the feeds'), self.search),
            ('Read all', gtk.STOCK_SORT_ASCENDING, _('Read all'), '<control>M', _('Mark all feed items as read'), self.mark_all_as_read),
            ('Preferences', gtk.STOCK_EXECUTE, _('_Preferences'), '<control>P', _('Shows preferences'), self.preferences),
            ('NetworkMenu', None, _('_Network')),
            ('Update', None, _('_Update'), '<control>U', _('Updates the selected feed'), self.update_feed),
            ('Update all', gtk.STOCK_REFRESH, _('Update all'), '<control>R', _('Update all feeds'), self.update_all_feeds),
            ('Stop update', gtk.STOCK_STOP, _('Stop'), None, _('Stop update'), self.stop_feed_update),
            ('HelpMenu', None, _('_Help')),
            ('FAQ', gtk.STOCK_HELP, _('FAQ'), None, _('FAQ'), self.load_puf),
            ('Check updates', None, _('Check updates'), None, _('Check updates'), self.check_app_updates),
            ('About', gtk.STOCK_ABOUT, _('_About'), None, _('About'), self.help_about),
            ]

  ag.add_actions(actions)
  self.ui = gtk.UIManager()
  self.ui.insert_action_group(ag, 0)
  self.ui.add_ui_from_string(ui_string)
  self.window.add_accel_group(self.ui.get_accel_group())

 def create_base(self):
  """Creates the base app structure on the user home dir"""
  if not os.path.exists(db_path):
   if distro_package:
    os.makedirs(os.getenv("HOME") + '/.config/naufrago/')

   self.conn = sqlite3.connect(db_path, check_same_thread=False)
   cursor = self.conn.cursor()
   self.lock.acquire()
   cursor.executescript('''
     CREATE TABLE config(window_position varchar(16) NOT NULL, window_size varchar(16) NOT NULL, scroll1_size varchar(16) NOT NULL, scroll2_size varchar(16) NOT NULL, num_entries integer NOT NULL, update_freq integer NOT NULL, init_unfolded_tree integer NOT NULL, init_tray integer NOT NULL, init_update_all integer NOT NULL, offline_mode integer NOT NULL, show_trayicon integer NOT NULL, toolbar_mode integer NOT NULL, show_newentries_notification integer NOT NULL, hide_readentries integer NOT NULL, hide_dates integer NOT NULL, driven_mode integer NOT NULL, update_freq_timemode integer NOT NULL, init_check_app_updates integer NOT NULL, clear_mode integer NOT NULL);
     CREATE TABLE categoria(id integer PRIMARY KEY, nombre varchar(32) NOT NULL);
     CREATE TABLE feed(id integer PRIMARY KEY, nombre varchar(32) NOT NULL, url varchar(1024) NOT NULL, id_categoria integer NOT NULL);
     CREATE TABLE articulo(id integer PRIMARY KEY, titulo varchar(256) NOT NULL, contenido text, fecha integer NOT NULL, enlace varchar(1024) NOT NULL, leido INTEGER NOT NULL, importante INTEGER NOT NULL, imagenes TEXT, id_feed integer NOT NULL, entry_unique_id varchar(1024) NOT NULL, ghost integer NOT NULL);
     CREATE TABLE imagen(id integer PRIMARY KEY, nombre integer NOT NULL, url TEXT NOT NULL, id_articulo integer NOT NULL);
     INSERT INTO config VALUES('0,0', '600x400', '175x50', '300x150', 10, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0);
     INSERT INTO categoria VALUES(null, 'General');
     INSERT INTO feed VALUES(null, 'enchufado.com', 'http://enchufado.com/rss2.php', 1);''')
   self.conn.commit()
   self.lock.release()
   cursor.close()
   os.makedirs(favicon_path)
   os.makedirs(images_path)
  else:
   self.conn = sqlite3.connect(db_path, check_same_thread=False)

 def get_config(self):
  """Retrieves the app configuration"""
  global ABOUT_PAGE, PUF_PAGE

  cursor = self.conn.cursor()
  self.lock.acquire()
  cursor.execute('SELECT * FROM config')
  row = cursor.fetchone()
  self.lock.release()
  cursor.close()
  self.x = int(row[0].split(",")[0])
  self.y = int(row[0].split(",")[1])
  self.w = int(row[1].split("x")[0])
  self.h = int(row[1].split("x")[1])
  self.a = int(row[2].split("x")[0])
  self.b = int(row[2].split("x")[1])
  self.c = int(row[3].split("x")[0])
  self.d = int(row[3].split("x")[1])
  self.num_entries = int(row[4])
  self.update_freq = int(row[5])
  self.init_unfolded_tree = int(row[6])
  self.init_tray = int(row[7])
  self.init_update_all = int(row[8])
  self.offline_mode = int(row[9])
  self.show_trayicon = int(row[10])
  self.toolbar_mode = int(row[11])
  self.show_newentries_notification = int(row[12])
  self.hide_readentries = int(row[13])
  self.hide_dates = int(row[14])
  self.driven_mode = int(row[15])
  self.update_freq_timemode = int(row[16])
  self.init_check_app_updates = int(row[17])
  self.clear_mode = int(row[18])

  # Cargamos un par de html's...
  f = open(index_path, 'r')
  ABOUT_PAGE = f.read()
  f.close()
  f = open(puf_path, 'r')
  PUF_PAGE = f.read()
  f.close()
  
  # Valor del lock de los elementos de la ui...
  self.ui_lock = False
  # Valor del lock del botón stop...
  self.stop_feed_update_lock = False
  # Booleano indicador de si estamos o no en un proceso de feed update
  self.on_a_feed_update = False

 def save_config(self):
  """Saves user window configuration"""
  (x, y) = self.window.get_position()
  (w, h) = self.window.get_size()
  position = `x` + ',' + `y`
  size = `w` + 'x' + `h`

  # Ventana del arbol de feeds
  rect = self.scrolled_window1.get_allocation()
  (a, b) = self.scrolled_window1.get_size_request()
  a = rect.width
  scroll1 = `a` + 'x' + `b`

  # Ventana de lista de entries de cada feed
  (c, d) = self.scrolled_window2.get_size_request()
  scroll2 = `c` + 'x' + `d`

  cursor = self.conn.cursor()
  self.lock.acquire()
  cursor.execute('UPDATE config SET window_position = ?, window_size = ?, scroll1_size = ?, scroll2_size = ?, num_entries = ?, update_freq = ?, init_unfolded_tree = ?, init_tray = ?, init_update_all = ?, offline_mode = ?, show_trayicon = ?, toolbar_mode = ?, show_newentries_notification = ?, hide_readentries = ?, hide_dates = ?, driven_mode = ?, update_freq_timemode = ?, init_check_app_updates = ?, clear_mode = ?', [position,size,scroll1,scroll2,self.num_entries,self.update_freq,self.init_unfolded_tree,self.init_tray,self.init_update_all,self.offline_mode,self.show_trayicon,self.toolbar_mode,self.show_newentries_notification,self.hide_readentries,self.hide_dates,self.driven_mode,self.update_freq_timemode,self.init_check_app_updates,self.clear_mode])
  self.conn.commit()
  self.lock.release()
  cursor.close()

 def purge_entries(self):
  """Adequates excedent entries from each feed. This is called from Preferences
     dialog if the number of entries per feed has grown/shrunk."""
  updated_feed_ids = []
  s_valid = ''
  s_ghost = ''
  cursor = self.conn.cursor()
  self.lock.acquire()
  cursor.execute('SELECT id FROM feed')
  feeds = cursor.fetchall()
  self.lock.release()
  for row in feeds:
   self.lock.acquire()
   cursor.execute('SELECT id FROM articulo WHERE id_feed=? AND importante=0 ORDER BY fecha DESC LIMIT 0,?', [row[0],self.num_entries])
   row2 = cursor.fetchall()
   self.lock.release()
   if row2 is not None:
    s = ','.join(`n[0]` for n in row2)
    s_valid = s_valid + s
    updated_feed_ids.append(row[0])

   self.lock.acquire()
   cursor.execute('SELECT id FROM articulo WHERE id_feed=? AND importante=0 ORDER BY fecha DESC LIMIT ?,1000000', [row[0],self.num_entries])
   row2 = cursor.fetchall()
   self.lock.release()
   if row2 is not None:
    s = ','.join(`n[0]` for n in row2)
    s_ghost = s_ghost + s
    updated_feed_ids.append(row[0])

  self.lock.acquire()
  cursor.execute('UPDATE articulo SET ghost=0 WHERE id IN ('+s_valid+')')
  cursor.execute('UPDATE articulo SET ghost=1 WHERE id IN ('+s_ghost+')')
  self.conn.commit()
  self.lock.release()

  if len(updated_feed_ids)>0:
   self.liststore.clear()
   self.treestore.clear()
   self.scrolled_window2.set_size_request(0,0)
   self.scrolled_window2.hide()
   self.eb.hide()
   self.eb_image_zoom.hide()
   self.populate_feeds()
   self.webview.load_string(ABOUT_PAGE, "text/html", "utf-8", "file://"+index_path)
   if (self.driven_mode == 0) and (self.init_unfolded_tree == 1): self.treeview.expand_all()

 def create_main_window(self):
  """Creates the main window with all it's widgets"""
  # Creamos una ventana
  self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
  self.window.set_title("Naufrago!")
  self.window.set_icon_from_file(media_path + 'Viking_Longship.svg')
  self.window.connect("delete_event", self.delete_event)
  self.window.move(self.x, self.y)
  self.window.resize(self.w, self.h)

  ########################
  # PARTE 1 (feeds tree) #
  ########################
  # Creación del VBox.
  self.vbox = gtk.VBox(False, 0)
  # Creación del menubar
  self.create_ui(self.window)
  self.vbox.pack_start(self.ui.get_widget('/Menubar'), expand=False)
  self.toolbar = self.ui.get_widget('/Toolbar')
  # Por defecto, widget desactivado
  widget = self.ui.get_widget("/Toolbar/Stop update")
  widget.set_sensitive(False)

  self.vbox.pack_start(self.toolbar, expand=False)
  # Creación del HPaned.
  self.hpaned = gtk.HPaned()
  self.hpaned.set_border_width(2)
  # Creación del Tree izquierdo para los feeds
  # Campos: nombre, icono, id_categoria_o_feed, font-style
  self.treestore = gtk.TreeStore(str, str, int, str)
  # Create the TreeView using treestore
  self.treeview = gtk.TreeView(self.treestore)
  self.treeselection = self.treeview.get_selection()

  self.populate_feeds() # Propaga los feeds del usuario
  # Control de eventos de ratón y teclado del tree.
  self.treeview.connect("button_press_event", self.tree_button_press_event)
  self.treeview.connect("key_press_event", self.tree_key_press_event)
  self.treeview.connect("row-activated", self.tree_row_activated)
  self.treeview.connect("row-collapsed", self.tree_row_collapsed)
  self.treeview.connect("row-expanded", self.tree_row_expanded)
  self.treeselection.connect("changed", self.tree_row_selection)
  self.tvcolumn = gtk.TreeViewColumn(_("Feeds"))
  # Add tvcolumn to treeview
  self.treeview.append_column(self.tvcolumn)
  # CellRenderers para Iconos y Texto
  self.cellpb = gtk.CellRendererPixbuf()
  self.cell = gtk.CellRendererText()
  # Añadimos las cells a la tvcolumn
  self.tvcolumn.pack_start(self.cellpb, False)
  self.tvcolumn.pack_start(self.cell, True)
  if gtk.gtk_version[1] < 2:
     self.tvcolumn.set_cell_data_func(self.cellpb, self.make_pb)
  else:
     self.tvcolumn.set_attributes(self.cellpb, stock_id=1)
  self.tvcolumn.set_attributes(self.cell, text=0, font=3)
  # Allow drag and drop reordering of rows
  ###self.treeview.set_reorderable(True)
  self.treeview_setup_dnd(self.treeview)
  self.scrolled_window1 = gtk.ScrolledWindow()
  self.scrolled_window1.add(self.treeview)
  self.scrolled_window1.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
  self.scrolled_window1.set_size_request(self.a, self.b) # Sets an acceptable tree sizing
  self.hpaned.add1(self.scrolled_window1)

  ########################
  # PARTE 2 (entry list) #
  ########################
  # Creación del VPaned
  self.vpaned = gtk.VPaned()
  # Creación de los 2 elementos restantes: la lista y el browser.
  # Create a liststore
  # Campos: fecha, flag_importante, titulo, font-style, id_entry/articulo
  self.liststore = gtk.ListStore(str, bool, str, str, int)
  # Create the TreeView using liststore
  self.treeview2 = gtk.TreeView(self.liststore)
  self.treeview2.set_rules_hint(True) # differentiate rows...
  self.treeview2.connect("button_press_event", self.tree2_button_press_event)
  self.treeview2.connect("key_press_event", self.tree_key_press_event)
  self.treeselection2 = self.treeview2.get_selection()
  self.treeselection2.connect("changed", self.list_row_selection)

  # Create CellRenderers to render the data
  self.cellt = gtk.CellRendererToggle()
  self.cellt.set_property('activatable', True)
  self.cellt.connect('toggled', self.toggle_importante, self.liststore) # toggle signal capture
  self.celldate = gtk.CellRendererText()
  self.celltitle = gtk.CellRendererText()

  # Create the TreeViewColumns to display the data
  self.image = gtk.Image()
  self.image.set_from_stock(gtk.STOCK_MEDIA_RECORD, gtk.ICON_SIZE_MENU) # Record icon
  self.image.show() # Sin esto, no aparece!!! :S
  self.tvcolumn_important = gtk.TreeViewColumn(None, self.cellt)
  self.tvcolumn_important.set_widget(self.image)
  self.tvcolumn_fecha = gtk.TreeViewColumn(_('Date'), self.celldate, text=0, font=3)
  self.tvcolumn_titulo = gtk.TreeViewColumn(_('Title'), self.celltitle, text=2, font=3)
  # Append data to the liststore (not here!)
  # Add columns to treeview
  self.treeview2.append_column(self.tvcolumn_important)
  self.treeview2.append_column(self.tvcolumn_fecha)
  self.treeview2.append_column(self.tvcolumn_titulo)
  self.tvcolumn_important.add_attribute(self.cellt, "active", 1)
  # Make the treeview searchable
  self.treeview2.set_search_column(2)
  # Allow sorting on the column
  self.tvcolumn_fecha.set_sort_column_id(0)
  self.tvcolumn_important.set_sort_column_id(1)
  self.tvcolumn_titulo.set_sort_column_id(2)
  self.scrolled_window2 = gtk.ScrolledWindow()
  self.scrolled_window2.add(self.treeview2)
  self.scrolled_window2.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
  self.scrolled_window2.set_size_request(300,150) # Sets an acceptable list sizing
  #self.scrolled_window2.set_size_request(self.c, self.d) # Sets an acceptable list sizing
  self.vpaned.add1(self.scrolled_window2)

  ######################
  # PARTE 3  (browser) #
  ######################
  self.scrolled_window3 = gtk.ScrolledWindow()
  self.scrolled_window3.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
  self.webview = webkit.WebView()
  self.webview.set_full_content_zoom(True)
  self.webview.load_string(ABOUT_PAGE, "text/html", "utf-8", "file://"+index_path)
  self.webview.connect_after("populate-popup", self.create_webview_popup)
  # Open in new browser handler (this intercepts all requests)
  self.valid_links = ['valid_link', 'file://'+index_path, 'file://'+puf_path] # Valid links to browse
  for i in range(1,21):
   self.valid_links.append('file://'+puf_path+'#'+`i`)
  self.webview.connect("navigation-policy-decision-requested", self.navigation_requested)
  self.webview.connect("hovering-over-link", self.hover_link)
  self.scrolled_window3.add(self.webview)

  self.vbox2 = gtk.VBox(homogeneous=False, spacing=0)

  self.hbox = gtk.HBox(homogeneous=False, spacing=0)
  self.fullscreen = False
  self.image_zoom = gtk.Image()
  self.image_zoom.set_from_stock(gtk.STOCK_ZOOM_FIT, gtk.ICON_SIZE_MENU) # Record icon
  self.image_zoom.set_tooltip_text(_("Clic to fullscreen"))
  self.eb_image_zoom = gtk.EventBox() # Wrapper for the image to be able to catch 'button_press_event'
  self.eb_image_zoom.add(self.image_zoom)
  self.eb_image_zoom.connect("button_press_event", self.image_zoom_button_press_event)
  self.hbox.pack_start(self.eb_image_zoom, expand=False, fill=False, padding=5)

  self.headerlink = gtk.Label("")
  self.headerlink.set_tooltip_text(_("Clic to open in browser"))
  self.eb = gtk.EventBox() # Wrapper for the label to be able to catch 'button_press_event'
  self.eb.add(self.headerlink)
  self.eb.connect("button_press_event", self.headerlink_button_press_event)

  self.eb.connect("enter-notify-event", self.headerlink_mouse_enter)
  self.eb.connect("leave-notify-event", self.headerlink_mouse_leave)

  self.hbox.pack_start(self.eb, expand=True, fill=True, padding=5)
  self.vbox2.pack_start(self.hbox, expand=False, fill=False, padding=5)
  self.vbox2.pack_start(self.scrolled_window3, expand=True, fill=True, padding=0)

  self.vpaned.add2(self.vbox2)
  self.hpaned.add2(self.vpaned)
  self.vbox.pack_start(self.hpaned, True, True, 0)

  ####################################
  # PARTE 4 (statusbar & statusicon) #
  ####################################
  self.hbox2 = gtk.HBox(homogeneous=False, spacing=0)
  self.throbber = gtk.Image()
  self.throbber.set_from_file(app_path + 'media/throbber.gif')
  self.hbox2.pack_start(self.throbber, expand=False, fill=False, padding=0)
  self.statusbar = gtk.Label("")
  self.statusbar.set_justify(gtk.JUSTIFY_LEFT)
  self.statusbar.set_ellipsize(pango.ELLIPSIZE_END)
  self.statusbar.set_alignment(xalign=0.01, yalign=0)
  self.hbox2.pack_start(self.statusbar, expand=True, fill=True, padding=0)
  self.vbox.pack_start(self.hbox2, False, False, 0)

  self.window.add(self.vbox)

  # Create TrayIcon
  self.create_trayicon()
  self.window.show_all()
  self.throbber.hide()
  # The cursor change has to be done once the affected widget and its parents are shown!
  self.eb.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND2))

  # Specific hidings...
  self.eb.hide()
  self.eb_image_zoom.hide()
  self.scrolled_window2.set_size_request(0,0)
  self.scrolled_window2.hide()
  self.change_toolbar_mode(self.toolbar_mode)
  self.hide_date_column(self.hide_dates)

  if self.show_trayicon == 0: self.statusicon.set_visible(False)

  # Finally, check init options!
  self.check_init_options()

 def create_webview_popup(self, view, menu):
  """Creates the webview (browser item) popup menu."""
  zoom_in = gtk.ImageMenuItem(gtk.STOCK_ZOOM_IN)
  zoom_in.connect('activate', self.zoom_in_cb, view)
  menu.append(zoom_in)
  zoom_out = gtk.ImageMenuItem(gtk.STOCK_ZOOM_OUT)
  zoom_out.connect('activate', self.zoom_out_cb, view)
  menu.append(zoom_out)
  zoom_hundred = gtk.ImageMenuItem(gtk.STOCK_ZOOM_100)
  zoom_hundred.connect('activate', self.zoom_hundred_cb, view)
  menu.append(zoom_hundred)
  menu.show_all()
  return False

 def zoom_in_cb(self, menu_item, web_view):
  """Zoom into the page"""
  web_view.zoom_in()

 def zoom_out_cb(self, menu_item, web_view):
  """Zoom out of the page"""
  web_view.zoom_out()

 def zoom_hundred_cb(self, menu_item, web_view):
  """Zoom 100%"""
  if not (web_view.get_zoom_level() == 1.0):
   web_view.set_zoom_level(1.0)

 def navigation_requested(self, frame, request, navigation_action, policy_decision, data=None):
  """This intercepts all web requests done to the embedded webkit browser."""
  uri = navigation_action.get_uri()
  if uri in self.valid_links:
   return 0 # Let browse
  else:
   self.abrir_browser(self, uri)
   return 1 # Don't let browse

 def hover_link(self, title, uri, data=None):
  """Shows hovered link in Statusbar."""
  if data is not None:
   self.statusbar.set_text(data.encode("utf8"))
  else:
   self.statusbar.set_text('')

 def check_init_options(self):
  """Checks & applies init options."""
  if(self.init_unfolded_tree == 1): self.treeview.expand_all()
  if(self.init_tray == 1): self.statusicon_activate()
  if(self.init_check_app_updates == 1): self.check_app_updates()
  if(self.init_update_all == 1): self.update_all_feeds()

 def create_trayicon(self):
  """Creates the TrayIcon of the app and its popup menu."""
  self.statusicon = gtk.StatusIcon()
  self.statusicon.set_tooltip('Náufrago!')
  self.statusicon.set_from_file(media_path + 'Viking_Longship.svg')
  if self.show_trayicon == 1: self.statusicon.set_visible(True)
  self.window.connect('hide', self.statusicon_activate) # Hide window associated
  self.statusicon.connect('activate', self.statusicon_activate) # StatusIcon associated

  # StatusIcon popup menu
  self.statusicon_menu = gtk.Menu()
  # Create the menu items
  self.update_item = gtk.ImageMenuItem(_("Update all"))
  icon = self.update_item.render_icon(gtk.STOCK_REFRESH, gtk.ICON_SIZE_BUTTON)
  self.update_item.set_image(gtk.image_new_from_pixbuf(icon))
  self.stop_item = gtk.ImageMenuItem(_("Stop"))
  icon = self.stop_item.render_icon(gtk.STOCK_STOP, gtk.ICON_SIZE_BUTTON)
  self.stop_item.set_image(gtk.image_new_from_pixbuf(icon))
  self.quit_item = gtk.ImageMenuItem(_("Quit"))
  icon = self.quit_item.render_icon(gtk.STOCK_QUIT, gtk.ICON_SIZE_BUTTON)
  self.quit_item.set_image(gtk.image_new_from_pixbuf(icon))
  # Add them to the menu
  self.statusicon_menu.append(self.update_item)
  self.statusicon_menu.append(self.stop_item)
  self.statusicon_menu.append(self.quit_item)
  # Attach the callback functions to the activate signal
  self.update_item.connect("activate", self.update_all_feeds)
  self.stop_item.connect("activate", self.stop_feed_update)
  self.quit_item.connect("activate", self.delete_event)
  # Should we enable stop function when showing popup menu? It depends...
  if self.stop_feed_update_lock:
   self.stop_item.set_sensitive(True)
  else:
   self.stop_item.set_sensitive(False)
  self.statusicon_menu.show_all()
  self.statusicon.connect('popup-menu', self.statusicon_popup_menu)

  # Inicialización de pynotify...
  pynotify.init('Naufrago!')
  self.imageURI = 'file://' +  media_path + 'Viking_Longship.svg'

 def statusicon_popup_menu(self, statusicon, button, time):
  """StatusIcon popup menu launcher."""
  self.statusicon_menu.popup(None, None, None, button, time, self)

 def create_full_tree(self):
  """Creates the full feed tree strucure, including categories & feeds."""
  if (self.init_unfolded_tree == 1): category_icon = gtk.STOCK_OPEN
  else: category_icon = gtk.STOCK_DIRECTORY

  self.treestore.clear()
  self.treeindex = {} # A dictionary of feed iters stored by their id
  self.treeindex_cat = {} # A dictionary of category iters stored by their id
  cursor = self.conn.cursor()
  self.lock.acquire()
  cursor.execute('SELECT id,nombre FROM categoria ORDER BY nombre ASC')
  rows = cursor.fetchall()
  self.lock.release()
  for row in rows:
   boldornot = self.toggle_category_bold(row[0])
   # START: Driven mode
   if (self.driven_mode == 1):
    if boldornot == 'normal': category_icon = gtk.STOCK_DIRECTORY
    else: category_icon = gtk.STOCK_OPEN
   # END: Driven mode
   dad = self.treestore.append(None, [row[1], category_icon, row[0], boldornot]) # Initial tree creation
   self.treeindex_cat[row[0]] = dad
   self.lock.acquire()
   cursor.execute('SELECT id,nombre FROM feed WHERE id_categoria = ' + `row[0]` + ' ORDER BY nombre ASC')
   rows2 = cursor.fetchall()
   self.lock.release()
   for row2 in rows2:
    self.lock.acquire()
    cursor.execute('SELECT count(id) FROM articulo WHERE id_feed = ' + `row2[0]` + ' AND leido=0 AND ghost=0')
    row3 = cursor.fetchone()
    self.lock.release()
    if row3[0] == 0:
     feed_label = row2[1]
     font_style = 'normal'
    else:
     feed_label = row2[1] + ' [' + `row3[0]` + ']'
     font_style = 'bold'
    if os.path.exists(favicon_path + '/' + `row2[0]`):
     son = self.treestore.append(dad, [feed_label, `row2[0]`, row2[0], font_style]) # Initial tree creation
    else:
     son = self.treestore.append(dad, [feed_label, 'rss-image', row2[0], font_style]) # Initial tree creation
    self.treeindex[row2[0]] = son
   # START: Driven mode
   if (self.driven_mode == 1):
    (model, useless_iter) = self.treeselection.get_selected()
    if boldornot == 'normal':
     self.treeview.collapse_row(model.get_path(dad))
    else:
     self.treeview.expand_row(model.get_path(dad), open_all=False)
   # END: Driven mode

  self.force_gui_refresh()
  # These ones are "special" folders...
  self.add_icon_to_factory('importantes')
  self.add_icon_to_factory('no-leidos')
  self.lock.acquire()
  cursor.execute('SELECT count(id) FROM articulo WHERE importante=1 AND leido=0')
  row3 = cursor.fetchone()
  self.lock.release()
  if row3[0] == 0:
   special = self.treestore.append(None, [_("Important"), 'importantes', 9998, 'normal'])
  else:
   special = self.treestore.append(None, [_("Important")+' ['+`row3[0]`+']', 'importantes', 9998, 'bold'])
  self.lock.acquire()
  cursor.execute('SELECT count(id) FROM articulo WHERE leido=0 AND ghost=0')
  row3 = cursor.fetchone()
  self.lock.release()
  if row3[0] == 0:
   special2 = self.treestore.append(None, [_("Unread"), 'no-leidos', 9999, 'normal'])
  else:
   special2 = self.treestore.append(None, [_("Unread")+' ['+`row3[0]`+']', 'no-leidos', 9999, 'bold'])
  cursor.close()
  self.treeindex[9998] = special
  self.treeindex[9999] = special2

 def create_minimal_tree(self):
  """Creates the simplied feed tree strucure, including only feeds with unread items."""
  self.treestore.clear()
  self.treeindex = {} # A dictionary of feed iters stored by their id

  cursor = self.conn.cursor()
  self.lock.acquire()
  cursor.execute('SELECT id,nombre FROM feed ORDER BY nombre ASC')
  rows = cursor.fetchall()
  self.lock.release()
  for row2 in rows:
   self.lock.acquire()
   cursor.execute('SELECT count(id) FROM articulo WHERE id_feed = ' + `row2[0]` + ' AND leido=0 AND ghost=0')
   row3 = cursor.fetchone()
   self.lock.release()
   if row3[0] > 0:
    feed_label = row2[1] + ' [' + `row3[0]` + ']'
    font_style = 'bold'
    if os.path.exists(favicon_path + '/' + `row2[0]`):
     son = self.treestore.append(None, [feed_label, `row2[0]`, row2[0], font_style]) # Initial tree creation
    else:
     son = self.treestore.append(None, [feed_label, 'rss-image', row2[0], font_style]) # Initial tree creation
    self.treeindex[row2[0]] = son
  cursor.close()

 def populate_feeds(self):
  """Obtains the user feed tree structure"""
  self.populate_favicons() # Populate all favicons we have prior to use them
  if self.clear_mode == 1:
   self.create_minimal_tree()
  else:
   self.create_full_tree()

 def populate_entries(self, id_feed, search_request_entry_ids=None):
  """Obtains the entries of the selected feed"""
  font_style=''
  importante=False
  any_row_to_show=False
  self.liststore.clear()
  cursor = self.conn.cursor()
  if id_feed == 9998: # Important
   q = 'SELECT id,titulo,fecha,leido,importante FROM articulo WHERE importante=1 ORDER BY fecha DESC'
  elif id_feed == 9999: # Unread
   q = 'SELECT id,titulo,fecha,leido,importante FROM articulo WHERE leido=0 AND ghost=0 ORDER BY fecha DESC'
  elif search_request_entry_ids is not None: # Search
   q = 'SELECT id,titulo,fecha,leido,importante FROM articulo WHERE id IN ('+search_request_entry_ids+') AND ghost=0 ORDER BY fecha DESC'
  else: # Standard population
   q = 'SELECT id,titulo,fecha,leido,importante FROM articulo WHERE id_feed = '+`id_feed`+' AND ghost=0 ORDER BY fecha DESC'
  self.lock.acquire()
  cursor.execute(q)
  rows = cursor.fetchall()
  self.lock.release()
  cursor.close()
 
  p = re.compile(r'<[^<]*?/?>') # Removes HTML tags
  p2 = re.compile('\s{2,}') # Translate 2 o + joined whitespaces to only one
  for row in rows:
   if (not self.hide_readentries) or (self.hide_readentries and row[3] == 0) or (search_request_entry_ids is not None) or id_feed == 9998:
    now = datetime.datetime.now().strftime("%Y-%m-%d")
    fecha = datetime.datetime.fromtimestamp(row[2]).strftime("%Y-%m-%d")
    if now == fecha: fecha = _('Today')
    if row[3] == 1: font_style='normal'
    else: font_style='bold'
    if row[4] == 1: importante=True
    else: importante=False
    # We remove newlines, remove HTML tags and decode htmlentities.
    self.liststore.append([fecha, importante, self.htmlentitydecode(p2.sub('',p.sub('',row[1].replace('\n','')))), font_style, row[0]])
    any_row_to_show=True

  # Si no hay entries, no queremos su panel!
  if (rows is None) or (not any_row_to_show):
   self.scrolled_window2.set_size_request(0,0)
   self.scrolled_window2.hide()
  else:
   self.scrolled_window2.set_size_request(300,150)
   #self.scrolled_window2.set_size_request(self.c, self.d)
   self.scrolled_window2.show()

 def add_category(self, data=None):
  """Adds/edits a category to/from the user feed tree structure"""
  dialog = gtk.MessageDialog(self.window, (gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT), gtk.MESSAGE_QUESTION, gtk.BUTTONS_NONE, None)
  entry = gtk.Entry(max=128)

  if((data is not None) and (type(data) is not gtk.Action)): # Modo edición I
   cursor = self.conn.cursor()
   self.lock.acquire()
   cursor.execute('SELECT nombre FROM categoria WHERE id = ?', [data])
   nombre_categoria = cursor.fetchone()[0]
   self.lock.release()
   cursor.close()
   entry.set_text(nombre_categoria)
   dialog.set_title(_('Edit category'))
   dialog.set_markup(_('Change <b>category</b> name to:'))
   dialog.add_button(_("Edit"), gtk.RESPONSE_ACCEPT)
  else:
   dialog.set_title(_('Add category'))
   dialog.set_markup(_('Please, insert the <b>category</b>:'))
   dialog.add_button(_("Create"), gtk.RESPONSE_ACCEPT)
  dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT)

  # These are for 'capturing Enter' as OK
  dialog.set_default_response(gtk.RESPONSE_ACCEPT) # Sets default response
  entry.set_activates_default(True) # Activates default response

  dialog.vbox.pack_end(entry, True, True, 0)
  dialog.show_all()
  response = dialog.run()
  text = entry.get_text()
  dialog.destroy()

  if((text != '') and (response == gtk.RESPONSE_ACCEPT)):
   cursor = self.conn.cursor()
   # Create category in the database (if it does not exist!)
   self.lock.acquire()
   cursor.execute('SELECT id FROM categoria WHERE nombre = ?', [text.decode("utf-8")])
   row = cursor.fetchone()
   self.lock.release()
   if(row is None):
    if((data is not None) and (type(data) is not gtk.Action)): # Modo edición II
     self.lock.acquire()
     cursor.execute('SELECT nombre FROM categoria WHERE id = ?', [data])
     nombre_categoria = cursor.fetchone()[0]
     self.lock.release()
     if(text != nombre_categoria):
      (model, iter) = self.treeselection.get_selected()
      model.set(iter, 0, text)
      self.lock.acquire()
      cursor.execute('UPDATE categoria SET nombre = ? WHERE id = ?', [text.decode("utf-8"),data])
      self.conn.commit()
      self.lock.release()
    else:
     if self.clear_mode == 0: # NEW
      self.lock.acquire()
      cursor.execute('SELECT MAX(id) FROM categoria')
      row = cursor.fetchone()
      self.lock.release()
      # OLD: dad = self.alphabetical_node_insertion(text, [text, gtk.STOCK_DIRECTORY, row[0]+1, 'normal'])
      dad, useless_iter = self.alphabetical_node_insertion(text, [text, gtk.STOCK_DIRECTORY, row[0]+1, 'normal']) # NEW
      self.treeindex_cat[row[0]+1] = dad # Update category dict
     self.lock.acquire()
     cursor.execute('INSERT INTO categoria VALUES(null, ?)', [text.decode("utf-8")])
     self.conn.commit()
     self.lock.release()
   else:
    self.warning_message(_('Category <b>already present</b>!'))
   cursor.close()

 def alphabetical_node_insertion(self, nodo_a_insertar, node_data):
  """Inserts a new category in the feed list alphabetically."""
  iter = self.treestore.get_iter_root() # Magic
  if iter is not None:
   iter = self.do_comparison(nodo_a_insertar, iter)
  #self.treestore.insert_before(None, iter, node_data)
  #return iter
  # NEW
  inserted_iter = self.treestore.insert_before(None, iter, node_data)
  return iter, inserted_iter
  # NEW

 def do_comparison(self, nodo_a_insertar, iter_node_curr):
  """Recursion also does magic!"""
  node_curr = self.treestore.get_value(iter_node_curr, 0)
  id_node_curr = self.treestore.get_value(iter_node_curr, 2)
  if (id_node_curr == 9998) or (id_node_curr == 9999):
   return iter_node_curr

  res = cmp(nodo_a_insertar, node_curr)
  if res == 0: # Same strings
   return iter_node_curr
  elif res == -1: # 'categoria_a_insertar' goes before
   return iter_node_curr
  elif res == 1: # 'categoria_a_insertar' goes after
   iter = self.treestore.iter_next(iter_node_curr) # Pasamos al siguiente Padre...
   if (iter is not None):
    iter = self.do_comparison(nodo_a_insertar, iter)
    return iter
   else:
    return iter_node_curr

 def delete_category(self, data=None):
  """Deletes a category from the user feed tree structure"""
  (model, iter) = self.treeselection.get_selected()
  if(iter is not None): # Si hay algún nodo seleccionado...
   # OLD: if(model.iter_depth(iter) == 0): # ... y es un nodo padre
   if(model.iter_depth(iter) == 0) and (self.clear_mode == 0): # ... y es un nodo padre
    id_categoria = self.treestore.get_value(iter, 2)
    if(id_categoria != 1) and (id_categoria != 9998) and (id_categoria != 9999):
     dialog = gtk.MessageDialog(self.window, (gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT), gtk.MESSAGE_QUESTION, gtk.BUTTONS_OK_CANCEL, None)
     dialog.set_title(_('Delete category'))
     dialog.set_markup(_('Delete the selected <b>category</b>?'))
     dialog.format_secondary_markup(_('<b>Atention:</b> all contained RSS will be also deleted. Proceed?'))
     dialog.show_all()
     response = dialog.run()
     dialog.destroy()

     if(response == gtk.RESPONSE_OK):
      # Recuento de los no-leidos en los feeds de esta categoria
      #no_leidos = None
      #for i in range(model.iter_n_children(iter)):
      # a_child_iter = model.iter_nth_child(iter, i)
      # nombre_feed_temp = model.get_value(a_child_iter, 0)
      # (nombre_feed_temp, no_leidos_temp) = self.less_simple_name_parsing(nombre_feed_temp)
      # if no_leidos_temp is not None:
      #  no_leidos = 0
      #  no_leidos += int(no_leidos_temp)

      # De cara al model, esto es suficiente :-o
      self.treestore.remove(iter)
      del self.treeindex_cat[id_categoria] # Update category dict
      cursor = self.conn.cursor()
      self.lock.acquire()
      cursor.execute('SELECT id FROM feed WHERE id_categoria = ?', [id_categoria])
      feeds = cursor.fetchall()
      self.lock.release()
      for feed in feeds:
       del self.treeindex[feed[0]] # Update feeds dict
       if os.path.exists(favicon_path + '/'+ `feed[0]`):
        os.unlink(favicon_path + '/'+ `feed[0]`)
       self.lock.acquire()
       cursor.execute('SELECT id FROM articulo WHERE id_feed = ?', [feed[0]])
       articles = cursor.fetchall()
       self.lock.release()
       for art in articles:
        self.lock.acquire()
        cursor.execute('SELECT id,nombre FROM imagen WHERE id_articulo = ?', [art[0]])
        images = cursor.fetchall()
        self.lock.release()
        for i in images:
         self.lock.acquire()
         cursor.execute('SELECT count(id) FROM imagen WHERE nombre = ?', [i[1]])
         row3 = cursor.fetchone()
         self.lock.release()
         if (row3 is not None) and (row3[0] <= 1):
          if os.path.exists(images_path + '/'+ `i[1]`):
           os.unlink(images_path + '/'+ `i[1]`)
        self.lock.acquire()
        cursor.execute('DELETE FROM imagen WHERE id_articulo = ?', [art[0]])
        self.conn.commit()
        self.lock.release()
       self.lock.acquire()
       cursor.execute('DELETE FROM articulo WHERE id_feed = ?', [feed[0]])
       self.conn.commit()
       self.lock.release()
      self.lock.acquire()
      cursor.execute('DELETE FROM feed WHERE id_categoria = ?', [id_categoria])
      cursor.execute('DELETE FROM categoria WHERE id = ?', [id_categoria])
      self.conn.commit()
      self.lock.release()

      # Actualizamos No-leidos e Importantes
      self.update_special_folder(9999)
      self.update_special_folder(9998)

      # Finalmente ponemos las cosas en su sitio
      self.webview.load_string(ABOUT_PAGE, "text/html", "utf-8", "file://"+index_path)
      self.scrolled_window2.set_size_request(0,0)
      self.scrolled_window2.hide()
      cursor.close()
    else:
     self.warning_message(_('This category <b>cannot be deleted</b>!'))
   else:
    self.warning_message(_('You <b>must choose a category</b> folder!'))
  else:
   self.warning_message(_('You <b>must choose a category</b> folder!'))

 def add_feed(self, data=None):
  """Adds a feed to the user feed tree structure"""
  dialog = gtk.MessageDialog(self.window, (gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT), gtk.MESSAGE_QUESTION, gtk.BUTTONS_NONE, None)
  entryName = gtk.Entry(max=256)
  entryURL = gtk.Entry(max=1024)
  labelName = gtk.Label(_('Name '))

  new_feed = False
  if((data is not None) and (type(data) is not gtk.Action)): #  Modo edición I
   labelURL = gtk.Label('URL       ')
   cursor = self.conn.cursor()
   self.lock.acquire()
   cursor.execute('SELECT url,nombre FROM feed WHERE id = ?', [data])
   row = cursor.fetchone()
   self.lock.release()
   cursor.close()
   entryName.set_text(row[1])
   entryURL.set_text(row[0])
   dialog.set_title(_('Edit feed'))
   dialog.set_markup(_('Change <b>feed</b> data:'))
   dialog.add_button(_("Edit"), gtk.RESPONSE_ACCEPT)
  else:
   labelURL = gtk.Label('URL ')
   dialog.set_title(_('Add feed'))
   dialog.set_markup(_('Please, insert <b>feed</b> address:'))
   dialog.add_button(_("Add"), gtk.RESPONSE_ACCEPT)
   new_feed = True
  dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT)

  hbox1 = gtk.HBox()
  hbox1.pack_start(labelName, True, True, 0)
  hbox1.pack_start(entryName, True, True, 0)
  dialog.vbox.pack_start(hbox1, True, True, 0)
  hbox2 = gtk.HBox()
  hbox2.pack_start(labelURL, True, True, 0)
  hbox2.pack_start(entryURL, True, True, 0)
  dialog.vbox.pack_start(hbox2, True, True, 0)
  # These are for 'capturing Enter' as OK
  dialog.set_default_response(gtk.RESPONSE_ACCEPT) # Sets default response
  entryName.set_activates_default(True) # Activates default response for this entry
  entryURL.set_activates_default(True) # Activates default response for this entry
  dialog.show_all()

  if new_feed:
   labelName.hide()
   entryName.hide()

  response = dialog.run()
  textURL = entryURL.get_text()

  if((data is not None) and (type(data) is not gtk.Action)): #  Modo edición II
   textName = entryName.get_text().replace('[','(').replace(']',')')
  else:
   # Se toma un nombre temporal hasta que se obtenga el título del feed
   split = textURL.split("/")
   if len(split)>=3: textName = split[1] + split[2]
   elif len(split) == 2: textName = split[1]
   elif len(split) == 1: textName = split[0]
   else: textName = _('Default name')
  dialog.destroy()

  if((textName != '') and (textURL != '') and (response == gtk.RESPONSE_ACCEPT)):
   cursor = self.conn.cursor()
   (model, iter) = self.treeselection.get_selected()
   if((data is not None) and (type(data) is not gtk.Action)): # Modo edición III
    self.lock.acquire()
    cursor.execute('SELECT count(id) FROM articulo WHERE id_feed = ' + `data` + ' AND leido=0 AND ghost=0')
    row = cursor.fetchone()
    self.lock.release()
    if row[0] == 0:
     feed_label = textName
    else:
     feed_label = textName + ' [' + `row[0]` + ']'
    self.lock.acquire()
    cursor.execute('UPDATE feed SET nombre = ?,url = ? WHERE id = ?', [textName.decode("utf-8"),textURL.decode("utf-8"),data])
    self.conn.commit()
    self.lock.release()
    model.set(iter, 0, feed_label)
   else:
    # Create feed in the database (if it does not exist!)
    self.lock.acquire()
    cursor.execute('SELECT id FROM feed WHERE url = ?', [textURL.decode("utf-8")])
    row = cursor.fetchone()
    self.lock.release()
    if(row is None):
     id_categoria = 1 # Lo colocamos en la categoría seleccionada, o en 'General' (default) si no la hubiere
     if self.clear_mode == 0: # NEW
      if(iter is not None): # Si hay algún nodo seleccionado..
       if(model.iter_depth(iter) == 0): # ... y es un nodo padre
        id_categoria = self.treestore.get_value(iter, 2)
       elif(model.iter_depth(iter) == 1): # ... y es un nodo hijo
        iter = model.iter_parent(iter) # Cogemos al padre para usarlo como categoría destino
        id_categoria = self.treestore.get_value(iter, 2)
       else:
        iter = self.treestore.get_iter((0,)) # Hallamos el iter del nodo 'General'
      else:
       iter = self.treestore.get_iter((0,)) # Hallamos el iter del nodo 'General'

     self.lock.acquire()
     cursor.execute('SELECT MAX(id) FROM feed')
     row = cursor.fetchone()
     self.lock.release()
     id_feed = 0
     if row[0] is not None:
      id_feed = row[0]
     self.get_favicon(id_feed+1, textURL) # Downloads favicon & adds to the icon factory.
     if self.clear_mode == 0: # NEW
      son = self.treestore.append(iter, [textName, `id_feed+1`, id_feed+1, 'normal'])
     else: # NEW
      son = self.treestore.append(None, [textName, `id_feed+1`, id_feed+1, 'normal']) # NEW
     self.treeindex[id_feed+1] = son # Update feeds dict
     if self.clear_mode == 0:
      self.treeview.expand_row(model.get_path(iter), open_all=False) # Expand parent!
     self.lock.acquire()
     cursor.execute('INSERT INTO feed VALUES(null, ?, ?, ?)', [textName.decode("utf-8"),textURL.decode("utf-8"),id_categoria])
     self.conn.commit()
     self.lock.release()
     self.treeselection.select_iter(son)
     self.update_feed(data=None, new_feed=True)
    else:
     self.warning_message(_('Feed <b>already present</b>!'))
   cursor.close()

 def update_special_folder(self, id_folder):
  """Updates the total non-read entries of Unread or Non-important special folder"""
  (model, useless_iter) = self.treeselection.get_selected()
  dest_iter = self.treeindex[id_folder]
  nombre_feed_destino = model.get_value(dest_iter, 0)
  nombre_feed_destino = self.simple_name_parsing(nombre_feed_destino)
  if id_folder == 9999:
   q = 'SELECT count(id) FROM articulo WHERE leido=0 AND ghost=0'
  elif id_folder == 9998:
   q = 'SELECT count(id) FROM articulo WHERE leido=0 AND importante=1'
  cursor = self.conn.cursor()
  self.lock.acquire()
  cursor.execute(q)
  count = cursor.fetchone()[0]
  self.lock.release()
  cursor.close()
  if count is not None:
   if count > 0:
    feed_label = nombre_feed_destino + ' [' + `count` + ']'
    font_style = 'bold'
   else:
    feed_label = nombre_feed_destino
    font_style = 'normal'
  else:
   feed_label = nombre_feed_destino
   font_style = 'normal'
  model.set(dest_iter, 0, feed_label, 3, font_style)

 def delete_feed(self, data=None):
  """Deletes a feed from the user feed tree structure"""
  (model, iter) = self.treeselection.get_selected()
  if(iter is not None): # Si hay algún nodo seleccionado...
   # OLD: if(model.iter_depth(iter) == 1): # ... y es un nodo hijo
   if(model.iter_depth(iter) == 1) or (model.iter_depth(iter) == 0 and self.clear_mode == 1): # ... y es un nodo hijo
    dialog = gtk.MessageDialog(self.window, (gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT), gtk.MESSAGE_QUESTION, gtk.BUTTONS_OK_CANCEL, None)
    dialog.set_title(_('Delete feed'))
    dialog.set_markup(_('Delete selected <b>feed</b>?'))
    dialog.show_all()
    response = dialog.run()
    dialog.destroy()

    if(response == gtk.RESPONSE_OK):
     id_feed = self.treestore.get_value(iter, 2)

     cursor = self.conn.cursor()
     self.lock.acquire()
     cursor.execute('SELECT id FROM articulo WHERE id_feed = ?', [id_feed])
     articles = cursor.fetchall()
     self.lock.release()
     for art in articles:
      self.lock.acquire()
      cursor.execute('SELECT id,nombre FROM imagen WHERE id_articulo = ?', [art[0]])
      images = cursor.fetchall()
      self.lock.release()
      for i in images:
       self.lock.acquire()
       cursor.execute('SELECT count(id) FROM imagen WHERE nombre = ?', [i[1]])
       row3 = cursor.fetchone()
       self.lock.release()
       if (row3 is not None) and (row3[0] <= 1):
        if os.path.exists(images_path + '/'+ `i[1]`):
         os.unlink(images_path + '/'+ `i[1]`)
      self.lock.acquire()
      cursor.execute('DELETE FROM imagen WHERE id_articulo = ?', [art[0]])
      self.conn.commit()
      self.lock.release()
     self.lock.acquire()
     cursor.execute('DELETE FROM articulo WHERE id_feed = ?', [id_feed])
     cursor.execute('DELETE FROM feed WHERE id = ?', [id_feed])
     self.conn.commit()
     self.lock.release()
     cursor.close()
     if os.path.exists(favicon_path + '/'+ `id_feed`):
      os.unlink(favicon_path + '/'+ `id_feed`)

     if self.clear_mode == 0: # NEW
      # Unbold category if needed.
      self.toggle_category_bold()

     self.treestore.remove(iter)
     del self.treeindex[id_feed] # Update feeds dict
     self.liststore.clear() # Limpieza de tabla de entries/articulos

     if self.clear_mode == 0: # NEW
      # Actualizamos No-leidos e Importantes
      self.update_special_folder(9999)
      self.update_special_folder(9998)

     # Finalmente ponemos las cosas en su sitio
     self.webview.load_string(ABOUT_PAGE, "text/html", "utf-8", "file://"+index_path)
     self.scrolled_window2.set_size_request(0,0)
     self.scrolled_window2.hide()
   else:
    self.warning_message(_('You <b>must choose a feed</b>!'))
  else:
   self.warning_message(_('You <b>must choose a feed</b>!'))

 def delete(self, data=None):
  """Summons deleting feed or category, depending on selection."""
  (model, iter) = self.treeselection.get_selected()
  if(iter is not None): # Si hay algún nodo seleccionado...
   # OLD: if(model.iter_depth(iter) == 0): # Si es un nodo padre...
   if(model.iter_depth(iter) == 0 and self.clear_mode == 0): # Si es un nodo padre...
    self.delete_category()
   else: # ... y es un nodo hijo
    self.delete_feed()

 def edit(self, data=None):
  """Edits a tree node, whether it is root or leaf."""
  (model, iter) = self.treeselection.get_selected()
  if(iter is not None): # Si hay algún nodo seleccionado...
   id_categoria_o_feed = model.get_value(iter, 2)
   # OLD: if(model.iter_depth(iter) == 0): # ... y es un nodo padre
   if(model.iter_depth(iter) == 0 and self.clear_mode == 0): # ... y es un nodo padre
    if(id_categoria_o_feed != 1) and (id_categoria_o_feed != 9998) and (id_categoria_o_feed != 9999):
     self.add_category(id_categoria_o_feed)
    else:
     self.warning_message(_('This category <b>cannot be edited</b>!'))
   else: # ... y es un nodo hijo
    self.add_feed(id_categoria_o_feed)
  else:
   self.warning_message(_('You <b>must choose a category or a feed</b> to edit!'))

 def search(self, data=None):
  """Searches for a keyword on a given feed (or all, if no one is selected)."""
  dialog = gtk.MessageDialog(self.window, (gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT), gtk.MESSAGE_QUESTION, gtk.BUTTONS_NONE, None)
  dialog.add_button(_("Search"), gtk.RESPONSE_ACCEPT)
  dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT)

  dialog.set_title(_('Search'))
  dialog.set_markup(_('Insert the <b>searchterm</b>:'))
  entry = gtk.Entry(max=128)
  dialog.set_default_response(gtk.RESPONSE_ACCEPT) # Sets default response
  entry.set_activates_default(True) # Activates default response
  dialog.vbox.pack_end(entry, True, True, 0)
  dialog.show_all()
  response = dialog.run()
  text = entry.get_text()
  dialog.destroy()

  if((text != '') and (response == gtk.RESPONSE_ACCEPT)):
   self.on_a_search = True # NEW (flag that points out that we did a search)
   self.throbber.show()
   self.treeselection.unselect_all()

   cursor = self.conn.cursor()
   self.lock.acquire()
   cursor.execute("SELECT id FROM articulo WHERE titulo LIKE '%"+text+"%' OR contenido LIKE '%"+text+"%' AND ghost=0")
   row = cursor.fetchall()
   self.lock.release()
   cursor.close()
   entry_ids = ''
   if (row is not None) and (len(row)>0):
    for id_articulo in row:
     entry_ids += `id_articulo[0]` + ','
    entry_ids = entry_ids[0:-1]

    self.scrolled_window2.set_size_request(300,150)
    #self.scrolled_window2.set_size_request(self.c, self.d)
    self.scrolled_window2.show()
    self.populate_entries(123456, entry_ids) # Invented feed_id since we don't need any here...
    self.webview.load_string("<h2>" + _("Search results for") + ": "+ text + "</h2>", "text/html", "utf-8", "valid_link")
   else:
    self.warning_message(_('No entry found for <b>'+text+'</b>.'))

   self.throbber.hide()

 def change_toolbar_mode(self, toolbar_mode):
  """Changes the toolbar style."""
  if toolbar_mode == 0:
   self.toolbar.set_style(gtk.TOOLBAR_BOTH)
   self.toolbar.show()
  elif toolbar_mode == 1:
   self.toolbar.set_style(gtk.TOOLBAR_ICONS)
   self.toolbar.show()
  elif toolbar_mode == 2:
   self.toolbar.set_style(gtk.TOOLBAR_TEXT)
   self.toolbar.show()
  elif toolbar_mode == 3:
   self.toolbar.hide()

 def change_toolbar_mode_cb(self, combobox):
  """Changes the toolbar style: callback."""
  toolbar_mode = combobox.get_active()
  if toolbar_mode == 0:
   self.toolbar.set_style(gtk.TOOLBAR_BOTH)
   self.toolbar.show()
  elif toolbar_mode == 1:
   self.toolbar.set_style(gtk.TOOLBAR_ICONS)
   self.toolbar.show()
  elif toolbar_mode == 2:
   self.toolbar.set_style(gtk.TOOLBAR_TEXT)
   self.toolbar.show()
  elif toolbar_mode == 3:
   self.toolbar.hide()

 def change_timemode(self, aux):
  """Restores the time (hour/min) of feeds update."""
  self.update_freq_timemode = aux

 def change_timemode_cb(self, combobox2):
  """Changes the time (hour/min) of feeds update."""
  time_mode = combobox2.get_active()
  if time_mode == 0:
   self.update_freq_timemode = 0 # hour
  else:
   self.update_freq_timemode = 1 # min

 def trayicon_toggle_cb(self, checkboxparent, checkboxchild):
  """Controlls the linked trayicon checkboxes of the preferences dialog."""
  if checkboxparent.get_active():
   checkboxchild.set_sensitive(True)
   self.show_trayicon = 1
   self.statusicon.set_visible(True)
  else:
   checkboxchild.set_active(False)
   checkboxchild.set_sensitive(False)
   self.show_trayicon = 0
   self.statusicon.set_visible(False)

 def hide_read_entries(self, aux_hide_readentries):
  """Restores the state of the read entry hidding of the preferences dialog."""
  self.hide_readentries = aux_hide_readentries
  (model, iter) = self.treeselection.get_selected()
  if(iter is not None): # Si hay algún nodo seleccionado...
   # OLD: if(model.iter_depth(iter) == 1): # ... y es un nodo hijo (o sea, un feed)
   if model.iter_depth(iter) == 1 or (model.iter_depth(iter) == 0 and self.clear_mode == 1): # ... y es un nodo hijo (o sea, un feed)
    id_selected_feed = self.treestore.get_value(iter, 2)
    self.populate_entries(id_selected_feed)

 def hide_read_entries_cb(self, checkbox):
  """Controlls the read entry hidding of the preferences dialog."""
  (model, iter) = self.treeselection.get_selected()
  if(iter is not None): # Si hay algún nodo seleccionado...
   # OLD: if(model.iter_depth(iter) == 1): # ... y es un nodo hijo (o sea, un feed)
   if model.iter_depth(iter) == 1 or (model.iter_depth(iter) == 0 and self.clear_mode == 1): # ... y es un nodo hijo (o sea, un feed)
    if checkbox.get_active(): self.hide_readentries = 1
    else: self.hide_readentries = 0
    id_selected_feed = self.treestore.get_value(iter, 2)
    self.populate_entries(id_selected_feed)

 def hide_date_column(self, aux_hide_dates):
  """Restores the state of date column hidding of the preferences dialog."""
  self.hide_dates = aux_hide_dates
  if self.hide_dates == 1: self.tvcolumn_fecha.set_visible(False)
  else: self.tvcolumn_fecha.set_visible(True)

 def hide_date_column_cb(self, checkbox):
  """Controlls the date column hidding of the preferences dialog."""
  if checkbox.get_active():
   self.hide_dates = 1
   self.tvcolumn_fecha.set_visible(False)
  else:
   self.hide_dates = 0
   self.tvcolumn_fecha.set_visible(True)

 def driven_mode_action(self):
  """Collapse or expands parent nodes based on unread items within its feeds."""
  (model, useless_iter) = self.treeselection.get_selected() # We only want the model here...
  useless_iter_parent = None
  useless_iter_id_cat = None
  if type(useless_iter) is gtk.TreeIter:
   useless_iter_parent = model.iter_parent(useless_iter)
   if type(useless_iter_parent) is gtk.TreeIter:
    useless_iter_id_cat = model.get_value(useless_iter_parent, 2)

  iter = model.get_iter_root() # Magic
  id_cat = model.get_value(iter, 2)
  while (iter is not None):
   # OLD: if(model.iter_depth(iter) == 0) and (id_cat != 9998 and id_cat != 9999): # Si es padre
   if(model.iter_depth(iter) == 0) and (self.clear_mode == 0) and (id_cat != 9998 and id_cat != 9999): # Si es padre
    boldornot = model.get_value(iter, 3)
    if boldornot == 'normal':
     if (self.driven_mode == 1) and (useless_iter_id_cat is not None):
      if id_cat == useless_iter_id_cat:
       q = 'SELECT count(articulo.id) FROM articulo, feed, categoria WHERE articulo.leido=0 AND articulo.ghost=0 AND categoria.id='+`id_cat`+' AND articulo.id_feed=feed.id AND feed.id_categoria=categoria.id'
       cursor = self.conn.cursor()
       self.lock.acquire()
       cursor.execute(q)
       row = cursor.fetchone()
       self.lock.release()
       cursor.close()
       if (row is not None) and (row[0] == 0):
        # Esconder la lista de feeds y mostrar en el navegador los datos de la categoría
        self.liststore.clear() # Limpieza de tabla de entries/articulos
        self.scrolled_window2.set_size_request(0,0)
        self.scrolled_window2.hide()
        self.webview.load_string("<h2>"+_("Category")+": "+model.get_value(useless_iter_parent, 0)+"</h2>", "text/html", "utf-8", "valid_link")
        self.eb.hide()
        self.eb_image_zoom.hide()

     self.treeview.collapse_row(model.get_path(iter))
    elif boldornot == 'bold':
     self.treeview.expand_row(model.get_path(iter), open_all=False)
   iter = self.treestore.iter_next(iter) # Pasamos al siguiente Padre.. 
   if iter is not None:
    id_cat = model.get_value(iter, 2)

 def unfolded_or_driven_toggle(self, aux_init_unfolded_tree, aux_driven_mode, aux_clear_mode, hbox_throbber1, hbox_throbber2):
  """Restores the state of the linked checkboxes unfolded_tree and driven_mode."""
  hbox_throbber1.show()
  hbox_throbber2.show()
  self.force_gui_refresh()
  if (aux_init_unfolded_tree == 1) and (self.init_unfolded_tree == 0):
   self.init_unfolded_tree = 1
   self.driven_mode = 0
   self.clear_mode = 0
   self.create_full_tree()
   self.treeview.expand_all()

  elif (aux_driven_mode == 1) and (self.driven_mode == 0):
   self.init_unfolded_tree = 0
   self.driven_mode = 1
   self.clear_mode = 0
   self.create_full_tree()
   self.force_gui_refresh()
   self.driven_mode_action()

  elif (aux_clear_mode == 1) and (self.clear_mode == 0):
   self.init_unfolded_tree = 0
   self.driven_mode = 0
   self.clear_mode = 1
   self.create_minimal_tree()

  else:
   self.treeview.collapse_all()

  hbox_throbber1.hide()
  hbox_throbber2.hide()

 def unfolded_or_driven_toggle_cb(self, checkboxparent, checkboxchild1, checkboxchild2, caller_id, hbox_throbber):
  """Controlls the linked checkboxes unfolded_tree, driven_mode and clear_mode."""
  hbox_throbber.show()
  self.force_gui_refresh()
  if checkboxparent.get_active():
   checkboxchild1.set_active(False)
   checkboxchild2.set_active(False)
   if caller_id == 1:
    self.create_full_tree()
    self.init_unfolded_tree = 1
    self.driven_mode = 0
    self.clear_mode = 0
    self.treeview.expand_all()
   elif caller_id == 2:
    self.create_full_tree()
    self.init_unfolded_tree = 0
    self.driven_mode = 1
    self.clear_mode = 0
    self.driven_mode_action()
   elif caller_id == 3:
    self.create_minimal_tree()
    self.init_unfolded_tree = 0
    self.driven_mode = 0
    self.clear_mode = 1

  else:
   if caller_id == 1:
    self.init_unfolded_tree = 0
   elif caller_id == 2:
    self.driven_mode = 0
   elif caller_id == 3:
    self.clear_mode = 0
    self.create_full_tree()
   self.treeview.collapse_all()
  hbox_throbber.hide()

 def force_gui_refresh(self):
  """Forces updates to the application windows during a long callback or other internal operation."""
  # Found at: http://faq.pygtk.org/index.py?req=show&file=faq03.007.htp
  while gtk.events_pending():
   gtk.main_iteration(False)

 def progress_factory(self):
  """It is a factory of progress items (to avoid duplicating objects; pygtk doesn't like!)."""
  # Progress element present in some tabs...
  hbox_throbber = gtk.HBox()
  label = gtk.Label(_("Applying changes..."))
  progress = gtk.Image()
  progress.set_from_file(app_path + 'media/clock.png')
  hbox_throbber.pack_start(progress, False, False, 3)
  hbox_throbber.pack_start(label, False, False, 3)
  return hbox_throbber

 def preferences(self, data=None):
  """Preferences dialog."""
  dialog = gtk.Dialog(_("Preferences"), self.window, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, None)
  dialog.add_button(_("Save"), gtk.RESPONSE_ACCEPT)
  dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT)

  dialog.set_size_request(300,250)
  dialog.set_border_width(2)
  dialog.set_resizable(True)
  dialog.set_has_separator(False)
 
  notebook = gtk.Notebook()
  notebook.set_tab_pos(gtk.POS_TOP)

  # Tab 1
  vbox2 = gtk.VBox(homogeneous=True)
  align = gtk.Alignment()
  align.set_padding(10, 0, 15, 0)
  checkbox = gtk.CheckButton(_("Start with unfolded tree"))
  aux_init_unfolded_tree = self.init_unfolded_tree
  if(self.init_unfolded_tree == 1) and (self.driven_mode == 0): checkbox.set_active(True)
  else: checkbox.set_active(False)
  checkbox8 = gtk.CheckButton(_("Driven mode"))
  checkbox10 = gtk.CheckButton(_("Clear mode"))
  hbox_throbber1 = self.progress_factory()
  checkbox.connect('toggled', self.unfolded_or_driven_toggle_cb, checkbox8, checkbox10, 1, hbox_throbber1)
  vbox2.pack_start(checkbox, True, True, 5)
  checkbox2 = gtk.CheckButton(_("Start in Tray Icon"))
  if self.show_trayicon == 1:
   if self.init_tray == 1: checkbox2.set_active(True)
   else: checkbox2.set_active(False)
  else:
   checkbox2.set_active(False)
   checkbox2.set_sensitive(False)
  vbox2.pack_start(checkbox2, True, True, 5)
  checkbox3 = gtk.CheckButton(_("Update on start"))
  if(self.init_update_all == 1): checkbox3.set_active(True)
  else: checkbox3.set_active(False)
  vbox2.pack_start(checkbox3, True, True, 5)
  checkbox9 = gtk.CheckButton(_("Check application updates on start"))
  if(self.init_check_app_updates == 1): checkbox9.set_active(True)
  else: checkbox9.set_active(False)
  vbox2.pack_start(checkbox9, True, True, 5)
  vbox2.pack_start(hbox_throbber1, True, True, 5)
  align.add(vbox2)
  notebook.append_page(align, gtk.Label(_("Start")))

  # Tab 2
  vbox3 = gtk.VBox(homogeneous=True)
  align2 = gtk.Alignment()
  align2.set_padding(10, 0, 15, 0)
  hbox = gtk.HBox()
  label = gtk.Label(_("Number of feed entries"))
  hbox.pack_start(label, True, True, 2)
  # Spin button
  adjustment = gtk.Adjustment(value=10, lower=10, upper=1000, step_incr=10, page_incr=10, page_size=0)
  spin_button = gtk.SpinButton(adjustment=adjustment, climb_rate=0.0, digits=0)
  spin_button.set_numeric(numeric=True) # Only numbers can be typed
  spin_button.set_update_policy(gtk.UPDATE_IF_VALID) # Only update on valid changes
  spin_button.set_value(self.num_entries)
  hbox.pack_start(spin_button, True, True, 2)
  vbox3.pack_start(hbox, True, True, 5)
  hbox2 = gtk.HBox()
  label2 = gtk.Label(_("Update every"))
  hbox2.pack_start(label2, True, True, 2)
  # Spin button 2
  adjustment2 = gtk.Adjustment(value=1, lower=1, upper=60, step_incr=1, page_incr=1, page_size=0)
  spin_button2 = gtk.SpinButton(adjustment=adjustment2, climb_rate=0.0, digits=0)
  spin_button2.set_numeric(numeric=True) # Only numbers can be typed
  spin_button2.set_update_policy(gtk.UPDATE_IF_VALID) # Only update on valid changes
  spin_button2.set_value(self.update_freq)
  hbox2.pack_start(spin_button2, True, True, 2)
  aux_update_freq_timemode = self.update_freq_timemode
  combobox2 = gtk.combo_box_new_text()
  combobox2.append_text(_("hour/s"))
  combobox2.append_text(_("minute/s"))
  combobox2.set_active(self.update_freq_timemode)
  combobox2.connect('changed', self.change_timemode_cb)
  hbox2.pack_start(combobox2, True, True, 2)
  vbox3.pack_start(hbox2, True, True, 5)
  checkbox6 = gtk.CheckButton(_("Hide read entries"))
  aux_hide_readentries = self.hide_readentries # Aux var to remember original state
  if(self.hide_readentries == 1): checkbox6.set_active(True)
  else: checkbox6.set_active(False)
  checkbox6.connect('toggled', self.hide_read_entries_cb)
  vbox3.pack_start(checkbox6, True, True, 5)
  align2.add(vbox3)
  notebook.append_page(align2, gtk.Label(_("Feeds & articles")))

  # Tab 3
  vbox4 = gtk.VBox(homogeneous=True)
  align3 = gtk.Alignment()
  align3.set_padding(10, 0, 15, 0)
  checkbox7 = gtk.CheckButton(_("Hide dates"))
  aux_hide_dates = self.hide_dates # Aux var to remember original state
  if(self.hide_dates == 1): checkbox7.set_active(True)
  else: checkbox7.set_active(False)
  checkbox7.connect('toggled', self.hide_date_column_cb)
  vbox4.pack_start(checkbox7, True, True, 5)
  checkbox5 = gtk.CheckButton(_("Notification on new entries"))
  if(self.show_newentries_notification == 1): checkbox5.set_active(True)
  else: checkbox5.set_active(False)
  vbox4.pack_start(checkbox5, True, True, 5)
  checkbox1 = gtk.CheckButton(_("Show icon in tray"))
  aux_show_trayicon = self.show_trayicon # Aux var to remember original state
  if(self.show_trayicon == 1): checkbox1.set_active(True)
  else: checkbox1.set_active(False)
  checkbox1.connect('toggled', self.trayicon_toggle_cb, checkbox2)
  vbox4.pack_start(checkbox1, True, True, 5)
  hbox3 = gtk.HBox()
  label3 = gtk.Label(_("Toolbar mode"))
  hbox3.pack_start(label3, True, True, 2)
  combobox = gtk.combo_box_new_text()
  combobox.append_text(_("Full"))
  combobox.append_text(_("Icons only"))
  combobox.append_text(_("Text only"))
  combobox.append_text(_("Hidden"))
  combobox.set_active(self.toolbar_mode)
  combobox.connect('changed', self.change_toolbar_mode_cb)
  hbox3.pack_start(combobox, True, True, 2)
  vbox4.pack_start(hbox3, True, True, 5)
  align3.add(vbox4)
  notebook.append_page(align3, gtk.Label(_("Interface")))

  # Tab 4
  vbox5 = gtk.VBox(homogeneous=True)
  align4 = gtk.Alignment()
  align4.set_padding(10, 0, 15, 0)
  checkbox0 = gtk.CheckButton(_("Offline mode (slower!)"))
  if(self.offline_mode == 1): checkbox0.set_active(True)
  else: checkbox0.set_active(False)
  vbox5.pack_start(checkbox0, True, True, 5)
  aux_driven_mode = self.driven_mode
  if(self.driven_mode == 1) and (self.clear_mode == 0) and (self.init_unfolded_tree == 0): checkbox8.set_active(True)
  else: checkbox8.set_active(False)
  hbox_throbber2 = self.progress_factory()
  checkbox8.connect('toggled', self.unfolded_or_driven_toggle_cb, checkbox, checkbox10, 2, hbox_throbber2)
  vbox5.pack_start(checkbox8, True, True, 5)
  # NEW
  aux_clear_mode = self.clear_mode
  if(self.clear_mode == 1) and (self.driven_mode == 0) and (self.init_unfolded_tree == 0): checkbox10.set_active(True)
  else: checkbox10.set_active(False)
  checkbox10.connect('toggled', self.unfolded_or_driven_toggle_cb, checkbox, checkbox8, 3, hbox_throbber2)
  vbox5.pack_start(checkbox10, True, True, 5)
  vbox5.pack_start(hbox_throbber2, False, False, 5)
  # NEW
  align4.add(vbox5)
  notebook.append_page(align4, gtk.Label(_("Modes")))

  dialog.vbox.pack_start(notebook)
  dialog.show_all()
  hbox_throbber1.hide()
  hbox_throbber2.hide()
  response = dialog.run() # Dialog loop
  dialog.destroy()

  if(response == gtk.RESPONSE_ACCEPT):
   # Adequate entries in case of increasing/decreasing their number in configuration
   num_entries_prev = self.num_entries
   self.num_entries = spin_button.get_value_as_int()
   if self.num_entries < num_entries_prev:
    self.purge_entries()
   self.update_freq = spin_button2.get_value_as_int()

   if combobox.get_active() != self.toolbar_mode:
    self.toolbar_mode = combobox.get_active()
    self.change_toolbar_mode(self.toolbar_mode)

   if(checkbox0.get_active()): self.offline_mode = 1
   else: self.offline_mode = 0
   if(checkbox.get_active()): self.init_unfolded_tree = 1
   else: self.init_unfolded_tree = 0
   if(checkbox2.get_active()): self.init_tray = 1
   else: self.init_tray = 0
   if(checkbox3.get_active()): self.init_update_all = 1
   else: self.init_update_all = 0
   if(checkbox5.get_active()): self.show_newentries_notification = 1
   else: self.show_newentries_notification = 0
   if(checkbox6.get_active()): self.hide_readentries = 1
   else: self.hide_readentries = 0
   if(checkbox7.get_active()): self.hide_dates = 1
   else: self.hide_dates = 0
   if(checkbox8.get_active()): self.driven_mode = 1
   else: self.driven_mode = 0
   if(checkbox9.get_active()): self.init_check_app_updates = 1
   else: self.init_check_app_updates = 0

   if checkbox1.get_active() and self.show_trayicon == 0:
    self.show_trayicon = 1
    self.statusicon.set_visible(True)
   elif not checkbox1.get_active() and self.show_trayicon == 1:
    self.show_trayicon = 0
    self.statusicon.set_visible(False)
   self.save_config()

  else: # Restore things back...
   self.change_toolbar_mode(self.toolbar_mode)
   self.change_timemode(aux_update_freq_timemode)
   self.statusicon.set_visible(aux_show_trayicon)
   self.show_trayicon = aux_show_trayicon
   self.hide_read_entries(aux_hide_readentries)
   self.hide_date_column(aux_hide_dates)
   self.unfolded_or_driven_toggle(aux_init_unfolded_tree, aux_driven_mode, aux_clear_mode, hbox_throbber1, hbox_throbber2)

 def treeview_copy_row(self, treeview, model, source, target, drop_position):
  """Copy tree model rows from treeiter source into, before or after treeiter target.
  All children of the source row are also copied and the
  expanded/collapsed status of each row is maintained."""
  source_row = model[source]
  cursor = self.conn.cursor()
  if drop_position == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE:
   #print '---Prepend---'
   new = model.prepend(parent=target, row=source_row)
  elif drop_position == gtk.TREE_VIEW_DROP_INTO_OR_AFTER:
   #print '---Append---'
   new = model.append(parent=target, row=source_row)
  #elif drop_position == gtk.TREE_VIEW_DROP_BEFORE:
  # new = model.insert_before(parent=None, sibling=target, row=source_row)
  #elif drop_position == gtk.TREE_VIEW_DROP_AFTER:
  # new = model.insert_after(parent=None, sibling=target, row=source_row)
  parent_value = `model.get_value(target, 0)`
  row_value = `model.get_value(source_row.iter, 0)`
  row_value = self.simple_name_parsing(row_value)
  self.lock.acquire()
  cursor.execute('UPDATE feed SET id_categoria = (SELECT id FROM categoria WHERE nombre = ?) WHERE id = (SELECT id FROM feed WHERE nombre = ?)', [parent_value.decode("utf-8"),row_value.decode("utf-8")])
  self.conn.commit()
  self.lock.release()
  cursor.close()

  # If the source row is expanded, expand the newly copied row
  # also.  We must add at least one child before we can expand,
  # so we expand here after the children have been copied.
  source_is_expanded = treeview.row_expanded(model.get_path(source))
  if source_is_expanded:
   #self.treeview_expand_to_path(treeview, model.get_path(new))
   self.treeview.expand_row(model.get_path(new), open_all=False)

 def checkSanity(self, model, iter_to_copy, target_iter):
  """Prevents that a node can be copied inside himself (anti-recursivity!),
  and also checks for application node logic."""

  #iter_to_copy_value = model.get_value(iter_to_copy, 0)
  #target_iter_value = model.get_value(target_iter, 0)
  target_iter_id = model.get_value(target_iter, 2)

  path_of_iter_to_copy = model.get_path(iter_to_copy)
  path_of_target_iter = model.get_path(target_iter)

  if((path_of_target_iter[0:len(path_of_iter_to_copy)] == path_of_iter_to_copy) or # anti-recursive
    (len(path_of_iter_to_copy) == 1) or # source is parent
    (len(path_of_target_iter) == 2) or # dest is child
    (self.treestore.is_ancestor(target_iter, iter_to_copy)) or # dest is already child's parent
    (target_iter_id == 9998) or (target_iter_id == 9999) or # dest is a special folder
    (self.clear_mode == 1)): # NEW: clear_mode doesn't allow this
     return False
  else:
   return True

 def treeview_on_drag_data_received(self, treeview, drag_context, x, y, selection_data, info, eventtime):
  """Handler for 'drag-data-received' that moves dropped TreeView rows."""
  model, source = treeview.get_selection().get_selected()
  # Workaround for DnD at the end of the tree.
  temp = treeview.get_dest_row_at_pos(x, y)
  if temp != None:
   target_path, drop_position = temp
  else:
   target_path, drop_position = (len(model)-1,), gtk.TREE_VIEW_DROP_AFTER

  target = model.get_iter(target_path)
  if self.checkSanity(model, source, target):
   self.treeview_copy_row(treeview, model, source, target, drop_position)
   # If the drop has created a new child (drop into), expand
   # the parent so the user can see the newly copied row.
   if(drop_position == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE or drop_position == gtk.TREE_VIEW_DROP_INTO_OR_AFTER):
    treeview.expand_row(target_path, open_all=False)
    # Finish the drag and have gtk+ delete the drag source rows.
    drag_context.finish(success=True, del_=True, time=eventtime)
   else:
    drag_context.finish(success=False, del_=False, time=eventtime)
   # Some cleaning...
   self.liststore.clear()
   self.eb.hide()
   self.eb_image_zoom.hide()
   self.webview.load_string(ABOUT_PAGE, "text/html", "utf-8", "file://"+index_path)
   self.scrolled_window2.set_size_request(0,0)
   self.scrolled_window2.hide()

 def treeview_setup_dnd(self, treeview):
  """Setup a treeview to move rows using drag and drop."""
  target_entries = [('example', gtk.TARGET_SAME_WIDGET, 0)]
  # target_entries=[(drag type string, target_flags, application integer ID used for identification purposes)]
  # Drag start operation (origin)
  treeview.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, target_entries, gtk.gdk.ACTION_MOVE)
  # Params: 1st mouse button, target_entries (ver arriba), type of action to do
  # Drag end operation (destination)
  treeview.enable_model_drag_dest(target_entries, gtk.gdk.ACTION_MOVE)
  # Params: target_entries (ver arriba), type of action to do
  treeview.connect('drag-data-received', self.treeview_on_drag_data_received)

 def tree_button_press_event(self, treeview, event):
  """Fires the tree menu popup. This handles the feed list options.
  Showing feed entries is handled through *tree_row_selection* handler
  callbacked by the *change* event."""

  if event.button == 3:
   x = int(event.x)
   y = int(event.y)
   pthinfo = treeview.get_path_at_pos(x, y)
   if pthinfo is not None:
    path, col, cellx, celly = pthinfo
    treeview.grab_focus()
    treeview.set_cursor(path, col, 0)

    (model, iter) = self.treeselection.get_selected()
    id = model.get_value(iter, 2)

    tree_menu = gtk.Menu()
    # Create the menu items
    toggle_todos_leido_item = gtk.ImageMenuItem(_("Mark all as read"))
    icon = toggle_todos_leido_item.render_icon(gtk.STOCK_SELECT_ALL, gtk.ICON_SIZE_BUTTON)
    toggle_todos_leido_item.set_image(gtk.image_new_from_pixbuf(icon))

    if (id != 9998) and (id != 9999):
     update_item = gtk.ImageMenuItem(_("Update"))
     icon = update_item.render_icon(gtk.STOCK_REFRESH, gtk.ICON_SIZE_BUTTON)
     update_item.set_image(gtk.image_new_from_pixbuf(icon))
     if self.ui_lock: update_item.set_sensitive(False)

     edit_item = gtk.ImageMenuItem(_("Edit"))
     icon = edit_item.render_icon(gtk.STOCK_EDIT, gtk.ICON_SIZE_BUTTON)
     edit_item.set_image(gtk.image_new_from_pixbuf(icon))
     if self.ui_lock: edit_item.set_sensitive(False)

     delete_item = gtk.ImageMenuItem(_("Delete"))
     icon = delete_item.render_icon(gtk.STOCK_CLOSE, gtk.ICON_SIZE_BUTTON)
     delete_item.set_image(gtk.image_new_from_pixbuf(icon))
     if self.ui_lock: delete_item.set_sensitive(False)

     separator = gtk.SeparatorMenuItem()
     new_feed_item = gtk.ImageMenuItem(_("New feed"))
     icon = new_feed_item.render_icon(gtk.STOCK_FILE, gtk.ICON_SIZE_BUTTON)
     new_feed_item.set_image(gtk.image_new_from_pixbuf(icon))
     new_category_item = gtk.ImageMenuItem(_("New category"))
     icon = new_category_item.render_icon(gtk.STOCK_DIRECTORY, gtk.ICON_SIZE_BUTTON)
     new_category_item.set_image(gtk.image_new_from_pixbuf(icon))

    # Add them to the menu
    tree_menu.append(toggle_todos_leido_item)
    if (id != 9998) and (id != 9999):
     tree_menu.append(update_item)
     tree_menu.append(edit_item)
     tree_menu.append(delete_item)
     tree_menu.append(separator)
     tree_menu.append(new_feed_item)
     tree_menu.append(new_category_item)

    # Attach the callback functions to the activate signal
    if (id != 9998) and (id != 9999):
     toggle_todos_leido_item.connect("activate", self.toggle_leido, 'tree')
     update_item.connect_object("activate", self.update_feed, None)
     edit_item.connect_object("activate", self.edit, None)
     delete_item.connect_object("activate", self.delete, None)
     new_feed_item.connect_object("activate", self.add_feed, None)
     new_category_item.connect_object("activate", self.add_category, None)
    else:
     toggle_todos_leido_item.connect("activate", self.toggle_leido, 'tree')

    tree_menu.show_all()
    tree_menu.popup(None, None, None, event.button, event.get_time())

   return True

 def tree2_button_press_event(self, treeview, event):
  """Fires the tree2 menu popup. This one handles entries options."""
  if event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
   self.abrir_browser()
  elif event.button == 3:
   x = int(event.x)
   y = int(event.y)
   pthinfo = treeview.get_path_at_pos(x, y)
   if pthinfo is not None:
    path, col, cellx, celly = pthinfo
    treeview.grab_focus()
    treeview.set_cursor(path, col, 0)

    tree_menu = gtk.Menu()
    # Create the menu items
    abrir_browser_item = gtk.MenuItem(_("Open in browser"))
    copiar_portapapeles_item = gtk.ImageMenuItem(_("Copy URL to clipboard"))
    icon = copiar_portapapeles_item.render_icon(gtk.STOCK_PASTE, gtk.ICON_SIZE_BUTTON)
    copiar_portapapeles_item.set_image(gtk.image_new_from_pixbuf(icon))
    toggle_leido_item = gtk.ImageMenuItem(_("Toggle read/non-read"))
    icon = toggle_leido_item.render_icon(gtk.STOCK_INDEX, gtk.ICON_SIZE_BUTTON)
    toggle_leido_item.set_image(gtk.image_new_from_pixbuf(icon))
    toggle_todos_leido_item = gtk.ImageMenuItem(_("Toggle all read/non-read"))
    icon = toggle_todos_leido_item.render_icon(gtk.STOCK_SELECT_ALL, gtk.ICON_SIZE_BUTTON)
    toggle_todos_leido_item.set_image(gtk.image_new_from_pixbuf(icon))
    # Add them to the menu
    tree_menu.append(abrir_browser_item)
    tree_menu.append(copiar_portapapeles_item)
    tree_menu.append(toggle_leido_item)
    tree_menu.append(toggle_todos_leido_item)
    # Attach the callback functions to the activate signal
    abrir_browser_item.connect("activate", self.abrir_browser, None)
    copiar_portapapeles_item.connect("activate", self.copiar_al_portapapeles, None)
    toggle_leido_item.connect("activate", self.toggle_leido, 'single')
    toggle_todos_leido_item.connect("activate", self.toggle_leido, 'all')
    tree_menu.show_all()
    tree_menu.popup(None, None, None, event.button, event.get_time())
   return True

 def image_zoom_button_press_event(self, eventbox, event):
  """Toggles fullscreen mode for the browser."""
  if event.button == 1:
   if self.fullscreen:
    self.scrolled_window1.set_size_request(self.a, self.b)
    self.scrolled_window1.show()
    self.scrolled_window2.set_size_request(300,150)
    #self.scrolled_window2.set_size_request(self.c, self.d)
    self.scrolled_window2.show()
    self.fullscreen = False
   else:
    self.scrolled_window1.set_size_request(0,0)
    self.scrolled_window1.hide()
    self.scrolled_window2.set_size_request(0,0)
    self.scrolled_window2.hide()
    self.fullscreen = True

 def headerlink_button_press_event(self, eventbox, event):
  """Launches a browser opening the selected feed entry."""
  if event.button == 1:
   self.abrir_browser(self)

 def headerlink_mouse_enter(self, widget, event):
  """Shows the link the headerlink points to in the statusbar."""
  (model, iter) = self.treeselection2.get_selected()
  if(iter is not None): # Hay alguna fila de la lista seleccionada
   id_articulo = self.liststore.get_value(iter, 4)
   cursor = self.conn.cursor()
   self.lock.acquire()
   cursor.execute('SELECT enlace FROM articulo WHERE id = ?', [id_articulo])
   link = cursor.fetchone()[0]
   self.lock.release()
   cursor.close()
   self.statusbar.set_text(link.encode("utf8"))

 def headerlink_mouse_leave(self, widget, event):
  """Hides the link the headerlink points to in the statusbar."""
  self.statusbar.set_text("")

 def update_feed(self, data=None, new_feed=False):
  """Updates a single (selected) feed or the ones from a (selected) category, if any."""
  (model, iter) = self.treeselection.get_selected()
  if(iter is not None): # Si hay algún nodo seleccionado...
   nodes = {} # Dictionary! (key:value pairs containing id_feed:iter)
   id_category = self.treestore.get_value(iter, 2)
   # OLD: if(model.iter_depth(iter) == 0) and (id_category != 9998) and (id_category != 9999): # Si es un nodo padre...
   if(model.iter_depth(iter) == 0) and (self.clear_mode == 0) and (id_category != 9998 and id_category != 9999): # Si es un nodo padre...
    # Update all feeds of this category
    iter = model.iter_children(iter)
    while iter:
     id_feed = self.treestore.get_value(iter, 2)
     nodes[id_feed] = iter # Storing id_feed:iter pairs...
     iter = self.treestore.iter_next(iter)
    # Old way: self.get_feed(feed_ids)
   # OLD: elif(model.iter_depth(iter) == 1): # Si es un nodo hijo...
   else: # NEW: Si es un nodo hijo...
    # Update this single feed
    id_feed = self.treestore.get_value(iter, 2)
    nodes[id_feed] = iter # Storing id_feed:iter pairs...
    # Old way: self.get_feed(id_feed)
   # New way:
   self.t = threading.Thread(target=self.get_feed, args=(nodes,new_feed, ))
   self.t.start()

 def update_all_feeds(self, data=None):
  """Updates all feeds (no complications!)."""
  # Old way: self.get_feed()
  # New way:
  if self.ui_lock is False: # This prevents autoupdate from launching if an update is alredy in progress...
   self.t = threading.Thread(target=self.get_feed, args=())
   self.t.start()
  return True

 def stop_feed_update(self, data=None):
  """Stop feeds update."""
  if self.stop_feed_update_lock is False:
   self.stop_feed_update_lock = True
   widget = self.ui.get_widget("/Toolbar/Stop update")
   widget.set_sensitive(False)
   self.stop_item.set_sensitive(False)

 def check_feed_item(self, dentry):
  """Sets a default value for feed items if there's not any. Helper function of get_feed()."""
  if(hasattr(dentry,'date_parsed')):
   dp = dentry.date_parsed
   try:
    secs = time.mktime(datetime.datetime(dp[0], dp[1], dp[2], dp[3], dp[4], dp[5], dp[6]).timetuple())
    #print 'Correct date taken: ' + str(dp)
   except:
    #print 'Dentry.date_parsed exist, BUT correct date could not be taken; creating my own...'
    split = str(datetime.datetime.now()).split(' ')
    ds = split[0].split('-')
    ts = split[1].split(':')
    t = datetime.datetime(int(ds[0]), int(ds[1]), int(ds[2]), int(ts[0]), int(ts[1]), int(float(ts[2])))
    secs = time.mktime(t.timetuple())
  else:
   #print 'Date entry does not exist! Creating my own...'
   split = str(datetime.datetime.now()).split(' ')
   ds = split[0].split('-')
   ts = split[1].split(':')
   t = datetime.datetime(int(ds[0]), int(ds[1]), int(ds[2]), int(ts[0]), int(ts[1]), int(float(ts[2])))
   secs = time.mktime(t.timetuple())
  
  if hasattr(dentry,'title'):
   if dentry.title is not None: title = dentry.title.encode("utf-8")
   else: title = _('Without title')
  else: title = _('Without title')

  if hasattr(dentry,'description'):
   if dentry.description is not None: description = dentry.description.encode("utf-8")
   else: description = ''
  else: description = ''

  if hasattr(dentry,'link'):
   if dentry.link is not None: link = dentry.link.encode("utf-8")
   else: link = _('Without link')
  else: link = _('Without link')

  if(hasattr(dentry,'id')):
   if dentry.id is not None:
    id = dentry.id.encode("utf-8")
   else:
    if title != '':
     id = hashlib.md5(title).hexdigest().encode("utf-8")
    else:
     id = hashlib.md5(description).hexdigest().encode("utf-8")
  else:
   if title != '':
    id = hashlib.md5(title).hexdigest().encode("utf-8")
   else:
    id = hashlib.md5(description).hexdigest().encode("utf-8")

  return (secs, title, description, link, id)

 def find_entry_images(self, feed_url, description):
  """Searches for img tags in order to identify feed body images. It also checks 
     paths to make sure all are absolute (if not, it tries to). Returns a
     comma-separated string with all images with it's (url) path."""
  images = ''
  rgxp = '''<img\s+[^>]*?src=["']?([^"'>]+)[^>]*?>'''

  m = re.findall(rgxp, description, re.I)
  for img in m:
   images += img+','
  if(images != ''):
   images = images[0:-1]
  return images

 def retrieve_entry_images(self, id_articulo, images):
  """Manages entry images. It discards downloading images that are already on the
     database to save space and bandwidth per URL basis."""
  if not os.path.exists(images_path):
   os.makedirs(images_path)

  cursor = self.conn.cursor()
  # Comprueba que esa URL no exista ya en la BD...
  for i in images.split(","):
   self.lock.acquire()
   cursor.execute('SELECT nombre FROM imagen WHERE url = ?', [i])
   row = cursor.fetchone()
   self.lock.release()
   if(row is None):
    # a) Si no existe, guarda entrada en tabla imagen y descarga físicamente la imagen a /imagenes.
    self.statusbar.set_text(_('Obtaining image ') + i + '...'.encode("utf8"))
    self.lock.acquire()
    cursor.execute('SELECT MAX(id) FROM imagen')
    id_entry_max = cursor.fetchone()[0]
    self.lock.release()
    if id_entry_max is None: id_entry_max = 1
    else: id_entry_max += 1
    self.lock.acquire()
    cursor.execute('INSERT INTO imagen VALUES(null, ?, ?, ?)', [id_entry_max,i,id_articulo])
    self.conn.commit()
    self.lock.release()
    try:
     web_file = urllib2.urlopen(i, timeout=10)
     image = images_path + '/' + `id_entry_max`
     local_file = open(image, 'w')
     local_file.write(web_file.read())
     local_file.close()
     web_file.close()
    except:
     pass
    self.statusbar.set_text('')
   else:
    # b) Si existe, comprobamos que no sea una entrada repe...
    self.lock.acquire()
    cursor.execute('INSERT INTO imagen VALUES(null, ?, ?, ?)', [row[0],i,id_articulo])
    self.conn.commit()
    self.lock.release()
  cursor.close()

 def toggle_menuitems_sensitiveness(self, enable):
  """Enables/disables some menuitems while getting feeds to avoid
     multiple instances running or race conditions."""
  item_list = ["/Menubar/ArchiveMenu/Delete feed", "/Menubar/ArchiveMenu/Delete category",
               "/Menubar/ArchiveMenu/Import feeds", "/Menubar/ArchiveMenu/Export feeds",
               "/Menubar/ArchiveMenu/Quit", "/Menubar/EditMenu/Edit", "/Menubar/EditMenu/Search",
               "/Menubar/EditMenu/Read all", "/Menubar/EditMenu/Preferences", "/Menubar/NetworkMenu/Update",
               "/Menubar/NetworkMenu/Update all", "/Menubar/HelpMenu/Check updates",
               "/Toolbar/Update all", "/Toolbar/Read all", "/Toolbar/Search", "/Toolbar/Preferences"]

  for item in item_list:
   widget = self.ui.get_widget(item)
   widget.set_sensitive(enable)
  # Stop button
  widget = self.ui.get_widget("/Toolbar/Stop update")
  widget.set_sensitive(not enable)

  # Statusicon menuitems...
  self.update_item.set_sensitive(enable)
  self.stop_item.set_sensitive(not enable)
  self.quit_item.set_sensitive(enable)

  self.ui_lock = not enable

 def change_feed_icon(self, d, model, id_feed, cursor):
  """Toggles feed icons -between error & ok- while trying to obtain feed data."""
  dont_parse = False
  count = 0
  bozo_invalid = ['urlopen', 'Document is empty'] # Custom non-wanted bozos

  # This is for handling clear_mode feeds.
  if self.treeindex.has_key(id_feed):
   dest_iter = self.treeindex[id_feed]
  else:
   dest_iter = None

  if not len(d.entries) > 0: # Feed has no entries...
   self.lock.acquire()
   cursor.execute('SELECT count(id) FROM articulo WHERE id_feed = ?', [id_feed])
   num_entries = cursor.fetchone()[0]
   self.lock.release()
   if num_entries == 0: # ... and never had! Fingerprinted as invalid!
    if dest_iter is not None:
     model.set(dest_iter, 1, 'crossout-image')
    dont_parse = True
  elif hasattr(d,'bozo_exception'): # Feed HAS a bozo exception...
   #print d.bozo_exception
   for item in bozo_invalid:
    if item in str(d.bozo_exception):
     if dest_iter is not None:
      model.set(dest_iter, 1, 'crossout-image')
     dont_parse = True
     break
    elif count == len(bozo_invalid):
     # Si el feed no tiene icono propio, procurarle el generico!
     if not os.path.exists(favicon_path + '/' + `id_feed`):
      if dest_iter is not None:
       model.set(dest_iter, 1, 'rss-image')
     else:
      if dest_iter is not None:
       model.set(dest_iter, 1, `id_feed`)
    count += 1
  else: # Feed HAS NOT any bozo exception...
   # Si el feed no tiene icono propio, procurarle el generico!
   if not os.path.exists(favicon_path + '/' + `id_feed`):
    if dest_iter is not None:
     model.set(dest_iter, 1, 'rss-image')
   else:
    if dest_iter is not None: 
     model.set(dest_iter, 1, `id_feed`)

  if dont_parse:
   return True
  else:
   return False

 def get_feed_helper(self, iter, child, id_feed, cursor, model, new_posts, num_new_posts_total, aux_num_new_posts_total, mode, id_category=None, new_feed=False):
  """Exploits the entry retrieving for both getting all feeds or only the selected
     category or feed."""

  global APP_VERSION

  # START NAME PARSING #
  #if child is not None: # Check que descarta feeds que todavia no tienen entradas (en clear_mode)
  # nombre_feed = model.get_value(child, 0)
  # nombre_feed = self.simple_name_parsing(nombre_feed)
  #else:
  # self.lock.acquire()
  #  cursor.execute('SELECT nombre FROM feed WHERE id = ' + `id_feed`)
  #  row = cursor.fetchone()
  #  self.lock.release()
  #  nombre_feed = row[0]
  # END NAME PARSING #

  # Primero obtenemos el feed (los datos)...
  self.lock.acquire()
  cursor.execute('SELECT nombre,url FROM feed WHERE id = ?', [id_feed])
  row = cursor.fetchone()
  nombre_feed = row[0]
  url = row[1]
  self.lock.release()
  self.statusbar.set_text(_('Obtaining feed ') + nombre_feed + '...'.encode("utf8"))

  gtk.gdk.threads_enter()
  d = feedparser.parse(url, agent='Naufrago!/'+APP_VERSION+'; +http://sourceforge.net/projects/naufrago/')

  dont_parse = self.change_feed_icon(d, model, id_feed, cursor)
  if dont_parse:
   gtk.gdk.threads_leave()
   #continue
   return (new_posts, num_new_posts_total, False)

  feed_link = ''
  if(hasattr(d.feed,'link')): feed_link = d.feed.link.encode('utf-8')

  # Si se trata de un feed nuevo, necesitamos el título antes de nada
  if new_feed:
   if(hasattr(d.feed,'title')):
    nombre_feed = title = d.feed.title.encode('utf-8')
    # Update db...
    (model_tmp, iter_tmp) = self.treeselection.get_selected()
    id_feed_tmp = model_tmp.get_value(iter_tmp, 2)
    self.lock.acquire()
    cursor.execute('UPDATE feed SET nombre = ? WHERE id = ?', [title.decode('utf-8'),id_feed_tmp])
    self.conn.commit()
    self.lock.release()
    # Update feed tree...
    model_tmp.set(iter_tmp, 0, title)

  limit = count = len(d.entries)
  if count > self.num_entries:
   limit = self.num_entries

  new_entries = []
  # Check for article existence...
  for i in range(0, count):
   (secs, title, description, link, id) = self.check_feed_item(d.entries[i])
   self.lock.acquire()
   cursor.execute('SELECT id FROM articulo WHERE entry_unique_id = ? AND id_feed = ?', [id.decode("utf-8"),id_feed])
   unique = cursor.fetchone()
   self.lock.release()
   images = ''
   # Non-existant entry? Insert!
   if(unique is None):
    images = self.find_entry_images(feed_link, description)
    ghost = 0
    if i >= limit:
     ghost = 1
    self.lock.acquire()
    cursor.execute('INSERT INTO articulo VALUES(null, ?, ?, ?, ?, 0, 0, ?, ?, ?, ?)', [title.decode("utf-8"),description.decode("utf-8"),secs,link.decode("utf-8"),images,id_feed,id.decode("utf-8"),ghost])
    self.conn.commit()
    self.lock.release()
    self.lock.acquire()
    cursor.execute('SELECT MAX(id) FROM articulo')
    recently_inserted_entry = cursor.fetchone()
    self.lock.release()
    new_entries.append(recently_inserted_entry[0]) # Lista de control de nuevas entries insertadas
    # START Offline mode image retrieving
    if i < limit:
     if (self.offline_mode == 1) and (images != ''):
      self.lock.acquire()
      cursor.execute('SELECT id from imagen WHERE id_articulo = ?', [recently_inserted_entry[0]]) # No dupes
      images_present = cursor.fetchone()
      self.lock.release()
      if images_present is None:
       self.retrieve_entry_images(recently_inserted_entry[0], images)
    # END Offline mode image retrieving
    # Accounting...
    if i < limit:
    # new_posts = True
     num_new_posts_total += 1

   else:
    # START Offline mode image retrieving
    if i < limit:
     if (self.offline_mode == 1):
      self.lock.acquire()
      cursor.execute('SELECT imagenes FROM articulo WHERE id = ?', [unique[0]]) # ¿Hay imagenes?
      imagenes = cursor.fetchone()
      self.lock.release()
      if (imagenes is not None) and (imagenes[0] != ''):
       self.lock.acquire()
       cursor.execute('SELECT id from imagen WHERE id_articulo = ?', [unique[0]]) # No dupes
       images_present = cursor.fetchone()
       self.lock.release()
       if images_present is None:
        self.retrieve_entry_images(unique[0], imagenes[0])
    # END Offline mode image retrieving
    else:
     self.lock.acquire()
     cursor.execute('UPDATE articulo SET ghost = 1 WHERE id = ? AND importante = 0', [unique[0]])
     self.conn.commit()
     self.lock.release()

  # CLEANUP: Check first is the feed is full (to do some cleanup)
  self.lock.acquire()
  cursor.execute('SELECT count(id) FROM articulo WHERE id_feed = ? AND importante = 0', [id_feed])
  total = cursor.fetchone()
  self.lock.release()
  if (total is not None):
   # Si lo que recibimos del feed es menor que self.num_entries,
   # count pasará a valer lo mismo que self.num_entries.
   if count < self.num_entries:
    count = self.num_entries
   # Si el total (sin importantes) supera lo que recibimos del feed
   # (o self.num_entries si count es menor), entramos a hacer LIMPIEZA.
   if (total[0]>count):
    exceed = total[0] - count
    self.lock.acquire()
    cursor.execute('SELECT id FROM articulo WHERE id_feed = ? AND importante=0 ORDER BY fecha ASC LIMIT ?', [id_feed,exceed])
    row  = cursor.fetchall()
    self.lock.release()
    for id_articulo in row:
     # Ahora borramos las imagenes del filesystem, si procede
     self.lock.acquire()
     cursor.execute('SELECT id FROM imagen WHERE id_articulo = ?', [id_articulo[0]])
     images = cursor.fetchall()
     self.lock.release()
     for i in images:
      self.lock.acquire()
      cursor.execute('SELECT count(id) FROM imagen WHERE nombre = ?', [i[0]])
      num_images = cursor.fetchone()
      self.lock.release()
      if (num_images is not None) and (num_images[0] == 1):
       if os.path.exists(images_path + '/' + `i[0]`):
        os.unlink(images_path + '/' + `i[0]`)
      self.lock.acquire()
      cursor.execute('DELETE FROM imagen WHERE id_articulo = ?', [id_articulo[0]])
      self.conn.commit()
      self.lock.release()

     self.lock.acquire()
     cursor.execute('DELETE FROM articulo WHERE id = ?', [id_articulo[0]])
     self.conn.commit()
     self.lock.release()
     # Accounting...
     if len(new_entries) > 0:
      if id_articulo[0] in new_entries:
       num_new_posts_total -= 1
       new_entries.remove(id_articulo[0])
  # Accounting...
  if len(new_entries) > 0:
   new_posts = True
  else:
   new_posts = False

  gtk.gdk.threads_leave()

  # MOVIDO JUSTO ABAJO!
  # Actualizamos la lista de entries del feed seleccionado
  #if(count != 0):
  # (model2, iter2) = self.treeselection.get_selected()
  # if(iter2 is not None): # Si hay algún nodo seleccionado...
    # OLD: if(model2.iter_depth(iter2) == 1): # ... y es un nodo hijo
  #  if(model2.iter_depth(iter2) == 1) or (model2.iter_depth(iter2) == 0 and self.clear_mode == 1): # ... y es un nodo hijo
  #   id_selected_feed = self.treestore.get_value(iter2, 2)
  #   if id_selected_feed == id_feed:
  #    self.populate_entries(id_feed)

  if new_posts:
   # Actualizamos la lista de entries del feed seleccionado
   (model2, iter2) = self.treeselection.get_selected()
   if(iter2 is not None): # Si hay algún nodo seleccionado...
    # OLD: if(model2.iter_depth(iter2) == 1): # ... y es un nodo hijo
    if(model2.iter_depth(iter2) == 1) or (model2.iter_depth(iter2) == 0 and self.clear_mode == 1): # ... y es un nodo hijo
     id_selected_feed = self.treestore.get_value(iter2, 2)
     if id_selected_feed == id_feed:
      self.populate_entries(id_feed)

   # Luego el recuento del feed
   #if nombre_feed is None:
   # self.lock.acquire()
   # cursor.execute('SELECT nombre FROM feed WHERE id = ' + `id_feed`)
   # row = cursor.fetchone()
   # self.lock.release()
   # nombre_feed = row[0]

   self.lock.acquire()
   cursor.execute('SELECT count(id) FROM articulo WHERE id_feed = ' + `id_feed` + ' AND leido=0 AND ghost=0')
   row = cursor.fetchone()
   self.lock.release()
   if row[0] == 0:
    feed_label = nombre_feed
    font_style = 'normal'
   else:
    feed_label = nombre_feed + ' [' + `row[0]` + ']'
    font_style = 'bold'
   #if (count != 0):
   if mode == 'all':
    if self.clear_mode == 0:
     model2.set(child, 0, feed_label, 3, font_style)
    else:
     if not self.treeindex.has_key(id_feed): # Insert feed on the tree if it's not already there!
      # TEST
      if os.path.exists(favicon_path + '/' + `id_feed`):
       useless_iter, feed_iter = self.alphabetical_node_insertion(feed_label, [feed_label, `id_feed`, id_feed, font_style])
      else:
       useless_iter, feed_iter = self.alphabetical_node_insertion(feed_label, [feed_label, 'rss-image', id_feed, font_style])
      self.treeindex[id_feed] = feed_iter
      # TEST
      #feed_iter = self.treestore.append(None, [feed_label, `id_feed`, id_feed, font_style])
      #self.treeindex[id_feed] = feed_iter
     else:
      model2.set(child, 0, feed_label, 3, font_style)
   else:
    model.set(child, 0, feed_label, 3, font_style)

   if self.clear_mode == 0: # NEW
    # Y luego el recuento de los No-leidos
    (model3, useless_iter) = self.treeselection.get_selected()
    dest_iter = self.treeindex[9999]
    nombre_feed_destino = model3.get_value(dest_iter, 0)
    nombre_feed_destino = self.simple_name_parsing(nombre_feed_destino)
    self.lock.acquire()
    cursor.execute('SELECT count(id) FROM articulo WHERE leido=0 AND ghost=0')
    count = cursor.fetchone()
    self.lock.release()
    if count is not None:
     if count[0] > 0:
      feed_label = nombre_feed_destino + ' [' + `count[0]` + ']'
      font_style = 'bold'
      # Y luego el resaltado de la categoría
      model.set(iter, 3, 'bold')
     else:
      feed_label = nombre_feed_destino
      font_style = 'normal'
    else:
     feed_label = nombre_feed_destino
     font_style = 'normal'
    model3.set(dest_iter, 0, feed_label, 3, font_style)

  if self.clear_mode == 0: # NEW
   # START: Driven mode, parte 1
   # Cualquier feed con nuevas entradas expanderá la categoria.
   if (self.driven_mode == 1):
    if new_posts:
     self.treeview.expand_row(model.get_path(iter), open_all=False)
   # END: Driven mode, parte 1

  # ¿Hay cancelación?
  if self.stop_feed_update_lock:
   #break
   return (new_posts, num_new_posts_total, True)

  if self.clear_mode == 0: # NEW
   # START: Driven mode, parte 2
   # Si no hubo ninguna entrada nueva y no habia ya ninguna previamente,
   # contraeremos la categoria.
   if (self.driven_mode == 1):
    if num_new_posts_total == aux_num_new_posts_total:
     if mode == 'all':
      boldornot = self.toggle_category_bold(id_category)
     else: # mode == 'single'
      boldornot = self.toggle_category_bold()
     if boldornot == 'normal':
      self.treeview.collapse_row(model.get_path(iter))
   # END: Driven mode, parte 2

  return (new_posts, num_new_posts_total, False)

 def get_feed(self, data=None, new_feed=False):
  """Obtains & stores the feeds (thanks feedparser!)."""
  self.toggle_menuitems_sensitiveness(enable=False)
  self.throbber.show()
  new_posts = False # Reset
  aux_num_new_posts_total = num_new_posts_total = 0 # Overall
  self.on_a_feed_update = True # Booleano indicador de que estamos en un proceso de feed update

  if(data is None): # Iterarlo todo

   (model, iter) = self.treeselection.get_selected() # We only want the model here...
   iter = model.get_iter_root() # Magic
   cursor = self.conn.cursor()
   while (iter is not None) and (not self.stop_feed_update_lock):
    # OLD: if(model.iter_depth(iter) == 0): # Si es padre
    if(model.iter_depth(iter) == 0) and (self.clear_mode == 0): # Si es padre
     id_category = model.get_value(iter, 2)
     new_posts = False # Reset
     aux_num_new_posts_total = num_new_posts_total
     for i in range(model.iter_n_children(iter)):
      child = model.iter_nth_child(iter, i)
      id_feed = model.get_value(child, 2)
      (new_posts, num_new_posts_total, break_flag) = self.get_feed_helper(iter, child, id_feed, cursor, model, new_posts, num_new_posts_total, aux_num_new_posts_total, 'all', id_category, new_feed)
      if break_flag:
       break
    # NEW
    #
    # TODO; Esto NO puede iterarse por las ramas del árbol. Tiene que hacerse por SQL!!!
    #
    else:
     self.lock.acquire()
     cursor.execute('SELECT id,nombre FROM feed ORDER BY nombre ASC')
     rows = cursor.fetchall()
     self.lock.release()
     for row in rows:
      new_posts = False # Reset
      aux_num_new_posts_total = num_new_posts_total
      id_feed = row[0]
      #feed_label = row[1]
      if not self.treeindex.has_key(id_feed):
       #print 'Feed id "' + `id_feed` + '" NO encontrado, insertando en el árbol...'
       #iter = self.treestore.append(None, [feed_label, `id_feed`, id_feed, 'normal'])
       #self.treeindex[id_feed] = iter
       iter = None
      else:
       iter = self.treeindex[id_feed]
      (new_posts, num_new_posts_total, break_flag) = self.get_feed_helper(iter, iter, id_feed, cursor, model, new_posts, num_new_posts_total, aux_num_new_posts_total, 'all', None, new_feed)
      if break_flag:
       break
     break # <--- break para salir del while!
    #else:
    # print model.get_value(iter, 0)
    # new_posts = False # Reset
    # aux_num_new_posts_total = num_new_posts_total
    # id_feed = model.get_value(iter, 2)
    # (new_posts, num_new_posts_total, break_flag) = self.get_feed_helper(iter, iter, id_feed, cursor, model, new_posts, num_new_posts_total, aux_num_new_posts_total, 'all', None, new_feed)
    # if break_flag:
    #  break
    # NEW
    iter = self.treestore.iter_next(iter) # Pasamos al siguiente Padre...
   cursor.close()

  else: # Iterar sobre los elementos del diccionario recibido como data.

   (model, iter) = self.treeselection.get_selected() # We only want the model here...
   cursor = self.conn.cursor()
   for id_feed, child in data.iteritems():
    (new_posts, num_new_posts_total, break_flag) = self.get_feed_helper(iter, child, id_feed, cursor, model, new_posts, num_new_posts_total, aux_num_new_posts_total, 'single', None, new_feed)
    if break_flag:
     break
   cursor.close()

  # Restablecemos el indicador de cancelación
  self.stop_feed_update_lock = False
  self.on_a_feed_update = False

  # Notificación de mensajes nuevos 
  if self.show_newentries_notification:
   if num_new_posts_total > 0:
    new_entries_txt = _('New entry/s')
    were_added_txt = _(' entry/s were added')
    n = pynotify.Notification(new_entries_txt, `num_new_posts_total` + were_added_txt, self.imageURI)
    #n.attach_to_status_icon(self.statusicon) # <-- This fucks up the whole thing!!!
    n.show()

  self.statusbar.set_text('')
  # Fires tray icon blinking
  if((num_new_posts_total > 0) and (window_visible is False) and (self.show_trayicon == 1)):
   self.statusicon.set_blinking(True)
  self.throbber.hide()
  self.toggle_menuitems_sensitiveness(enable=True)

 def import_feeds(self, data=None):
  """Imports feeds from an OPML file. It does not import categories
  or feeds with an existent name in the DB, and the later ones keep
  their settings (in case of feeds, they maintain url and category)."""
  dialog = gtk.FileChooserDialog(_("Open.."),
                                self.window,
                                gtk.FILE_CHOOSER_ACTION_OPEN,
                                (gtk.STOCK_OPEN, gtk.RESPONSE_OK,
                                gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

  dialog.set_default_response(gtk.RESPONSE_OK)

  filter = gtk.FileFilter()
  filter.set_name("opml/xml")
  filter.add_pattern("*.opml")
  filter.add_pattern("*.xml")
  dialog.add_filter(filter)

  filter = gtk.FileFilter()
  filter.set_name(_("All files"))
  filter.add_pattern("*")
  dialog.add_filter(filter)

  response = dialog.run()
  filename = dialog.get_filename()
  dialog.destroy()

  if response == gtk.RESPONSE_OK:
   dialog.hide()
   f = open(filename, 'r')
   tree = ElementTree.parse(f)
   current_category = 1 # General
   cursor = self.conn.cursor()
   for node in tree.getiterator('outline'):
    name = node.attrib.get('text').replace('[','(').replace(']',')')
    url = node.attrib.get('xmlUrl')
    if url:
     self.lock.acquire()
     cursor.execute('SELECT id FROM feed WHERE nombre = ?', [name])
     row = cursor.fetchone()
     self.lock.release()
     if(row is None):
      # Create feed in the DB
      self.lock.acquire()
      cursor.execute('INSERT INTO feed VALUES(null, ?, ?, ?)', [name,url,current_category])
      self.conn.commit()
      row = cursor.execute('SELECT MAX(id) FROM feed')
      id_feed = cursor.fetchone()[0]
      self.lock.release()
      # Obtain feed favicon
      #self.get_favicon(id_feed, url)
      t = threading.Thread(target=self.get_favicon, args=(id_feed, url, ))
      t.start()
    else:
     if len(node) != 0:
      self.lock.acquire()
      cursor.execute('SELECT id FROM categoria WHERE nombre = ?', [name])
      row = cursor.fetchone()
      self.lock.release()
      if(row is None):
       # Create category in the DB (if it does not exist already)
       self.lock.acquire()
       cursor.execute('INSERT INTO categoria VALUES(null, ?)', [name])
       self.conn.commit()
       row = cursor.execute('SELECT MAX(id) FROM categoria')
       row = cursor.fetchone()
       self.lock.release()
      current_category = row[0]
   f.close()
   cursor.close()

   self.liststore.clear()
   self.treestore.clear()
   self.populate_feeds()
   if(self.init_unfolded_tree == 1): self.treeview.expand_all()

 def export_feeds(self, data=None):
  """Exports feeds to an OPML file."""
  dialog = gtk.FileChooserDialog(_("Open.."),
                                self.window,
                                gtk.FILE_CHOOSER_ACTION_SAVE, None)

  dialog.add_button(_("_Save"), gtk.RESPONSE_OK)
  dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT)
  dialog.set_default_response(gtk.RESPONSE_OK)

  filter = gtk.FileFilter()
  filter.set_name("opml/xml")
  filter.add_pattern("*.opml")
  dialog.add_filter(filter)
  
  response = dialog.run()

  if response == gtk.RESPONSE_OK:
   f = open(dialog.get_filename()+'.opml', 'w')
   out = '<?xml version="1.0"?>\n<opml version="1.0">\n<head>\n<title>Naufrago! Feed List Export</title>\n</head>\n<body>\n'
   cursor = self.conn.cursor()
   self.lock.acquire()
   cursor.execute('SELECT id,nombre FROM categoria')
   categorias = cursor.fetchall()
   self.lock.release()
   cursor.close()
   for row in categorias:
    out += '<outline title="'+row[1]+'" text="'+row[1]+'" description="'+row[1]+'" type="folder">\n'
    self.lock.acquire()
    cursor.execute('SELECT nombre,url FROM feed WHERE id_categoria = ?', [row[0]])
    feeds = cursor.fetchall()
    self.lock.release()
    for row2 in feeds:
     nombre = row2[0].replace('&', '%26')
     url = row2[1].replace('&', '%26')
     out += '<outline title="'+nombre+'" text="'+nombre+'" type="rss" xmlUrl="'+url+'"/>\n'
    out += '</outline>'
   out += '</body>\n</opml>'
   f.write(out)
   f.close()
  dialog.destroy()

 def add_icon_to_factory(self, filename, id_feed=None):
  """Adds an icon to the icon factory."""
  if filename == None:
   factory = gtk.IconFactory()
   pixbuf = gtk.gdk.pixbuf_new_from_file(media_path + 'SRD_RSS_Logo_mini.png')
   iconset = gtk.IconSet(pixbuf)
   factory.add(str(id_feed), iconset)
   factory.add_default()
  elif filename == 'importantes' or filename == 'no-leidos':
   factory = gtk.IconFactory()
   pixbuf = gtk.gdk.pixbuf_new_from_file(media_path + 'blue_folder.png')
   iconset = gtk.IconSet(pixbuf)
   factory.add(filename, iconset)
   factory.add_default()
  else:
   try:
    factory = gtk.IconFactory()
    pixbuf = gtk.gdk.pixbuf_new_from_file(filename)
    iconset = gtk.IconSet(pixbuf)
    #factory.add('stock_id_name', iconset)
    factory.add(str(id_feed), iconset) # Icon stock id will be the id_feed!
    factory.add_default()
   except: # Si casca, queremos el icono por defecto!
    if os.path.exists(filename):
     os.unlink(filename)
    factory = gtk.IconFactory()
    pixbuf = gtk.gdk.pixbuf_new_from_file(media_path + 'SRD_RSS_Logo_mini.png')
    iconset = gtk.IconSet(pixbuf)
    factory.add(str(id_feed), iconset)
    factory.add_default()

 def get_favicon(self, id_feed, url):
  """Obtains the favicon from a web and stores it on the filesystem. It should be
     called only once at feed entry creation OR on feed import process."""
  if not os.path.exists(favicon_path):
   os.makedirs(favicon_path)

  gtk.gdk.threads_enter()
  try:
   split = url.split("/")
   favicon_url = split[0] + '//' + split[1] + split[2] + '/favicon.ico'
   web_file = urllib2.urlopen(favicon_url, timeout=10)
   favicon = favicon_path + '/' + `id_feed`
   local_file = open(favicon, 'w')
   local_file.write(web_file.read())
   local_file.close()
   web_file.close()
   # Registrar el favicon...
   self.add_icon_to_factory(favicon, id_feed)
  except:
   self.add_icon_to_factory(None, id_feed)
  gtk.gdk.threads_leave()

 def populate_favicons(self):
  """Iterates 'favicons' directory to load existent favicons in a bunch."""
  for f in os.listdir(favicon_path):
   self.add_icon_to_factory(favicon_path + '/' + f, f)
   
 # INIT #
 ########

 def __init__(self):
  self.lock = threading.Lock()
  # Crea la base para la aplicación (directorio + feed de regalo!), si no la hubiere
  self.create_base()
  # Obtiene la config de la app
  self.get_config()
  # Creamos la ventana principal
  self.create_main_window()

def main():
 # Params: interval in miliseconds, callback, callback_data
 # Start timer (1h = 60min = 3600secs = 3600*1000ms)
 if naufrago.update_freq_timemode == 0: mult = 3600
 elif naufrago.update_freq_timemode == 1: mult = 60
 gobject.timeout_add(naufrago.update_freq*mult*1000, naufrago.update_all_feeds)
 gtk.main()
 
if __name__ == "__main__":
 naufrago = Naufrago()
 main()
