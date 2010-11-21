#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
   print self.treestore.get_value(iter, 0)
   #if(len(model.get_path(iter))==2): # Si es hoja, presentar entradas
   if(model.iter_depth(iter) == 2): # Si es hoja, presentar entradas
    self.get_feed(self.treestore.get_value(iter, 0))

 def warning_message(self, str):
  """Shows a custom warning message dialog"""

 def help_about(self, action):
  """Shows the about message dialog"""

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

 def delete_category(self, data=None):
  """Deletes a category from the user feed tree structure"""

 def add_feed(self, data=None):
  """Adds a feed to the user feed tree structure"""

 def delete_feed(self, data=None):
  """Deletes a feed from the user feed tree structure"""
 
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
  if drop_position == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE:
   new = model.prepend(parent=target, row=source_row)
  elif drop_position == gtk.TREE_VIEW_DROP_INTO_OR_AFTER:
   new = model.append(parent=target, row=source_row)
  elif drop_position == gtk.TREE_VIEW_DROP_BEFORE:
   new = model.insert_before(
   parent=None, sibling=target, row=source_row)
  elif drop_position == gtk.TREE_VIEW_DROP_AFTER:
   new = model.insert_after(
   parent=None, sibling=target, row=source_row)

  # Copy any children of the source row.
  for n in range(model.iter_n_children(source)):
   child = model.iter_nth_child(source, n)
   self.treeview_copy_row(treeview, model, child, new, gtk.TREE_VIEW_DROP_INTO_OR_BEFORE)

   # If the source row is expanded, expand the newly copied row
   # also.  We must add at least one child before we can expand,
   # so we expand here after the children have been copied.
   source_is_expanded = treeview.row_expanded(model.get_path(source))
   if source_is_expanded:
    self.treeview_expand_to_path(treeview, model.get_path(new))

 def checkSanity(self, model, iter_to_copy, target_iter):
  """Prevents that a node can be copied inside himself (anti-recursivity!),
  and also checks for application node logic."""
  path_of_iter_to_copy = model.get_path(iter_to_copy)
  print 'Iter to copy:'
  print path_of_iter_to_copy
  path_of_target_iter = model.get_path(target_iter)
  print 'Target iter:'
  print path_of_target_iter
  print 'Target iter value (example value):'
  print model.get_value(target_iter, 0)
  if((path_of_target_iter[0:len(path_of_iter_to_copy)] == path_of_iter_to_copy) or # anti-recursive
    (len(path_of_iter_to_copy) == 1) or # source is parent
    #
    # With drag'n'drop I don't know how to avoid putting leafs on the tree root :(
    #
    #(model.iter_depth(target_iter) == 0) or # dest is root node
    #(target_iter == model.get_iter_root()) or # dest is root node 2
    #(path_of_target_iter == model.get_path(model.get_iter_root())) or # dest is root node 3
    (len(path_of_target_iter) == 2)): # dest is child
     return False
  else:

 def treeview_on_drag_data_received(self, treeview, drag_context, x, y, selection_data, info, eventtime):
  """Handler for 'drag-data-received' that moves dropped TreeView rows."""
  target_path, drop_position = treeview.get_dest_row_at_pos(x, y)
  model, source = treeview.get_selection().get_selected()
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

