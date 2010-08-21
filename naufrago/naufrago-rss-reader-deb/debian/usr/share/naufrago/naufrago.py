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
from htmlentitydefs import name2codepoint
import hashlib
import xml.sax.saxutils
import locale
import gettext

ABOUT_PAGE = ''
PUF_PAGE = ''
debian = True
window_visible = True

# Locale stuff
APP = 'naufrago'
if debian == True: DIR = '/usr/share/naufrago/locale'
else: DIR = os.getcwd() + '/locale'

locale.setlocale(locale.LC_ALL, '')
locale = locale.getdefaultlocale()[0]
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext

if debian == True: # We're running on 'Debian-mode' (installed from .deb)
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
 else:
  index_path = current_path + '/content/index.html'
  puf_path = current_path + '/content/puf.html'

class Naufrago:

 def delete_event(self, event, data=None):
  """Closes the app through window manager signal"""
  self.save_config()
  gtk.main_quit()
  return False

 def tree_key_press_event(self, widget, event):
  """Tells which keyboard button was pressed"""
  key = gtk.gdk.keyval_name(event.keyval)
  if(key == 'Delete'):
   (model, iter) = self.treeselection.get_selected()
   if(iter is not None): # Si hay algún nodo seleccionado...
    text = self.treestore.get_value(iter, 0)
    if(model.iter_depth(iter) == 0): # Si es un nodo padre...
     self.delete_category()
    elif(model.iter_depth(iter) == 1): # Si es un nodo hijo...
     self.delete_feed()

 def make_pb(self, tvcolumn, cell, model, iter):
  """Renders the parameter received icons"""
  stock = model.get_value(iter, 1)
  pb = self.treeview.render_icon(stock, gtk.ICON_SIZE_MENU, None)
  cell.set_property('pixbuf', pb)
  return

 def toggle_importante(self, cell, path, model):
  """Sets the toggled state on the toggle button to true or false"""
  model[path][1] = not model[path][1]
  if model[path][1] == True:
   self.eb.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("pink"))
  else:
   self.eb.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#EDECEB"))
  cursor = self.conn.cursor()
  cursor.execute('UPDATE articulo SET importante = ? WHERE id = ?', [model[path][1],model[path][4]])
  self.conn.commit()
  cursor.close()
  return

 def simple_name_parsing(self, nombre_feed):
  """Parses & returns the proper name of the feeds on the tree."""
  rgxp = r''' \[.*\]$'''
  m = re.search(rgxp, nombre_feed)
  if m is not None:
   nombre_feed = nombre_feed.split(' ')
   nombre_feed = ' '.join(nombre_feed[0:len(nombre_feed)-1])
  return nombre_feed

 def toggle_leido(self, event, data=None):
  """Toggle entries between read/non-read states."""
  cursor = self.conn.cursor()
  
  if(data == 'tree'): # La petición de toggle proviene del árbol de feeds
   (model, iter) = self.treeselection.get_selected()
   if(iter is not None): # Hay algún nodo seleccionado
    row_name = self.treestore.get_value(iter, 0)
    if(model.iter_depth(iter) == 1): # Si es hoja...
     # 1º vamos a por el label del feed...
     id_feed = self.treestore.get_value(iter, 2)

     # START NAME PARSING #
     nombre_feed = model.get_value(iter, 0)
     nombre_feed = self.simple_name_parsing(nombre_feed)
     # END NAME PARSING #

     model.set(iter, 0, nombre_feed, 3, 'normal')
     # 2º vamos a por las entries del feed...
     (model, iter) = self.treeselection2.get_selected()
     iter = model.get_iter_root() # Magic
     while iter:
      self.liststore.set_value(iter, 3, 'normal')
      iter = self.liststore.iter_next(iter)
     # ...y 3º a por los datos
     cursor.execute('UPDATE articulo SET leido=1 WHERE id_feed = ?', [id_feed])
     self.conn.commit()
     cursor.close()

    elif(model.iter_depth(iter) == 0): # Si es padre...
     # 1º vamos a por el label del feed...
     feed_ids = ''
     iter = model.iter_children(iter)
     while iter:
      id_feed = self.treestore.get_value(iter, 2)
      feed_ids += str(id_feed)+','

      # START NAME PARSING #
      nombre_feed = model.get_value(iter, 0)
      nombre_feed = self.simple_name_parsing(nombre_feed)
      # END NAME PARSING #

      model.set(iter, 0, nombre_feed, 3, 'normal')
      iter = self.treestore.iter_next(iter)
     feed_ids = feed_ids[0:-1]
     # 2º vamos a por las entries del feed...
     (model, iter) = self.treeselection2.get_selected()
     iter = model.get_iter_root() # Magic
     while iter:
      self.liststore.set_value(iter, 3, 'normal')
      iter = self.liststore.iter_next(iter)
     # ...y 3º a por los datos
     q = 'UPDATE articulo SET leido=1 WHERE id_feed IN (' + feed_ids + ')'
     cursor.execute(q)
     self.conn.commit()
     cursor.close()

  else: # La petición de toggle proviene de la lista de entries de un feed
   (model, iter) = self.treeselection2.get_selected()
   if(iter is not None): # Hay alguna fila de la lista seleccionada
    fecha = self.liststore.get_value(iter, 0)
    titulo = self.liststore.get_value(iter, 2)
    id_articulo = self.liststore.get_value(iter, 4)
    liststore_font_style = font_style = model.get(iter, 3)[0]

    if(data == 'single'):
     if(font_style == 'normal'):
      self.liststore.set_value(iter, 3, 'bold')
      #model.set(iter, 0, fecha, 2, titulo, 3, 'bold') # That sucks (it doesn't update the model)!
      cursor.execute('UPDATE articulo SET leido=0 WHERE id = ?', [id_articulo])
      self.conn.commit()
      cursor.close()
      # START NAME PARSING #
      # Y actualizar el modelo de datos.
      (model, iter) = self.treeselection.get_selected()
      rgxp = r''' \[.*\]$'''
      nombre_feed = model.get_value(iter, 0)
      m = re.search(rgxp, nombre_feed)
      if m is not None:
       nombre_feed = nombre_feed.split(' ')
       nombre_feed = ' '.join(nombre_feed[0:len(nombre_feed)-1])
       no_leidos = m.group(0).replace('[','').replace(']','').strip()
       no_leidos = int(no_leidos) + 1
       feed_label = nombre_feed + ' [' + str(no_leidos) + ']'
      else:
       feed_label = nombre_feed + ' [1]'
      model.set(iter, 0, feed_label, 3, 'bold')
      # END NAME PARSING #
       

     else: # if(font_style == 'bold')
      self.liststore.set_value(iter, 3, 'normal')
      #model.set(iter, 0, fecha, 2, titulo, 3, 'normal') # That sucks too (same crap)!
      cursor.execute('UPDATE articulo SET leido=1 WHERE id = ?', [id_articulo])
      self.conn.commit()
      cursor.close()
      # START NAME PARSING #
      # Y actualizar el modelo de datos.
      (model, iter) = self.treeselection.get_selected()
      rgxp = r''' \[.*\]$'''
      nombre_feed = model.get_value(iter, 0)
      m = re.search(rgxp, nombre_feed)
      if m is not None:
       nombre_feed = nombre_feed.split(' ')
       nombre_feed = ' '.join(nombre_feed[0:len(nombre_feed)-1])
       no_leidos = m.group(0).replace('[','').replace(']','').strip()
       no_leidos = int(no_leidos) - 1
       if no_leidos == 0: # Si no quedan entries del feed por leer...
        font_style = 'normal'
        feed_label = nombre_feed
       else:
        font_style = 'bold'
        feed_label = nombre_feed + ' [' + str(no_leidos) + ']'
       model.set(iter, 0, feed_label, 3, font_style)
       # END NAME PARSING #


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
      entry_ids += str(id_articulo)+','
      iter = self.liststore.iter_next(iter)
     entry_ids = entry_ids[0:-1]
     q = 'UPDATE articulo SET leido=' + str(leido) +' WHERE id IN (' + entry_ids + ')'
     cursor.execute(q)
     self.conn.commit()
     cursor.close()

     # START NAME PARSING #
     # Y actualizar el modelo de datos.
     (model, iter) = self.treeselection.get_selected()
     rgxp = r''' \[.*\]$'''
     nombre_feed = model.get_value(iter, 0)
     font_style = ''
     if liststore_font_style == 'bold': # Si antes era bold...
      m = re.search(rgxp, nombre_feed)
      if m is not None:
       nombre_feed = nombre_feed.split(' ')
       nombre_feed = ' '.join(nombre_feed[0:len(nombre_feed)-1])
       feed_label = nombre_feed
      else:
       feed_label = nombre_feed
      font_style = 'normal'
     elif liststore_font_style == 'normal': # Sino, si antes era normal...
      m = re.search(rgxp, nombre_feed)
      if m is not None:
       nombre_feed = nombre_feed.split(' ')
       nombre_feed = ' '.join(nombre_feed[0:len(nombre_feed)-1])
       feed_label = nombre_feed + ' [' + str(count) + ']'
      else:
       feed_label = nombre_feed + ' [' + str(count) + ']'
      font_style = 'bold'
     model.set(iter, 0, feed_label, 3, font_style)
     # END NAME PARSING #

 def abrir_browser(self, event=None, data=None):
  """Opens a given url in the user sensible web browser."""
  (model, iter) = self.treeselection2.get_selected()
  if(iter is not None): # Hay alguna fila de la lista seleccionada
   if data is not None:
    link = data
   else:
    id_articulo = self.liststore.get_value(iter, 4)
    cursor = self.conn.cursor()
    cursor.execute('SELECT enlace FROM articulo WHERE id = ?', [id_articulo])
    link = cursor.fetchone()[0]
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
    cursor.execute('SELECT enlace FROM articulo WHERE id = ?', [id_articulo])
    link = cursor.fetchone()[0]
    cursor.close()
   clipboard = gtk.clipboard_get()
   clipboard.set_text(link)
   clipboard.store()

 def htmlentitydecode(self, s):
  """Escapes htmlentities."""
  return re.sub('&(%s);' % '|'.join(name2codepoint), lambda m: unichr(name2codepoint[m.group(1)]), s)

 def list_row_selection(self, event):
  """List row change detector"""

  (model, iter) = self.treeselection2.get_selected()
  if(iter is not None): # Hay alguna fila de la lista seleccionada
   fecha = self.liststore.get_value(iter, 0)
   flag_importante = self.liststore.get_value(iter, 1)
   titulo = self.liststore.get_value(iter, 2)
   id_articulo = self.liststore.get_value(iter, 4)
   liststore_font_style = self.liststore.get_value(iter, 3)
   if liststore_font_style == 'bold':
    model.set(iter, 3, 'normal')
   
   # Coloración de la barra del título de la entry caso de ser importante
   if flag_importante:
    self.eb.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("pink"))
   else:
    self.eb.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#EDECEB"))

   # This prevents htmlentities from doing weird things to the headerlink!
   self.headerlink.set_markup('<b><u><span foreground="blue">'+xml.sax.saxutils.escape(titulo)+'</span></u></b>')

   self.headerlink.set_justify(gtk.JUSTIFY_CENTER)
   self.headerlink.set_ellipsize(pango.ELLIPSIZE_END)
   self.eb.show()
   self.eb_image_zoom.show()

   cursor = self.conn.cursor()
   # Turno de webkit...
   cursor.execute('SELECT leido,contenido FROM articulo WHERE id = ?', [id_articulo])
   row = cursor.fetchone()
   contenido = row[1]

   # Offline mode image retrieving
   if self.offline_mode == 1:
    # Reemplazar los tags img para que apunten a local...
    cursor.execute('SELECT nombre,url FROM imagen WHERE id_articulo = ?', [id_articulo])
    row2 = cursor.fetchall()
    if (row2 is not None) and (len(row2)>0):
     for img in row2:
      # Sustituir los paths de imagenes remotas por los locales!
      contenido = contenido.replace(img[1], images_path + '/' + str(img[0]))
     self.valid_links.append('file://'+images_path+'/'+str(img[0])) # Valid link for now...
     self.webview.load_string(contenido, "text/html", "utf-8", 'file://'+images_path+'/'+str(img[0]))
     self.valid_links.pop() # ...and invalid link again!
    else:
     self.webview.load_string(contenido, "text/html", "utf-8", "valid_link")
   else:
    self.webview.load_string(contenido, "text/html", "utf-8", "valid_link")

   if(row[0] == 0):
    # Si no estaba leído, marcarlo como tal.
    cursor.execute('UPDATE articulo SET leido=1 WHERE id = ?', [id_articulo])
    self.conn.commit()

   cursor.close()
   # Y actualizar el modelo de datos.
   (model, iter) = self.treeselection.get_selected()

   # START NAME PARSING #
   if liststore_font_style == 'bold': # Si la entry era bold, cabe actualizar el nodo del feed
    rgxp = r''' \[.*\]$'''
    feed_label = ''
    nombre_feed = model.get_value(iter, 0)
    m = re.search(rgxp, nombre_feed)
    if m is not None:
     nombre_feed = nombre_feed.split(' ')
     nombre_feed = ' '.join(nombre_feed[0:len(nombre_feed)-1])
     no_leidos = m.group(0).replace('[','').replace(']','').strip()
     no_leidos = int(no_leidos) - 1
     if no_leidos == 0: # Si no quedan entries del feed por leer...
      font_style = 'normal'
      feed_label = nombre_feed
     else: # Y si todavía quedan...
      font_style = 'bold'
      feed_label = nombre_feed + ' [' + str(no_leidos) + ']'
     model.set(iter, 0, feed_label, 3, font_style)
   # END NAME PARSING #
 
 def tree_row_selection(self, event):
  """Feed row change detector; triggers entry visualization on the list."""
  (model, iter) = self.treeselection.get_selected()
  if(iter is not None): # Hay algún nodo seleccionado
   row_name = self.treestore.get_value(iter, 0)
   if(model.iter_depth(iter) == 1): # Si es hoja, presentar entradas
    id_feed = self.treestore.get_value(iter, 2)
    self.populate_entries(id_feed)
    cursor = self.conn.cursor()
    cursor.execute('SELECT url FROM feed WHERE id = ?', [id_feed])
    url = cursor.fetchone()[0]
    cursor.close()
    # START NAME PARSING #
    row_name = self.simple_name_parsing(row_name)
    # END NAME PARSING #
    FEED_PAGE = "<h2>Feed: " + row_name + "</h2><p>" + _("Source") + ": <a href='" + url + "'>" + url + "</a></p>"
    self.webview.load_string(FEED_PAGE, "text/html", "utf-8", "valid_link")
   elif(model.iter_depth(iter) == 0): # Si es padre, limpliar 
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

 def statusicon_activate(self, data=None):
  """Activates the tray icon."""
  global window_visible # Global since we need to modify it

  # Deactivates tray icon blinking
  self.statusicon.set_blinking(False)

  if(window_visible):
   self.window.hide()
   (self.x, self.y) = self.window.get_position()
   window_visible = False
  else:
   self.window.move(self.x, self.y)
   self.window.show()
   window_visible = True

 def warning_message(self, str):
  """Shows a custom warning message dialog"""
  dialog = gtk.MessageDialog(self.window, (gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT), gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, str)
  dialog.run()
  dialog.destroy()

 def load_puf(self, data=None):
  """Shows the PUF/FAQ on the browser window."""
  self.scrolled_window2.set_size_request(0,0)
  self.scrolled_window2.hide()
  self.eb.hide()
  self.eb_image_zoom.hide()
  self.webview.load_string(PUF_PAGE, "text/html", "utf-8", "file://"+puf_path)

 def help_about(self, action):
  """Shows the about message dialog"""
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
  about.set_version("0.1")
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
                 <separator/><menuitem action='Import feeds'/>
                 <menuitem action='Export feeds'/>
                 <separator/>
                 <menuitem action='Quit'/>
                </menu>
                <menu action='EditMenu'>
                 <menuitem action='Edit'/>
                 <menuitem action='Preferences'/>
                </menu>
                <menu action='NetworkMenu'>
                 <menuitem action='Update'/>
                 <menuitem action='Update all'/>
                </menu>
                <menu action='HelpMenu'>
                 <menuitem action='FAQ'/>
                 <menuitem action='About'/>
                </menu>
               </menubar>
               <toolbar name='Toolbar'>
                <toolitem name='New feed' action='New feed'/>
                <toolitem name='New category' action='New category'/>
                <separator name='sep1'/>
                <toolitem name='Update all' action='Update all'/>
                <separator name='sep2'/>
                <toolitem name='Preferences' action='Preferences'/>
               </toolbar>
              </ui>"""

  # Generate a stock image from a file (http://faq.pygtk.org/index.py?req=show&file=faq08.012.htp)
  factory = gtk.IconFactory()
  pixbuf = gtk.gdk.pixbuf_new_from_file(media_path + 'SRD_RSS_Logo_mini.png')
  iconset = gtk.IconSet(pixbuf)
  factory.add('rss-image', iconset)
  factory.add_default()

  # Una opción para que se muestren los iconos en los menus (a contracorriente de Gnome):
  # gconf-editor: Desktop -> Gnome -> Interface -> menus_have_icons (y buttons_have_icons)
  ag = gtk.ActionGroup('WindowActions')
  actions = [
            ('ArchiveMenu', None, _('_Archive')),
            ('New feed', 'rss-image', _('New _feed'), '<control>F', _('Adds a feed'), self.add_feed),
            ('New category', gtk.STOCK_DIRECTORY, _('New _category'), '<control>C', _('Adds a category'), self.add_category),
            ('Delete feed', gtk.STOCK_CLEAR, _('Delete _feed'), '<alt>F', _('Deletes a feed'), self.delete_feed),
            ('Delete category', gtk.STOCK_CLOSE, _('Delete _category'), '<alt>C', _('Deletes a category'), self.delete_category),
            ('Import feeds', gtk.STOCK_REDO, _('Import feeds'), None, _('Imports a feedlist'), self.import_feeds),
            ('Export feeds', gtk.STOCK_UNDO, _('Export feeds'), None, _('Exports a feedlist'), self.export_feeds),
            ('Quit', gtk.STOCK_QUIT, _('_Quit'), '<control>Q', _('Quits'), self.delete_event),
            ('EditMenu', None, _('E_dit')),
            ('Edit', gtk.STOCK_EDIT, _('_Edit'), '<control>E', _('Edits the selected element'), self.edit),
            ('Preferences', gtk.STOCK_EXECUTE, _('_Preferences'), '<control>P', _('Shows preferences'), self.preferences),
            ('NetworkMenu', None, _('_Network')),
            ('Update', None, _('_Update'), '<control>U', _('Updates the selected feed'), self.update_feed),
            ('Update all', gtk.STOCK_REFRESH, _('U_pdate all'), '<control>P', _('Update all feeds'), self.update_all_feeds),
            ('HelpMenu', None, _('_Help')),
            ('FAQ', gtk.STOCK_HELP, _('FAQ'), None, _('FAQ'), self.load_puf),
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
   if debian == True:
    os.makedirs(os.getenv("HOME") + '/.config/naufrago/')
   else:
    os.makedirs(current_path + '/.naufrago/')

   self.conn = sqlite3.connect(db_path, check_same_thread=False)
   cursor = self.conn.cursor()
   cursor.executescript('''
     CREATE TABLE config(window_position varchar(16) NOT NULL, window_size varchar(16) NOT NULL, scroll1_size varchar(16) NOT NULL, scroll2_size varchar(16) NOT NULL, num_entries integer NOT NULL, update_freq integer NOT NULL, init_unfolded_tree integer NOT NULL, init_tray integer NOT NULL, init_update_all integer NOT NULL, offline_mode integer NOT NULL, show_trayicon integer NOT NULL, toolbar_mode integer NOT NULL);
     CREATE TABLE categoria(id integer PRIMARY KEY, nombre varchar(32) NOT NULL);
     CREATE TABLE feed(id integer PRIMARY KEY, nombre varchar(32) NOT NULL, url varchar(1024) NOT NULL, id_categoria integer NOT NULL);
     CREATE TABLE articulo(id integer PRIMARY KEY, titulo varchar(256) NOT NULL, contenido text, fecha integer NOT NULL, enlace varchar(1024) NOT NULL, leido INTEGER NOT NULL, importante INTEGER NOT NULL, imagenes TEXT, id_feed integer NOT NULL, entry_unique_id varchar(1024) NOT NULL);
     CREATE TABLE imagen(id integer PRIMARY KEY, nombre integer NOT NULL, url TEXT NOT NULL, id_articulo integer NOT NULL);
     INSERT INTO config VALUES('0,0', '600x400', '175x50', '300x150', 10, 1, 1, 0, 0, 0, 0, 0);
     INSERT INTO categoria VALUES(null, 'General');
     INSERT INTO feed VALUES(null, 'enchufado.com', 'http://enchufado.com/rss2.php', 1);''')
   self.conn.commit()
   cursor.close()
   os.makedirs(favicon_path)
   os.makedirs(images_path)
  else:
   self.conn = sqlite3.connect(db_path, check_same_thread=False)

 def get_config(self):
  """Retrieves the app configuration"""
  global ABOUT_PAGE, PUF_PAGE

  cursor = self.conn.cursor()
  cursor.execute('SELECT * FROM config')
  row = cursor.fetchone()
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

  # Cargamos un par de html's...
  f = open(index_path, 'r')
  ABOUT_PAGE = f.read()
  f.close()
  f = open(puf_path, 'r')
  PUF_PAGE = f.read()
  f.close()
  
  # Valor del lock...
  self.lock = False

 def save_config(self):
  """Saves user window configuration"""
  (x, y) = self.window.get_position()
  (w, h) = self.window.get_size()
  position = str(x)+','+str(y)
  size = str(w)+'x'+str(h)
  (a, b) = self.scrolled_window1.get_size_request()
  scroll1 = str(a)+'x'+str(b)
  (c, d) = self.scrolled_window2.get_size_request()
  scroll2 = str(c)+'x'+str(d)
  cursor = self.conn.cursor()
  cursor.execute('UPDATE config SET window_position = ?, window_size = ?, scroll1_size = ?, scroll2_size = ?, num_entries = ?, update_freq = ?, init_unfolded_tree = ?, init_tray = ?, init_update_all = ?, offline_mode = ?, show_trayicon = ?, toolbar_mode = ?', [position,size,scroll1,scroll2,self.num_entries,self.update_freq,self.init_unfolded_tree,self.init_tray,self.init_update_all,self.offline_mode,self.show_trayicon,self.toolbar_mode])
  self.conn.commit()
  cursor.close()

 def purge_entries(self):
  """Purges excedent entries from each feed. This is called from Preferences
     dialog if the number of entries per feed is shrunk."""
  updated_feed_ids = []
  cursor = self.conn.cursor()
  cursor.execute('SELECT id FROM feed')
  feeds = cursor.fetchall()
  for row in feeds:
   cursor.execute('SELECT id FROM articulo WHERE id_feed = ? AND importante = 0 ORDER BY fecha DESC LIMIT ?,1000000', [row[0],self.num_entries])
   articles = cursor.fetchall()
   if articles is not None:
    id_articulos = ''
    for art in articles:
     id_articulos += str(art[0])+','
     # Aprovechamos el bucle para borrar las imagenes del filesystem, si procede.
     # Ojo, porque cabe controlar que esa imagen no sea usada también por otro artículo,
     # dado que éstas se comparten entre artículos si son la misma.
     cursor.execute('SELECT id FROM imagen WHERE id_articulo = ?', [art[0]])
     images = cursor.fetchall()
     for i in images:
      cursor.execute('SELECT count(nombre) FROM imagen WHERE nombre = ?', [i[0]])
      row3 = cursor.fetchone()
      if (row3 is not None) and (row3[0] <= 1):
       if os.path.exists(images_path + '/'+ str(i[0])):
        os.unlink(images_path + '/'+ str(i[0]))
    id_articulos = id_articulos[0:len(id_articulos)-1]

    cursor.execute('DELETE FROM imagen WHERE id_articulo IN ('+id_articulos+')')
    cursor.execute('DELETE FROM articulo WHERE id IN ('+id_articulos+')')
    self.conn.commit()
    cursor.close()
    updated_feed_ids.append(row[0])

  if len(updated_feed_ids)>0:
   self.liststore.clear()
   self.treestore.clear()
   self.scrolled_window2.set_size_request(0,0)
   self.scrolled_window2.hide()
   self.eb.hide()
   self.eb_image_zoom.hide()
   self.populate_feeds()
   self.webview.load_string(ABOUT_PAGE, "text/html", "utf-8", "file://"+index_path)
   if(self.init_unfolded_tree == 1): self.treeview.expand_all()

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
  self.vbox.pack_start(self.toolbar, expand=False)
  # Creación del HPaned.
  self.hpaned = gtk.HPaned()
  self.hpaned.set_border_width(2)
  # Creación del Tree izquierdo para los feeds
  # Campos: nombre, icono, id_categoria
  self.treestore = gtk.TreeStore(str, str, int, str)
  self.populate_feeds() # Propaga los feeds del usuario
  # Create the TreeView using treestore
  self.treeview = gtk.TreeView(self.treestore)
  # Control de eventos de ratón y teclado del tree.
  self.treeview.connect("button_press_event", self.tree_button_press_event)
  self.treeview.connect("key_press_event", self.tree_key_press_event)
  self.treeview.connect("row-activated", self.tree_row_activated)
  self.treeselection = self.treeview.get_selection()
  self.treeselection.connect("changed", self.tree_row_selection)
  self.tvcolumn = gtk.TreeViewColumn('Feeds')
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
  # Allow sorting on the column
  self.tvcolumn.set_sort_column_id(0)
  # Allow drag and drop reordering of rows
  self.treeview.set_reorderable(True)
  self.treeview_setup_dnd(self.treeview)
  self.scrolled_window1 = gtk.ScrolledWindow()
  self.scrolled_window1.add(self.treeview)
  self.scrolled_window1.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
  self.scrolled_window1.set_size_request(175,50) # Sets an acceptable tree sizing
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
  self.tvcolumn_titulo.set_sort_column_id(2)
  self.scrolled_window2 = gtk.ScrolledWindow()
  self.scrolled_window2.add(self.treeview2)
  self.scrolled_window2.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
  self.scrolled_window2.set_size_request(300,150) # Sets an acceptable list sizing
  self.vpaned.add1(self.scrolled_window2)

  ###########
  # PARTE 3 #
  ###########
  self.scrolled_window3 = gtk.ScrolledWindow()
  self.scrolled_window3.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
  self.webview = webkit.WebView()
  self.webview.set_full_content_zoom(True)
  self.webview.load_string(ABOUT_PAGE, "text/html", "utf-8", "file://"+index_path)
  self.webview.connect_after("populate-popup", self.create_webview_popup)
  # Open in new browser handler (this intercepts all requests)
  self.valid_links = ['valid_link', 'file://'+index_path, 'file://'+puf_path] # Valid links to browse
  for i in range(1,19):
   self.valid_links.append('file://'+puf_path+'#'+str(i))
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

  ###########
  # PARTE 4 #
  ###########
  self.hbox2 = gtk.HBox(homogeneous=False, spacing=0)
  self.throbber = gtk.Image()
  self.throbber.set_from_file(app_path + 'media/throbber.gif')
  self.hbox2.pack_start(self.throbber, expand=False, fill=False, padding=0)
  self.statusbar = gtk.Label("")
  self.statusbar.set_justify(gtk.JUSTIFY_LEFT)
  self.statusbar.set_ellipsize(pango.ELLIPSIZE_END)
  ###self.statusbar.set_alignment(xalign=0, yalign=0)
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
   self.statusbar.set_text(data)
  else:
   self.statusbar.set_text("")

 def check_init_options(self):
  """Checks & applies init options."""
  if(self.init_unfolded_tree == 1): self.treeview.expand_all()
  if(self.init_tray == 1): self.statusicon_activate()
  if(self.init_update_all == 1): self.update_all_feeds()

 def create_trayicon(self):
  """Creates the TrayIcon of the app and its popup menu."""
  self.statusicon = gtk.StatusIcon()
  self.statusicon.set_tooltip('Náufrago!')
  self.statusicon.set_from_file(media_path + 'Viking_Longship.svg')
  self.statusicon.set_visible(True)
  self.window.connect('hide', self.statusicon_activate) # Hide window associated
  self.statusicon.connect('activate', self.statusicon_activate) # StatusIcon associated

  # StatusIcon popup menu
  self.statusicon_menu = gtk.Menu()
  # Create the menu items
  update_item = gtk.ImageMenuItem(_("Update all"))
  icon = update_item.render_icon(gtk.STOCK_REFRESH, gtk.ICON_SIZE_BUTTON)
  update_item.set_image(gtk.image_new_from_pixbuf(icon))
  quit_item = gtk.ImageMenuItem(_("Quit"))
  icon = quit_item.render_icon(gtk.STOCK_QUIT, gtk.ICON_SIZE_BUTTON)
  quit_item.set_image(gtk.image_new_from_pixbuf(icon))
  # Add them to the menu
  self.statusicon_menu.append(update_item)
  self.statusicon_menu.append(quit_item)
  # Attach the callback functions to the activate signal
  update_item.connect("activate", self.update_all_feeds)
  quit_item.connect("activate", self.delete_event)
  self.statusicon_menu.show_all()
  self.statusicon.connect('popup-menu', self.statusicon_popup_menu)

 def statusicon_popup_menu(self, statusicon, button, time):
  """StatusIcon popup menu launcher."""
  self.statusicon_menu.popup(None, None, None, button, time, self)

 def populate_feeds(self):
  """Obtains the user feed tree structure"""
  self.populate_favicons() # Populate all favicons we have prior to use them

  cursor = self.conn.cursor()
  cursor.execute('SELECT id,nombre FROM categoria ORDER BY nombre ASC')
  rows = cursor.fetchall()
  for row in rows:
   dad = self.treestore.append(None, [row[1], gtk.STOCK_OPEN, row[0], 'normal']) # Initial tree creation
   cursor.execute('SELECT id,nombre FROM feed WHERE id_categoria = ' + str(row[0]) + ' ORDER BY nombre ASC')
   rows2 = cursor.fetchall()
   for row2 in rows2:
    cursor.execute('SELECT count(id) FROM articulo WHERE id_feed = ' + str(row2[0]) + ' AND leido = 0')
    row3 = cursor.fetchone()
    if row3[0] == 0:
     feed_label = row2[1]
     font_style = 'normal'
    else:
     feed_label = row2[1] + ' [' + str(row3[0]) + ']'
     font_style = 'bold'
    if os.path.exists(favicon_path + '/' + str(row2[0])):
     son = self.treestore.append(dad, [feed_label, str(row2[0]), row2[0], font_style]) # Initial tree creation
    else:
     son = self.treestore.append(dad, [feed_label, 'rss-image', row2[0], font_style]) # Initial tree creation
  cursor.close()

 def populate_entries(self, id_feed):
  """Obtains the entries of the selected feed"""
  font_style=''
  importante=False
  self.liststore.clear()
  cursor = self.conn.cursor()
  cursor.execute('SELECT id,titulo,fecha,leido,importante FROM articulo WHERE id_feed = ? ORDER BY fecha DESC', [int(id_feed)])
  rows = cursor.fetchall()
  cursor.close()
  
  for row in rows:
   now = datetime.datetime.now().strftime("%Y-%m-%d")
   fecha = datetime.datetime.fromtimestamp(row[2]).strftime("%Y-%m-%d")
   if now == fecha: fecha = _('Today')
   if row[3] == 1: font_style='normal'
   else: font_style='bold'
   if row[4] == 1: importante=True
   else: importante=False
   self.liststore.append([fecha, importante, self.htmlentitydecode(row[1]), font_style, row[0]])

  # Si no hay entries, no queremos su panel!
  if (rows is None) or (len(rows) == 0):
   self.scrolled_window2.set_size_request(0,0)
   self.scrolled_window2.hide()
  else:
   self.scrolled_window2.set_size_request(300,150)
   self.scrolled_window2.show()

 def add_category(self, data=None):
  """Adds/edits a category to/from the user feed tree structure"""
  dialog = gtk.MessageDialog(self.window, (gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT), gtk.MESSAGE_QUESTION, gtk.BUTTONS_OK_CANCEL, None)
  entry = gtk.Entry(max=32)

  if((data is not None) and (type(data) is not gtk.Action)): # Modo edición I
   cursor = self.conn.cursor()
   cursor.execute('SELECT nombre FROM categoria WHERE id = ?', [data])
   nombre_categoria = cursor.fetchone()[0]
   cursor.close()
   entry.set_text(nombre_categoria)
   dialog.set_title(_('Edit category'))
   dialog.set_markup(_('Change <b>category</b> name to:'))
  else:
   dialog.set_title(_('Add category'))
   dialog.set_markup(_('Please, insert the <b>category</b>:'))

  # These are for 'capturing Enter' as OK
  dialog.set_default_response(gtk.RESPONSE_OK) # Sets default response
  entry.set_activates_default(True) # Activates default response

  dialog.vbox.pack_end(entry, True, True, 0)
  dialog.show_all()
  response = dialog.run()
  text = entry.get_text()
  dialog.destroy()

  if((text != '') and (response == gtk.RESPONSE_OK)):
   cursor = self.conn.cursor()
   # Create category in the database (if it does not exist!)
   cursor.execute('SELECT id FROM categoria WHERE nombre = ?', [text.decode("utf-8")])
   if(cursor.fetchone() is None):
    if((data is not None) and (type(data) is not gtk.Action)): # Modo edición II
     cursor.execute('SELECT nombre FROM categoria WHERE id = ?', [data])
     nombre_categoria = cursor.fetchone()[0]
     if(text != nombre_categoria):
      cursor.execute('UPDATE categoria SET nombre = ? WHERE id = ?', [text.decode("utf-8"),data])
      (model, iter) = self.treeselection.get_selected()
      model.set(iter, 0, text)
    else:
     cursor.execute('SELECT MAX(id) FROM categoria')
     row = cursor.fetchone()
     dad = self.treestore.append(None, [text, gtk.STOCK_OPEN, row[0]+1, 'normal'])
     cursor.execute('INSERT INTO categoria VALUES(null, ?)', [text.decode("utf-8")])
    self.conn.commit()
   cursor.close()

 def delete_category(self, data=None):
  """Deletes a category from the user feed tree structure"""
  (model, iter) = self.treeselection.get_selected()
  if(iter is not None): # Si hay algún nodo seleccionado...
   if(model.iter_depth(iter) == 0): # ... y es un nodo padre
    id_categoria = self.treestore.get_value(iter, 2)
    if(id_categoria != 1):
     dialog = gtk.MessageDialog(self.window, (gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT), gtk.MESSAGE_QUESTION, gtk.BUTTONS_OK_CANCEL, None)
     dialog.set_title(_('Delete category'))
     dialog.set_markup(_('Delete the selected <b>category</b>?'))
     dialog.format_secondary_markup(_('<b>Atention:</b> all contained RSS will be also deleted. Proceed?'))
     dialog.show_all()
     response = dialog.run()
     dialog.destroy()

     if(response == gtk.RESPONSE_OK):
      # De cara al model, esto es suficiente :-o
      result = self.treestore.remove(iter)
      cursor = self.conn.cursor()
      cursor.execute('SELECT id FROM feed WHERE id_categoria = ?', [id_categoria])
      feeds = cursor.fetchall()
      for feed in feeds:
       if os.path.exists(favicon_path + '/'+ str(feed[0])):
        os.unlink(favicon_path + '/'+ str(feed[0]))
       cursor.execute('SELECT id FROM articulo WHERE id_feed = ?', [feed[0]])
       articles = cursor.fetchall()
       for art in articles:
        cursor.execute('SELECT id,nombre FROM imagen WHERE id_articulo = ?', [art[0]])
        images = cursor.fetchall()
        for i in images:
         cursor.execute('SELECT count(id) FROM imagen WHERE nombre = ?', [i[1]])
         row3 = cursor.fetchone()
         if (row3 is not None) and (row3[0] <= 1):
          if os.path.exists(images_path + '/'+ str(i[1])):
           os.unlink(images_path + '/'+ str(i[1]))
        cursor.execute('DELETE FROM imagen WHERE id_articulo = ?', [art[0]])
        self.conn.commit()
       cursor.execute('DELETE FROM articulo WHERE id_feed = ?', [feed[0]])
       self.conn.commit()
      cursor.execute('DELETE FROM feed WHERE id_categoria = ?', [id_categoria])
      cursor.execute('DELETE FROM categoria WHERE id = ?', [id_categoria])
      self.conn.commit()
      # Finalmente ponemos las cosas en su sitio
      self.webview.load_string(ABOUT_PAGE, "text/html", "utf-8", "file://"+index_path)
      self.scrolled_window2.set_size_request(0,0)
      self.scrolled_window2.hide()
      cursor.close()
    else:
     self.warning_message(_('The General category cannot be deleted!'))
   else:
    self.warning_message(_('You must choose a category folder!'))
  else:
   self.warning_message(_('You must choose a category folder!'))

 def add_feed(self, data=None):
  """Adds a feed to the user feed tree structure"""
  dialog = gtk.MessageDialog(self.window, (gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT), gtk.MESSAGE_QUESTION, gtk.BUTTONS_OK_CANCEL, None)
  entryName = gtk.Entry(max=32)
  entryURL = gtk.Entry(max=1024)
  labelName = gtk.Label(_('Name '))

  new = False
  if((data is not None) and (type(data) is not gtk.Action)): #  Modo edición I
   labelURL = gtk.Label('URL       ')
   cursor = self.conn.cursor()
   cursor.execute('SELECT url,nombre FROM feed WHERE id = ?', [data])
   row = cursor.fetchone()
   cursor.close()
   entryName.set_text(row[1])
   entryURL.set_text(row[0])
   dialog.set_title(_('Edit feed'))
   dialog.set_markup(_('Change <b>feed</b> data:'))
  else:
   labelURL = gtk.Label('URL ')
   dialog.set_title(_('Add feed'))
   dialog.set_markup(_('Please, insert <b>feed</b> data:'))
   new = True

  hbox1 = gtk.HBox()
  hbox1.pack_start(labelName, True, True, 0)
  hbox1.pack_start(entryName, True, True, 0)
  dialog.vbox.pack_start(hbox1, True, True, 0)
  hbox2 = gtk.HBox()
  hbox2.pack_start(labelURL, True, True, 0)
  hbox2.pack_start(entryURL, True, True, 0)
  dialog.vbox.pack_start(hbox2, True, True, 0)
  # These are for 'capturing Enter' as OK
  dialog.set_default_response(gtk.RESPONSE_OK) # Sets default response
  entryName.set_activates_default(True) # Activates default response for this entry
  entryURL.set_activates_default(True) # Activates default response for this entry
  dialog.show_all()

  if new == True:
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

  if((textName != '') and (textURL != '') and (response == gtk.RESPONSE_OK)):
   cursor = self.conn.cursor()
   (model, iter) = self.treeselection.get_selected()
   if((data is not None) and (type(data) is not gtk.Action)): # Modo edición III
    cursor.execute('SELECT count(id) FROM articulo WHERE id_feed = ' + str(data) + ' AND leido = 0')
    row = cursor.fetchone()
    if row[0] == 0:
     feed_label = textName
    else:
     feed_label = textName + ' [' + str(row[0]) + ']'
    cursor.execute('UPDATE feed SET nombre = ?,url = ? WHERE id = ?', [textName.decode("utf-8"),textURL.decode("utf-8"),data])
    self.conn.commit()
    model.set(iter, 0, feed_label)
   else:
    # Create feed in the database (if it does not exist!)
    cursor.execute('SELECT id FROM feed WHERE url = ?', [textURL.decode("utf-8")])
    if(cursor.fetchone() is None):
     # Lo colocamos en la categoría seleccionada, o en 'General' (default) si no la hubiere
     id_categoria = 1
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
     cursor.execute('SELECT MAX(id) FROM feed')
     row = cursor.fetchone()
     id_feed = 0
     if row[0] is not None:
      id_feed = row[0]
     self.get_favicon(id_feed+1, textURL) # Downloads favicon & adds to the icon factory.
     son = self.treestore.append(iter, [textName, str(id_feed+1), id_feed+1, 'normal'])
     self.treeview.expand_row(model.get_path(iter), open_all=False) # Expand parent!
     cursor.execute('INSERT INTO feed VALUES(null, ?, ?, ?)', [textName.decode("utf-8"),textURL.decode("utf-8"),id_categoria])
     self.conn.commit()
     self.treeselection.select_iter(son)
     self.update_feed(data=None, new=True)
   cursor.close()

 def delete_feed(self, data=None):
  """Deletes a feed from the user feed tree structure"""
  (model, iter) = self.treeselection.get_selected()
  if(iter is not None): # Si hay algún nodo seleccionado...
   if(model.iter_depth(iter) == 1): # ... y es un nodo hijo
    dialog = gtk.MessageDialog(self.window, (gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT), gtk.MESSAGE_QUESTION, gtk.BUTTONS_OK_CANCEL, None)
    dialog.set_title(_('Delete feed'))
    dialog.set_markup(_('Delete selected <b>feed</b>?'))
    dialog.show_all()
    response = dialog.run()
    dialog.destroy()

    if(response == gtk.RESPONSE_OK):
     text = self.treestore.get_value(iter, 0)
     id_feed = self.treestore.get_value(iter, 2)
     result = self.treestore.remove(iter)
     self.liststore.clear() # Limpieza de tabla de entries/articulos
     cursor = self.conn.cursor()

     cursor.execute('SELECT id FROM articulo WHERE id_feed = ?', [id_feed])
     articles = cursor.fetchall()
     for art in articles:
      cursor.execute('SELECT id,nombre FROM imagen WHERE id_articulo = ?', [art[0]])
      images = cursor.fetchall()
      for i in images:
       cursor.execute('SELECT count(id) FROM imagen WHERE nombre = ?', [i[1]])
       row3 = cursor.fetchone()
       if (row3 is not None) and (row3[0] <= 1):
        if os.path.exists(images_path + '/'+ str(i[1])):
         os.unlink(images_path + '/'+ str(i[1]))
      cursor.execute('DELETE FROM imagen WHERE id_articulo = ?', [art[0]])
      self.conn.commit()
     cursor.execute('DELETE FROM articulo WHERE id_feed = ?', [id_feed])
     cursor.execute('DELETE FROM feed WHERE id = ?', [id_feed])
     self.conn.commit()
     cursor.close()
     if os.path.exists(favicon_path + '/'+ str(id_feed)):
      os.unlink(favicon_path + '/'+ str(id_feed))
     # Finalmente ponemos las cosas en su sitio
     self.webview.load_string(ABOUT_PAGE, "text/html", "utf-8", "file://"+index_path)
     self.scrolled_window2.set_size_request(0,0)
     self.scrolled_window2.hide()
   else:
    self.warning_message(_('You must choose a feed!'))
  else:
   self.warning_message(_('You must choose a feed!'))

 def delete(self, data=None):
  """Summons deleting feed or category, depending on selection."""
  (model, iter) = self.treeselection.get_selected()
  if(iter is not None): # Si hay algún nodo seleccionado...
   if(model.iter_depth(iter) == 0): # Si es un nodo padre...
    self.delete_category()
   if(model.iter_depth(iter) == 1): # ... y es un nodo hijo
    self.delete_feed()

 def edit(self, data=None):
  """Edits a tree node, whether it is root or leaf."""
  (model, iter) = self.treeselection.get_selected()
  if(iter is not None): # Si hay algún nodo seleccionado...
   id_categoria_o_feed = model.get_value(iter, 2)
   if(model.iter_depth(iter) == 0): # ... y es un nodo padre
    if(id_categoria_o_feed != 1):
     self.add_category(id_categoria_o_feed)
    else:
     self.warning_message(_('The General category cannot be edited!'))
   elif(model.iter_depth(iter) == 1): # ... y es un nodo hijo
    self.add_feed(id_categoria_o_feed)
  else:
   self.warning_message(_('You must choose a category or a feed to edit!'))

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

 def trayicon_toggle(self, checkboxparent, checkboxchild):
  """Controlls the linked trayicon checkboxes of the preferences dialog.."""
  if checkboxparent.get_active():
   checkboxchild.set_sensitive(True)
  else:
   checkboxchild.set_active(False)
   checkboxchild.set_sensitive(False)

 def preferences(self, data=None):
  """Preferences dialog."""
  dialog = gtk.Dialog(_("Preferences"), self.window, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                   (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
  dialog.set_size_request(250,200)
  dialog.set_border_width(2)
  dialog.set_resizable(False)
  dialog.set_has_separator(False)
 
  notebook = gtk.Notebook()
  notebook.set_tab_pos(gtk.POS_TOP)

  vbox2 = gtk.VBox(homogeneous=True)
  align = gtk.Alignment()
  align.set_padding(10, 0, 15, 0)
  checkbox = gtk.CheckButton(_("Start with unfolded tree"))
  if(self.init_unfolded_tree == 1): checkbox.set_active(True)
  else: checkbox.set_active(False)
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
  align.add(vbox2)
  notebook.append_page(align, gtk.Label(_("Start")))

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
  label2 = gtk.Label(_("Update every (in hours)"))
  hbox2.pack_start(label2, True, True, 2)
  # Spin button 2
  adjustment2 = gtk.Adjustment(value=1, lower=1, upper=24, step_incr=1, page_incr=1, page_size=0)
  spin_button2 = gtk.SpinButton(adjustment=adjustment2, climb_rate=0.0, digits=0)
  spin_button2.set_numeric(numeric=True) # Only numbers can be typed
  spin_button2.set_update_policy(gtk.UPDATE_IF_VALID) # Only update on valid changes
  spin_button2.set_value(self.update_freq)
  hbox2.pack_start(spin_button2, True, True, 2)
  vbox3.pack_start(hbox2, True, True, 5)

  checkbox0 = gtk.CheckButton(_("Offline mode (slower!)"))
  if(self.offline_mode == 1): checkbox0.set_active(True)
  else: checkbox0.set_active(False)
  vbox3.pack_start(checkbox0, True, True, 5)
  align2.add(vbox3)
  notebook.append_page(align2, gtk.Label(_("Feeds & articles")))

  vbox4 = gtk.VBox(homogeneous=True)
  align3 = gtk.Alignment()
  align3.set_padding(10, 0, 15, 0)
  checkbox1 = gtk.CheckButton(_("Show icon in tray"))
  checkbox1.connect('toggled', self.trayicon_toggle, checkbox2)
  if(self.show_trayicon == 1): checkbox1.set_active(True)
  else: checkbox1.set_active(False)
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
  hbox3.pack_start(combobox, True, True, 2)
  vbox4.pack_start(hbox3, True, True, 5)
  align3.add(vbox4)
  notebook.append_page(align3, gtk.Label(_("Interface")))

  dialog.vbox.pack_start(notebook)
  dialog.show_all()
  response = dialog.run() # Dialog loop
  dialog.destroy()

  if(response == gtk.RESPONSE_ACCEPT):
   # Purge excedent entries in case of decreasing their number in configuration
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

   if checkbox1.get_active() and self.show_trayicon == 0:
    self.show_trayicon = 1
    self.statusicon.set_visible(True)
   elif not checkbox1.get_active() and self.show_trayicon == 1:
    self.show_trayicon = 0
    self.statusicon.set_visible(False)
   #if(checkbox1.get_active()): self.show_trayicon = 1
   #else: self.show_trayicon = 0
   self.save_config()

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
  parent_value = str(model.get_value(target, 0))
  row_value = str(model.get_value(source_row.iter, 0))
  row_value = self.simple_name_parsing(row_value)
  cursor.execute('UPDATE feed SET id_categoria = (SELECT id FROM categoria WHERE nombre = ?) WHERE id = (SELECT id FROM feed WHERE nombre = ?)', [parent_value,row_value])
  self.conn.commit()
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

  iter_to_copy_value = model.get_value(iter_to_copy, 0)
  target_iter_value = model.get_value(target_iter, 0)

  path_of_iter_to_copy = model.get_path(iter_to_copy)
  path_of_target_iter = model.get_path(target_iter)

  if((path_of_target_iter[0:len(path_of_iter_to_copy)] == path_of_iter_to_copy) or # anti-recursive
    (len(path_of_iter_to_copy) == 1) or # source is parent
    (len(path_of_target_iter) == 2) or # dest is child
    (self.treestore.is_ancestor(target_iter, iter_to_copy))): # dest is already child's parent
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
   time = event.time
   pthinfo = treeview.get_path_at_pos(x, y)
   if pthinfo is not None:
    path, col, cellx, celly = pthinfo
    treeview.grab_focus()
    treeview.set_cursor(path, col, 0)

    tree_menu = gtk.Menu()
    # Create the menu items
    toggle_todos_leido_item = gtk.ImageMenuItem(_("Mark all as read"))
    icon = toggle_todos_leido_item.render_icon(gtk.STOCK_SELECT_ALL, gtk.ICON_SIZE_BUTTON)
    toggle_todos_leido_item.set_image(gtk.image_new_from_pixbuf(icon))
    update_item = gtk.ImageMenuItem(_("Update"))
    icon = update_item.render_icon(gtk.STOCK_REFRESH, gtk.ICON_SIZE_BUTTON)
    update_item.set_image(gtk.image_new_from_pixbuf(icon))
    if self.lock == True: update_item.set_sensitive(False)

    edit_item = gtk.ImageMenuItem(_("Edit"))
    icon = edit_item.render_icon(gtk.STOCK_EDIT, gtk.ICON_SIZE_BUTTON)
    edit_item.set_image(gtk.image_new_from_pixbuf(icon))
    if self.lock == True: edit_item.set_sensitive(False)

    delete_item = gtk.ImageMenuItem(_("Delete"))
    icon = delete_item.render_icon(gtk.STOCK_CLOSE, gtk.ICON_SIZE_BUTTON)
    delete_item.set_image(gtk.image_new_from_pixbuf(icon))
    if self.lock == True: delete_item.set_sensitive(False)

    separator = gtk.SeparatorMenuItem()
    new_feed_item = gtk.ImageMenuItem(_("New feed"))
    icon = new_feed_item.render_icon(gtk.STOCK_FILE, gtk.ICON_SIZE_BUTTON)
    new_feed_item.set_image(gtk.image_new_from_pixbuf(icon))
    new_category_item = gtk.ImageMenuItem(_("New category"))
    icon = new_category_item.render_icon(gtk.STOCK_DIRECTORY, gtk.ICON_SIZE_BUTTON)
    new_category_item.set_image(gtk.image_new_from_pixbuf(icon))
    # Add them to the menu
    tree_menu.append(toggle_todos_leido_item)
    tree_menu.append(update_item)
    tree_menu.append(edit_item)
    tree_menu.append(delete_item)
    tree_menu.append(separator)
    tree_menu.append(new_feed_item)
    tree_menu.append(new_category_item)
    # Attach the callback functions to the activate signal
    toggle_todos_leido_item.connect("activate", self.toggle_leido, 'tree')
    update_item.connect_object("activate", self.update_feed, None)
    edit_item.connect_object("activate", self.edit, None)
    delete_item.connect_object("activate", self.delete, None)
    new_feed_item.connect_object("activate", self.add_feed, None)
    new_category_item.connect_object("activate", self.add_category, None)
    tree_menu.show_all()
    tree_menu.popup(None, None, None, event.button, event.get_time())
   return True

 def tree2_button_press_event(self, treeview, event):
  """Fires the tree2 menu popup. This one handles entries options."""
  if event.button == 3:
   x = int(event.x)
   y = int(event.y)
   time = event.time
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
    self.scrolled_window1.set_size_request(175,50)
    self.scrolled_window1.show()
    self.scrolled_window2.set_size_request(300,150)
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
   cursor.execute('SELECT enlace FROM articulo WHERE id = ?', [id_articulo])
   link = cursor.fetchone()[0]
   cursor.close()
   self.statusbar.set_text(link)

 def headerlink_mouse_leave(self, widget, event):
  """Hides the link the headerlink points to in the statusbar."""
  self.statusbar.set_text("")

 def update_feed(self, data=None, new=False):
  """Updates a single (selected) feed or the ones from a (selected) category, if any."""
  (model, iter) = self.treeselection.get_selected()
  if(iter is not None): # Si hay algún nodo seleccionado...
   nodes = {} # Dictionary! (key:value pairs containing id_feed:iter)
   if(model.iter_depth(iter) == 0): # Si es un nodo padre...
    # Update all feeds of this category
    iter = model.iter_children(iter)
    while iter:
     id_feed = self.treestore.get_value(iter, 2)
     nodes[id_feed] = iter # Storing id_feed:iter pairs...
     iter = self.treestore.iter_next(iter)
    # Old way: self.get_feed(feed_ids)
   elif(model.iter_depth(iter) == 1): # Si es un nodo hijo...
    # Update this single feed
    id_feed = self.treestore.get_value(iter, 2)
    nodes[id_feed] = iter # Storing id_feed:iter pairs...
    # Old way: self.get_feed(id_feed)
   # New way:
   t = threading.Thread(target=self.get_feed, args=(nodes,new, ))
   t.start()

 def update_all_feeds(self, data=None):
  """Updates all feeds (no complications!)."""
  # Old way: self.get_feed()
  # New way:
  if self.lock == False: # This prevents autoupdate from launching if an update is alredy in progress...
   t = threading.Thread(target=self.get_feed, args=())
   t.start()
  return True

 def check_feed_item(self, dentry):
  """Sets a default value for feed items if there's not any. Helper function of get_feed()."""
  if(hasattr(dentry,'date_parsed')):
   dp = dentry.date_parsed
   secs = time.mktime(datetime.datetime(dp[0], dp[1], dp[2], dp[3], dp[4], dp[5], dp[6]).timetuple())
  else:
   split = str(datetime.datetime.now()).split(' ')
   ds = split[0].split('-')
   ts = split[1].split(':')
   t = datetime.datetime(int(ds[0]), int(ds[1]), int(ds[2]), int(ts[0]), int(ts[1]), int(float(ts[2])))
   secs = time.mktime(t.timetuple())
  if(hasattr(dentry,'title')): title = dentry.title.encode("utf-8")
  else: title = _('Without title')
  if(hasattr(dentry,'description')): description = dentry.description.encode("utf-8")
  else: description = ''
  if(hasattr(dentry,'link')): link = dentry.link.encode("utf-8")
  else: link = _('Without link')
  if(hasattr(dentry,'id')):
   id = dentry.id.encode("utf-8")
  else:
   if description != '':
    id = hashlib.md5(description).hexdigest().encode("utf-8")
   else:
    id = hashlib.md5(title).hexdigest().encode("utf-8")

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
   cursor.execute('SELECT nombre FROM imagen WHERE url = ?', [i])
   row = cursor.fetchone()
   if(row is None):
    # a) Si no existe, guarda entrada en tabla imagen y descarga físicamente la imagen a /imagenes.
    self.statusbar.set_text(_('Obtaining image ') + i + '...')
    cursor.execute('SELECT MAX(id) FROM imagen')
    id_entry_max = cursor.fetchone()[0]
    if id_entry_max is None: id_entry_max = 1
    else: id_entry_max += 1
    cursor.execute('INSERT INTO imagen VALUES(null, ?, ?, ?)', [id_entry_max,i,id_articulo])
    self.conn.commit()
    try:
     web_file = urllib2.urlopen(i)
     image = images_path + '/' + str(id_entry_max)
     local_file = open(image, 'w')
     local_file.write(web_file.read())
     local_file.close()
     web_file.close()
    except:
     pass
    self.statusbar.set_text('')
   else:
    # b) Si existe, comprobamos que no sea una entrada repe...
    cursor.execute('INSERT INTO imagen VALUES(null, ?, ?, ?)', [row[0],i,id_articulo])
    self.conn.commit()
  cursor.close()

 def toggle_menuitems_sensitiveness(self, enable):
  """Enables/disables some menuitems while getting feeds to avoid
     multiple instances running or race conditions."""
  item_list = ["/Menubar/ArchiveMenu/Delete feed", "/Menubar/ArchiveMenu/Delete category",
               "/Menubar/ArchiveMenu/Import feeds", "/Menubar/ArchiveMenu/Quit",
               "/Menubar/EditMenu/Edit", "/Menubar/EditMenu/Preferences",
               "/Menubar/NetworkMenu/Update", "/Menubar/NetworkMenu/Update all",
               "/Toolbar/Update all", "/Toolbar/Preferences"]

  for item in item_list:
   widget = self.ui.get_widget(item)
   widget.set_sensitive(enable)
  self.statusicon_menu.set_sensitive(enable)
  self.lock = not enable

 def get_feed(self, data=None, new=False):
  """Obtains & stores the feeds (thanks feedparser!). This function is, in some way,
     the heart of the app. Maybe it should be splitted in subfunctions in order to
     don't turn mad."""
  self.toggle_menuitems_sensitiveness(enable=False)
  gtk.gdk.threads_enter()
  self.throbber.show()
  new_posts = False # Reset

  if(data is None): # Iterarlo todo

   (model, iter) = self.treeselection.get_selected() # We only want the model here...
   iter = model.get_iter_root() # Magic
   cursor = self.conn.cursor()
   while iter is not None:
    if(model.iter_depth(iter) == 0): # Si es padre
     for i in range(model.iter_n_children(iter)):
      child = model.iter_nth_child(iter, i)

      # START NAME PARSING #
      nombre_feed = model.get_value(child, 0)
      nombre_feed = self.simple_name_parsing(nombre_feed)
      # END NAME PARSING #

      id_feed = model.get_value(child, 2)
      # Primero obtenemos el feed (los datos)...
      cursor.execute('SELECT url FROM feed WHERE id = ?', [id_feed])
      url = cursor.fetchone()[0]
      self.statusbar.set_text(_('Obtaining feed ') + nombre_feed + '...')
      d = feedparser.parse(url)
      feed_link = ''
      if(hasattr(d.feed,'link')): feed_link = d.feed.link.encode('utf-8')

      limit = count = len(d.entries)
      if count > self.num_entries:
       limit = self.num_entries
      # Check for article existence...
      for i in range(0, limit):
       (secs, title, description, link, id) = self.check_feed_item(d.entries[i])
       cursor.execute('SELECT id FROM articulo WHERE entry_unique_id = ? AND id_feed = ?', [id.decode("utf-8"),id_feed])
       unique = cursor.fetchone()
       images = ''
       # Non-existant entry? Insert!
       if(unique is None):
        # Check first is the feed is full
        cursor.execute('SELECT count(id) FROM articulo WHERE id_feed = ? AND importante = 0', [id_feed])
        row2 = cursor.fetchone()
        if((row2 is not None) and (row2[0]>=self.num_entries)):
         cursor.execute('SELECT id,fecha FROM articulo WHERE importante = 0 AND id_feed = ? ORDER BY fecha ASC LIMIT 1', [id_feed])
         id_articulo, fecha = cursor.fetchone()
         if secs > fecha:
          # If so, do some purging first...
          # Ahora borramos las imagenes del filesystem, si procede
          cursor.execute('SELECT id FROM imagen WHERE id_articulo = ?', [id_articulo])
          images = cursor.fetchall()
          for i in images:
           cursor.execute('SELECT count(nombre) FROM imagen WHERE nombre = ?', [i[0]])
           row3 = cursor.fetchone()
           if (row3 is not None) and (row3[0] <= 1):
            if os.path.exists(images_path + '/'+ str(i[0])):
             os.unlink(images_path + '/'+ str(i[0]))
          cursor.execute('DELETE FROM imagen WHERE id_articulo = ?', [id_articulo])
          cursor.execute('DELETE FROM articulo WHERE id = ?', [id_articulo])
          self.conn.commit()
          images = self.find_entry_images(feed_link, description)
          cursor.execute('INSERT INTO articulo VALUES(null, ?, ?, ?, ?, 0, 0, ?, ?, ?)', [title.decode("utf-8"),description.decode("utf-8"),secs,link.decode("utf-8"),images,id_feed,id.decode("utf-8")])
          self.conn.commit()
          cursor.execute('SELECT MAX(id) FROM articulo')
          unique = cursor.fetchone()
          # START Offline mode image retrieving
          if (self.offline_mode == 1) and (images != ''):
           cursor.execute('SELECT id from imagen WHERE id_articulo = ?', [unique[0]]) # No dupes
           images_present = cursor.fetchone()
           if images_present is None:
            self.retrieve_entry_images(unique[0], images)
          # END Offline mode image retrieving
          new_posts = True
        else:
         images = self.find_entry_images(feed_link, description)
         cursor.execute('INSERT INTO articulo VALUES(null, ?, ?, ?, ?, 0, 0, ?, ?, ?)', [title.decode("utf-8"),description.decode("utf-8"),secs,link.decode("utf-8"),images,id_feed,id.decode("utf-8")])
         self.conn.commit()
         cursor.execute('SELECT MAX(id) FROM articulo')
         unique = cursor.fetchone()
         # START Offline mode image retrieving
         if (self.offline_mode == 1):
          cursor.execute('SELECT imagenes FROM articulo WHERE id = ?', [unique[0]]) # ¿Hay imagenes?
          imagenes = cursor.fetchone()
          if (imagenes is not None) and (imagenes[0] != ''):
           cursor.execute('SELECT id from imagen WHERE id_articulo = ?', [unique[0]]) # No dupes
           images_present = cursor.fetchone()
           if images_present is None:
            self.retrieve_entry_images(unique[0], imagenes[0])
         # END Offline mode image retrieving
         new_posts = True
       else:
        # START Offline mode image retrieving
        if (self.offline_mode == 1):
         cursor.execute('SELECT imagenes FROM articulo WHERE id = ?', [unique[0]]) # ¿Hay imagenes?
         imagenes = cursor.fetchone()
         if (imagenes is not None) and (imagenes[0] != ''):
          cursor.execute('SELECT id from imagen WHERE id_articulo = ?', [unique[0]]) # No dupes
          images_present = cursor.fetchone()
          if images_present is None:
           self.retrieve_entry_images(unique[0], imagenes[0])
        # END Offline mode image retrieving

      if(count != 0):
       (model, iter2) = self.treeselection.get_selected()
       if(iter2 is not None): # Si hay algún nodo seleccionado...
        if(model.iter_depth(iter2) == 1): # ... y es un nodo hijo
         id_selected_feed = self.treestore.get_value(iter2, 2)
         if id_selected_feed == id_feed:
          self.populate_entries(id_feed)

      if new_posts == True:
       # Y luego con el arbol (modelo de datos)
       cursor.execute('SELECT count(id) FROM articulo WHERE id_feed = ' + str(id_feed) + ' AND leido = 0')
       row = cursor.fetchone()
       if row[0] == 0:
        feed_label = nombre_feed
        font_style = 'normal'
       else:
        feed_label = nombre_feed + ' [' + str(row[0]) + ']'
        font_style = 'bold'
       model.set(child, 0, feed_label, 3, font_style)

     iter = self.treestore.iter_next(iter) # Pasamos al siguiente Padre...
   cursor.close()

  else: # Iterar sobre los elementos del diccionario recibido como data.

   (model, iter) = self.treeselection.get_selected() # We only want the model here...
   cursor = self.conn.cursor()
   for k, v in data.iteritems():
    #key: id_feed, value: feed_iter
    #print k, v
    id_feed = k
    child = v

    # START NAME PARSING #
    nombre_feed = model.get_value(child, 0)
    nombre_feed = self.simple_name_parsing(nombre_feed)
    # END NAME PARSING #

    # Primero obtenemos el feed (los datos)...
    cursor.execute('SELECT url FROM feed WHERE id = ?', [id_feed])
    url = cursor.fetchone()[0]
    self.statusbar.set_text(_('Obtaining feed ') + nombre_feed + '...')
    d = feedparser.parse(url)
    feed_link = ''
    if(hasattr(d.feed,'link')): feed_link = d.feed.link.encode('utf-8')

    # Si se trata de un feed nuevo, necesitamos el título antes de nada
    if(new == True):
     if(hasattr(d.feed,'title')):
      nombre_feed = title = d.feed.title.encode('utf-8')
      # Update db...
      (model, iter) = self.treeselection.get_selected()
      id_feed = model.get_value(iter, 2)
      cursor.execute('UPDATE feed SET nombre = ? WHERE id = ?', [title.decode('utf-8'),id_feed])
      self.conn.commit()
      # Update feed tree...
      model.set(iter, 0, title)

    limit = count = len(d.entries)
    if count > self.num_entries:
     limit = self.num_entries
    # Check for article existence...
    for i in range(0, limit):
     (secs, title, description, link, id) = self.check_feed_item(d.entries[i])
     cursor.execute('SELECT id FROM articulo WHERE entry_unique_id = ? AND id_feed = ?', [id.decode('utf-8'),id_feed])
     unique = cursor.fetchone()
     images = ''
     # Non-existant entry? Insert!
     if(unique is None):
      # Check first is the feed is full
      cursor.execute('SELECT count(id) FROM articulo WHERE id_feed = ? AND importante = 0', [id_feed])
      row2 = cursor.fetchone()
      if(row2 is not None) and (row2[0]>=self.num_entries):
       cursor.execute('SELECT id,fecha FROM articulo WHERE importante = 0 AND id_feed = ? ORDER BY fecha ASC LIMIT 1', [id_feed])
       id_articulo, fecha = cursor.fetchone()
       if secs > fecha:
        # If so, do some purging first...
        # Ahora borramos las imagenes del filesystem, si procede
        cursor.execute('SELECT id FROM imagen WHERE id_articulo = ?', [id_articulo])
        images = cursor.fetchall()
        for i in images:
         cursor.execute('SELECT count(nombre) FROM imagen WHERE nombre = ?', [i[0]])
         row3 = cursor.fetchone()
         if (row3 is not None) and (row3[0] <= 1):
          if os.path.exists(images_path + '/'+ str(i[0])):
           os.unlink(images_path + '/'+ str(i[0]))
        cursor.execute('DELETE FROM articulo WHERE id = ?', [id_articulo])
        cursor.execute('DELETE FROM imagen WHERE id_articulo = ?', [id_articulo])
        self.conn.commit()
        images = self.find_entry_images(feed_link, description)
        cursor.execute('INSERT INTO articulo VALUES(null, ?, ?, ?, ?, 0, 0, ?, ?, ?)', [title.decode("utf-8"),description.decode("utf-8"),secs,link.decode("utf-8"),images,id_feed,id.decode("utf-8")])
        self.conn.commit()
        cursor.execute('SELECT MAX(id) FROM articulo')
        unique = cursor.fetchone()
        # START Offline mode image retrieving
        if (self.offline_mode == 1) and (images != ''):
         cursor.execute('SELECT id from imagen WHERE id_articulo = ?', [unique[0]]) # No dupes
         images_present = cursor.fetchone()
         if images_present is None:
          self.retrieve_entry_images(unique[0], images)
        # END Offline mode image retrieving
        new_posts = True
      else:
       images = self.find_entry_images(feed_link, description)
       cursor.execute('INSERT INTO articulo VALUES(null, ?, ?, ?, ?, 0, 0, ?, ?, ?)', [title.decode("utf-8"),description.decode("utf-8"),secs,link.decode("utf-8"),images,id_feed,id.decode("utf-8")])
       self.conn.commit()
       cursor.execute('SELECT MAX(id) FROM articulo')
       unique = cursor.fetchone()
       # START Offline mode image retrieving
       if (self.offline_mode == 1) and (images != ''):
        cursor.execute('SELECT id from imagen WHERE id_articulo = ?', [unique[0]]) # No dupes
        images_present = cursor.fetchone()
        if images_present is None:
         self.retrieve_entry_images(unique[0], images)
       # END Offline mode image retrieving
       new_posts = True
     else:
      # START Offline mode image retrieving
      if (self.offline_mode == 1):
       cursor.execute('SELECT imagenes FROM articulo WHERE id = ?', [unique[0]]) # ¿Hay imagenes?
       imagenes = cursor.fetchone()
       if (imagenes is not None) and (imagenes[0] != ''):
        cursor.execute('SELECT id from imagen WHERE id_articulo = ?', [unique[0]]) # No dupes
        images_present = cursor.fetchone()
        if images_present is None:
         self.retrieve_entry_images(unique[0], imagenes[0])
      # END Offline mode image retrieving

    if(count != 0):
     (model, iter2) = self.treeselection.get_selected()
     if(iter2 is not None): # Si hay algún nodo seleccionado...
      if(model.iter_depth(iter2) == 1): # ... y es un nodo hijo
       id_selected_feed = self.treestore.get_value(iter2, 2)
       if id_selected_feed == id_feed:
        self.populate_entries(id_feed)

    if new_posts == True:
     # Y luego con el arbol (modelo de datos)
     cursor.execute('SELECT count(id) FROM articulo WHERE id_feed = ' + str(id_feed) + ' AND leido = 0')
     row = cursor.fetchone()
     if row[0] == 0:
      feed_label = nombre_feed
      font_style = 'normal'
     else:
      feed_label = nombre_feed + ' [' + str(row[0]) + ']'
      font_style = 'bold'
     model.set(child, 0, feed_label, 3, font_style)

   cursor.close()

  self.statusbar.set_text('')
  # Fires tray icon blinking
  if((new_posts == True) and (window_visible == False)):
   self.statusicon.set_blinking(True)
  self.throbber.hide()
  gtk.gdk.threads_leave()
  self.toggle_menuitems_sensitiveness(enable=True)

 def import_feeds(self, data=None):
  """Imports feeds from an OPML file. It does not import categories
  or feeds with an existent name in the DB, and the later ones keep
  their settings (in case of feeds, they maintain url and category)."""
  dialog = gtk.FileChooserDialog(_("Open.."),
                                self.window,
                                gtk.FILE_CHOOSER_ACTION_OPEN,
                                (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                gtk.STOCK_OPEN, gtk.RESPONSE_OK))

  dialog.set_default_response(gtk.RESPONSE_OK)

  filter = gtk.FileFilter()
  filter.set_name("opml/xml")
  filter.add_pattern("*.opml")
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
   current_category = 0
   cursor = self.conn.cursor()
   for node in tree.getiterator('outline'):
    name = node.attrib.get('text').replace('[','(').replace(']',')')
    url = node.attrib.get('xmlUrl')
    tipo = node.attrib.get('type')
    if name and url:
     cursor.execute('SELECT id FROM feed WHERE nombre = ?', [name])
     if(cursor.fetchone() is None):
      # Create feed in the DB
      cursor.execute('INSERT INTO feed VALUES(null, ?, ?, ?)', [name,url,current_category])
      self.conn.commit()
      # Obtain feed favicon
      row = cursor.execute('SELECT MAX(id) FROM feed')
      id_feed = cursor.fetchone()[0]
      self.get_favicon(id_feed, url)
    elif tipo == 'folder' and len(node) is not 0:
     if node[0].attrib.get('type') != 'folder':
      cursor.execute('SELECT id FROM categoria WHERE nombre = ?', [name])
      row = cursor.fetchone()
      if(row is None):
       # Create category in the DB (if it does not exist already)
       cursor.execute('INSERT INTO categoria VALUES(null, ?)', [name])
       self.conn.commit()
       row = cursor.execute('SELECT MAX(id) FROM categoria')
       row = cursor.fetchone()
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
                                gtk.FILE_CHOOSER_ACTION_SAVE,
                                (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                gtk.STOCK_OPEN, gtk.RESPONSE_OK))

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
   cursor.execute('SELECT id,nombre FROM categoria')
   categorias = cursor.fetchall()
   cursor.close()
   for row in categorias:
    out += '<outline title="'+row[1]+'" text="'+row[1]+'" description="'+row[1]+'" type="folder">\n'
    cursor.execute('SELECT nombre,url FROM feed WHERE id_categoria = ?', [row[0]])
    feeds = cursor.fetchall()
    for row2 in feeds:
     out += '<outline title="'+row2[0]+'" text="'+row2[0]+'" description="'+row2[0]+'" type="rss" xmlUrl="'+row2[1]+'" htmlUrl="http://badopi.net"/>\n'
   out += '</body>\n</opml>'
   f.write(out)
   f.close()
  dialog.destroy()

 def add_icon_to_factory(self, filename, id_feed):
  """Adds an icon to the icon factory."""
  if filename == None:
   factory = gtk.IconFactory()
   pixbuf = gtk.gdk.pixbuf_new_from_file(media_path + 'SRD_RSS_Logo_mini.png')
   iconset = gtk.IconSet(pixbuf)
   factory.add(str(id_feed), iconset)
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
    pass

 def get_favicon(self, id_feed, url):
  """Obtains the favicon from a web and stores it on the filesystem. It should be
     called only once at feed entry creation OR on feed import process."""
  if not os.path.exists(favicon_path):
   os.makedirs(favicon_path)

  try:
   split = url.split("/")
   favicon_url = split[0] + '//' + split[1] + split[2] + '/favicon.ico'
   web_file = urllib2.urlopen(favicon_url)
   favicon = favicon_path + '/' + str(id_feed)
   local_file = open(favicon, 'w')
   local_file.write(web_file.read())
   local_file.close()
   web_file.close()
   # Registrar el favicon...
   self.add_icon_to_factory(favicon, id_feed)
  except:
   self.add_icon_to_factory(None, id_feed)
   pass

 def populate_favicons(self):
  """Iterates 'favicons' directory to load existent favicons in a bunch."""
  for f in os.listdir(favicon_path):
   self.add_icon_to_factory(favicon_path + '/' + f, f)
   
 # INIT #
 ########

 def __init__(self):
  # Inicializamos el threading...
  # Crea la base para la aplicación (directorio + feed de regalo!), si no la hubiere
  self.create_base()
  # Obtiene la config de la app
  self.get_config()
  # Creamos la ventana principal
  self.create_main_window()

def main():
 # Params: interval in miliseconds, callback, callback_data
 # Start timer (1h = 60min = 3600secs = 3600*1000ms)
 timer_id = gobject.timeout_add(naufrago.update_freq*3600*1000, naufrago.update_all_feeds)
 # In case we would want to stop the timer...
 #gobject.source_remove(timer_id)
 gtk.main()
 
if __name__ == "__main__":
 naufrago = Naufrago()
 main()

