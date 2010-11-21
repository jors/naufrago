#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Naufrago RSS Reader, by jors ( worbynet at gmail.com), 14-05-2010
#
# Special thanks for the _great_ DnD stuff to:
# - Doug Quale (quale1 at charter.net )
# - Walter Anger ( WalterAnger at aon.at )

import pygtk
pygtk.require('2.0')
import gtk
import os
import sqlite3

db_path = os.getenv("HOME") + '/.naufrago/naufrago.db'

class Naufrago:

 # CALLBACKS #
 #############

 def quit(self):
  """Quits the app"""
  self.hide()
  self.destroy()

 # Imprime una cadena por pantalla
 def callback(self, data):
  print "Hello again - %s was pressed" % data

 def delete_event(self, event, data=None):
  """Closes the app through window manager signal"""
  gtk.main_quit()
  return False

 def button_press_event(self, widget, event):
  """Tells which mouse button was pressed"""
  print 'Button ' + str(event.button) + '  pressed!'
  #if(event.button == 3):
   #menu1 = gtk.Menu()
   # TODO

 # DEPRECATED en favor de la función 'row_selection'
 def row_selection_change(self, selection, model, path, is_selected, user_data=None):
  ###iter = model.get_iter(path) # Útil para obtener un iter dado un path !!!
  values = model.get_value(iter, 0) # Útil para obtener un valor dada una columna y un iter !!!
  print values
  #print model.get_path(iter)
  #print model.get_string_from_iter(iter) # Útil para obtener un nombre dado un iter !!!
  # print model.get_iter_from_string(path) # Útil para obtener un iter dado un nombre !!!
  return True

 def make_pb(self, tvcolumn, cell, model, iter):
  """Renders the parameter received icons"""
  stock = model.get_value(iter, 1)
  pb = self.treeview.render_icon(stock, gtk.ICON_SIZE_MENU, None)
  cell.set_property('pixbuf', pb)
  return

# FUNCTIONS #
#############

 def row_selection(self, event):
  """Row change detector"""
  (model, iter) = self.treeselection.get_selected()
  if(iter is not None): # Hay algún nodo seleccionado
   row_name = self.treestore.get_value(iter, 0)
   print row_name
   #if(row_name not in category_list): # Si es hoja, presentar entradas
   if(model.iter_depth(iter) == 2): # Si es hoja, presentar entradas
    self.get_feed(self.treestore.get_value(iter, 0))

 def warning_message(self, str):
  """Shows a custom warning message dialog"""
  dialog = gtk.MessageDialog(self.window, (gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT), gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, str)
  dialog.run()
  dialog.destroy()

 def help_about(self, action):
  """Shows the about message dialog"""
  about = gtk.AboutDialog()
  about.set_program_name("Naufrago!")
  about.set_version("0.1")
  about.set_copyright("(c) jors")
  about.set_comments("Naufrago! is a simple RSS reader")
  about.set_website("http://www.enchufado.com/")
  about.set_logo(gtk.gdk.pixbuf_new_from_file("wilson.png"))
  about.run()
  about.destroy()

 def create_ui(self, window):
  """Creates the menubar"""
  ui_string = """<ui>
  <menubar name='Menubar'>
    <menu action='ArchivoMenu'>
      <menuitem action='Nuevo feed'/>
      <menuitem action='Nueva categoria'/>
      <menuitem action='Eliminar feed'/>
      <menuitem action='Eliminar categoria'/>
      <separator/>
      <menuitem action='Salir'/>
    </menu>
    <menu action='HerramientasMenu'>
      <menuitem action='Opciones'/>
    </menu>
    <menu action='AyudaMenu'>
      <menuitem action='Acerca de'/>
    </menu>
  </menubar>
</ui>"""

  # Una opción para que se muestren los iconos:
  # gconf-editor: Desktop -> Gnome -> Interface -> menus_have_icons (y buttons_have_icons)
  ag = gtk.ActionGroup('WindowActions')
  actions = [
            ('ArchivoMenu', None, '_Archivo'),
            ('Nuevo feed', gtk.STOCK_FILE, 'Nuevo _feed', '<control>F', 'Crea un feed', self.add_feed),
            ('Nueva categoria', gtk.STOCK_DIRECTORY, 'Nueva _categoria', '<control>C', 'Crea una categoria', self.add_category),
            ('Eliminar feed', gtk.STOCK_CLEAR, 'Eliminar _feed', '<alt>F', 'Elimina un feed', self.delete_feed),
            ('Eliminar categoria', gtk.STOCK_CLOSE, 'Eliminar _categoria', '<alt>C', 'Elimina una categoria', self.delete_category),
            ('Salir', gtk.STOCK_QUIT, '_Salir', '<control>S', 'Salir', self.delete_event),
            ('HerramientasMenu', None, '_Herramientas'),
            ('Opciones', gtk.STOCK_EXECUTE, '_Opciones', '<control>O', 'Muestra las opciones', self.callback),
            ('AyudaMenu', None, 'A_yuda'),
            ('Acerca de', gtk.STOCK_ABOUT, 'Acerca de', None, 'Acerca de', self.help_about),
            ]
  ag.add_actions(actions)
  self.ui = gtk.UIManager()
  self.ui.insert_action_group(ag, 0)
  self.ui.add_ui_from_string(ui_string)
  self.window.add_accel_group(self.ui.get_accel_group())

 def create_base(self):
  """Creates the base app structure on the user home dir"""
  if not os.path.exists(db_path):
    os.makedirs(os.getenv("HOME") + '/.naufrago')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.executescript('''
     CREATE TABLE categoria(id integer PRIMARY KEY, nombre varchar(32) NOT NULL);
     CREATE TABLE feed(id integer PRIMARY KEY, nombre varchar(32) NOT NULL, url varchar(1024) NOT NULL, id_categoria integer NOT NULL);
     CREATE TABLE articulo(id integer PRIMARY KEY, titulo varchar(256) NOT NULL, contenido text, fecha text NOT NULL, id_feed integer NOT NULL);
     CREATE TABLE imagen(id integer PRIMARY KEY, imagen blob NOT NULL, id_articulo integer NOT NULL);
     INSERT INTO categoria VALUES(null, 'General');
     INSERT INTO feed VALUES(null, 'enchufado.com', 'http://enchufado.com/rss2.php', 1);''')
    conn.commit()
    cursor.close()

 def create_main_window(self):
  """Creates the main window with all it's widgets"""
  # Creamos una ventana
  self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
  # Título de la ventana
  self.window.set_title("Naufrago!")
  # Establecemos el manejador para delete_event
  self.window.connect("delete_event", self.delete_event)
  self.window.set_border_width(5) # Grosor del borde de la ventana
  self.window.set_size_request(600, 300) # Dimensionamiento de la ventana
  # Creación del VBox.
  self.vbox = gtk.VBox(False, 0)
  # Creación del menubar
  self.create_ui(self.window)
  self.vbox.pack_start(self.ui.get_widget('/Menubar'), expand=False)
  # Creación del HPaned.
  self.hpaned = gtk.HPaned()
  # Creación del Tree izquierdo para los feeds
  self.treestore = self.populate_feeds() # Propaga los feeds del usuario
  # Create the TreeView using treestore
  self.treeview = gtk.TreeView(self.treestore)
  # Right mouse button tree menu.
  self.treeview.connect("button_press_event", self.button_press_event)
  self.treeselection = self.treeview.get_selection()
  ###self.treeselection.set_select_function(self.row_selection_change, self.treestore, True)
  self.treeselection.connect("changed", self.row_selection)
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
  self.tvcolumn.set_attributes(self.cell, text=0)

  # Allow sorting on the column
  self.tvcolumn.set_sort_column_id(0)
  # Allow drag and drop reordering of rows
  self.treeview.set_reorderable(True)
  self.treeview_setup_dnd(self.treeview)
  self.hpaned.add1(self.treeview)
 
  # Creación del VPaned
  self.vpaned = gtk.VPaned()
  # Creación de los 2 elementos restantes: la lista/tabla y el browser.
  self.button1 = gtk.Button("Button 1")
  self.button2 = gtk.Button("Button 2")
  #self.button1.connect("clicked", self.callback, "button 1")
  #self.button2.connect("clicked", self.callback, "button 2")
  self.vpaned.add1(self.button1)
  self.vpaned.add2(self.button2)
  self.hpaned.add2(self.vpaned)
  
  self.vbox.pack_start(self.hpaned, True, True, 0)
  self.window.add(self.vbox)
  self.window.show_all()

 def populate_feeds(self):
  """Obtains the user feed tree structure"""
  conn = sqlite3.connect(db_path)
  conn2 = sqlite3.connect(db_path)
  cursor = conn.cursor()
  cursor2 = conn2.cursor()
  self.treestore = gtk.TreeStore(str, str, 'gboolean')
  cursor.execute('''SELECT id,nombre FROM categoria''')
  for row in cursor:
   dad = self.treestore.append(None, [row[1], gtk.STOCK_OPEN, True])
   cursor2.execute('''SELECT nombre FROM feed WHERE id_categoria = ''' + str(row[0]))
   for row2 in cursor2:
    son = self.treestore.append(dad, [row2[0], gtk.STOCK_NEW, True])
  cursor2.close()
  cursor.close()
  return self.treestore

 def add_category(self, data=None):
  """Adds a category to the user feed tree structure"""
  dialog = gtk.MessageDialog(self.window, (gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT), gtk.MESSAGE_QUESTION, gtk.BUTTONS_OK_CANCEL, None)
  entry = gtk.Entry()
  dialog.set_markup('Por favor, introduce la <b>categoría</b>')
  dialog.vbox.pack_end(entry, True, True, 0)
  dialog.show_all()
  response = dialog.run()
  text = entry.get_text()
  dialog.destroy()

  if((text != '') and (response == gtk.RESPONSE_OK)):
   # Create category in the database (if it does not exist!)
   conn = sqlite3.connect(db_path)
   cursor = conn.cursor()
   #cursor.execute('SELECT id FROM categoria WHERE nombre LIKE ? UNION SELECT id FROM feed WHERE nombre LIKE ?', [text,text])
   #data = cursor.fetchone()
   #if(data is None):
   # print 'String no encontrado, insertando...'
   dad = self.treestore.append(None, [text, gtk.STOCK_OPEN, True])
   cursor.execute('INSERT INTO categoria VALUES(null, ?)', [text])
   conn.commit()
   #else:
   # print 'String encontrado, skipping!'
   cursor.close()

 def delete_category(self, data=None):
  """Deletes a category from the user feed tree structure"""
  (model, iter) = self.treeselection.get_selected()
  if(iter is not None): # Si hay algún nodo seleccionado...
   text = self.treestore.get_value(iter, 0)
   #if(text in category_list): # ... y es un nodo padre
   if(model.iter_depth(iter) == 0): # ... y es un nodo padre
    if(text != 'General'):
     dialog = gtk.MessageDialog(self.window, (gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT), gtk.MESSAGE_QUESTION, gtk.BUTTONS_OK_CANCEL, None)
     dialog.set_markup('¿Borrar la <b>categoría</b> seleccionada?')
     dialog.show_all()
     response = dialog.run()
     dialog.destroy()

     if(response == gtk.RESPONSE_OK):
      print 'Eliminando categoria ' + text + '...'
      result = self.treestore.remove(iter)
      conn = sqlite3.connect(db_path)
      cursor = conn.cursor()
      cursor.execute('DELETE FROM categoria WHERE nombre LIKE ?', [text])
      conn.commit()
      cursor.close()
    else:
     self.warning_message('¡La categoría General no puede ser eliminada!')
   else:
    self.warning_message('¡Debe seleccionar una carpeta de categoría!')
  else:
   self.warning_message('¡Debe seleccionar una carpeta de categoría!')

 def add_feed(self, data=None):
  """Adds a feed to the user feed tree structure"""
  dialog = gtk.MessageDialog(self.window, (gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT), gtk.MESSAGE_QUESTION, gtk.BUTTONS_OK_CANCEL, None)
  entryName = gtk.Entry()
  entryURL = gtk.Entry()
  labelName = gtk.Label('Nombre ')
  labelURL = gtk.Label('URL ')
  dialog.set_markup('Por favor, introduce el <b>feed</b>')
  hbox1 = gtk.HBox()
  hbox1.pack_start(labelName, True, True, 0)
  hbox1.pack_start(entryName, True, True, 0)
  dialog.vbox.pack_start(hbox1, True, True, 0)
  hbox2 = gtk.HBox()
  hbox2.pack_start(labelURL, True, True, 0)
  hbox2.pack_start(entryURL, True, True, 0)
  dialog.vbox.pack_start(hbox2, True, True, 0)
  dialog.show_all()
  response = dialog.run()
  textName = entryName.get_text()
  textURL = entryURL.get_text()
  dialog.destroy()

  if((textName != '') and (textURL != '') and (response == gtk.RESPONSE_OK)):
   # Create feed in the database (if it does not exist!)
   conn = sqlite3.connect(db_path)
   cursor = conn.cursor()
   #cursor.execute('SELECT id FROM feed WHERE nombre LIKE ? OR url LIKE ? UNION SELECT id FROM categoria WHERE nombre LIKE ?', [textName,textURL,textName])
   #data = cursor.fetchone()
   #if(data is None):
   # print 'String no encontrado, insertando...'
   # ¿Es esto una manera válida para hallar el iter del nodo 'General'?
   iter = self.treestore.get_iter((0,))
    #nodoPadre = self.treestore.get_value(iter, 0) # DEBUG
    # El None tiene que ser la categoria padre 'General'
    #son = self.treestore.append(None, [textName, gtk.STOCK_NEW, True])
   son = self.treestore.append(iter, [textName, gtk.STOCK_NEW, True])
   cursor.execute('INSERT INTO feed VALUES(null, ?, ?, 1)', [textName,textURL])
   conn.commit()
   #else:
   # print 'String encontrado, skipping!'
   cursor.close()

 def delete_feed(self, data=None):
  """Deletes a feed from the user feed tree structure"""
  (model, iter) = self.treeselection.get_selected()
  if(iter is not None): # Si hay algún nodo seleccionado...
   text = self.treestore.get_value(iter, 0)
   #if(text not in category_list): # ... y es un nodo hijo
   if(model.iter_depth(iter) == 1): # ... y es un nodo hijo
    dialog = gtk.MessageDialog(self.window, (gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT), gtk.MESSAGE_QUESTION, gtk.BUTTONS_OK_CANCEL, None)
    dialog.set_markup('¿Borrar el <b>feed</b> seleccionado?')
    dialog.show_all()
    response = dialog.run()
    dialog.destroy()

    if(response == gtk.RESPONSE_OK):
     print 'Eliminando feed ' + text + '...'
     result = self.treestore.remove(iter)
     conn = sqlite3.connect(db_path)
     cursor = conn.cursor()
     cursor.execute('DELETE FROM feed WHERE nombre LIKE ?', [text])
     conn.commit()
     cursor.close()
   else:
    self.warning_message('¡Debe seleccionar un feed!')
  else:
   self.warning_message('¡Debe seleccionar un feed!')

 def get_feed(self, str):
  """Obtains the feeds (thanks feedparser!)"""
  print 'Obteniendo feed de ' + str + '...'

 def treeview_expand_to_path(self, treeview, path):
  """Expand row at path, expanding any ancestors as needed.
  This function is provided by gtk+ >=2.2, but it is not yet wrapped
  by pygtk 2.0.0."""
  for i in range(len(path)):
   treeview.expand_row(path[:i+1], open_all=False)

 def treeview_copy_row(self, treeview, model, source, target, drop_position):
  """Copy tree model rows from treeiter source into, before or after treeiter target.
  All children of the source row are also copied and the
  expanded/collapsed status of each row is maintained."""
  source_row = model[source]
  conn = sqlite3.connect(db_path)
  cursor = conn.cursor()
  if drop_position == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE:
   print '---Prepend---'
   new = model.prepend(parent=target, row=source_row)
  elif drop_position == gtk.TREE_VIEW_DROP_INTO_OR_AFTER:
   print '---Append---'
   new = model.append(parent=target, row=source_row)
  #elif drop_position == gtk.TREE_VIEW_DROP_BEFORE:
  # new = model.insert_before(parent=None, sibling=target, row=source_row)
  # print 'option c'
  #elif drop_position == gtk.TREE_VIEW_DROP_AFTER:
  # new = model.insert_after(parent=None, sibling=target, row=source_row)
  # print 'option d'
  parent_value = str(model.get_value(target, 0))
  row_value = str(model.get_value(source_row.iter, 0))
  print 'Parent_value: ' + parent_value
  print 'Row_value: ' + row_value
  print "UPDATE feed SET id_categoria = (SELECT id FROM categoria WHERE nombre LIKE %s) WHERE id = (SELECT id FROM feed WHERE nombre LIKE %s)" % (parent_value,row_value)
  cursor.execute('UPDATE feed SET id_categoria = (SELECT id FROM categoria WHERE nombre LIKE ?) WHERE id = (SELECT id FROM feed WHERE nombre LIKE ?)', [parent_value,row_value])
  conn.commit()
  cursor.close()

  # If the source row is expanded, expand the newly copied row
  # also.  We must add at least one child before we can expand,
  # so we expand here after the children have been copied.
  source_is_expanded = treeview.row_expanded(model.get_path(source))
  if source_is_expanded:
   self.treeview_expand_to_path(treeview, model.get_path(new))

 def checkSanity(self, model, iter_to_copy, target_iter):
  """Prevents that a node can be copied inside himself (anti-recursivity!),
  and also checks for application node logic."""

  iter_to_copy_value = model.get_value(iter_to_copy, 0)
  target_iter_value = model.get_value(target_iter, 0)

  path_of_iter_to_copy = model.get_path(iter_to_copy)
  path_of_target_iter = model.get_path(target_iter)

  if((path_of_target_iter[0:len(path_of_iter_to_copy)] == path_of_iter_to_copy) or # anti-recursive
    #(iter_to_copy_value in category_list) or # source is parent
    (len(path_of_iter_to_copy) == 1) or # source is parent
    #(target_iter_value not in category_list)): # dest is child
    (len(path_of_target_iter) == 2)): # dest is child
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

 def treeview_setup_dnd(self, treeview):
  """Setup a treeview to move rows using drag and drop."""
  target_entries = [('example', gtk.TARGET_SAME_WIDGET, 0)]
  # [(drag type string, target_flags, application integer ID used for identification purposes)]

  # Drag start operation (origin)
  treeview.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, target_entries, gtk.gdk.ACTION_MOVE)
  # 1st mouse button, target_entries (ver arriba), type of action to do

  # Drag end operation (destination)
  treeview.enable_model_drag_dest(target_entries, gtk.gdk.ACTION_MOVE)
  #                               target_entries (ver arriba), type of action to do

  treeview.connect('drag-data-received', self.treeview_on_drag_data_received)

 # INIT #
 ########

 def __init__(self):

  # Crea la base para la aplicación (directorio + feed de regalo!), si no la hubiere
  self.create_base()

  # Creamos la ventana principal
  self.create_main_window()

def main():
 gtk.main()
 
if __name__ == "__main__":
 hello = Naufrago()
 main()

