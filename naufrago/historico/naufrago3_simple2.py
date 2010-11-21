#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import pygtk
pygtk.require('2.0')
import gtk

category_list = []
feed_list = []

class Naufrago:

 # CALLBACKS #
 #############
 def quit(self):
  """Quits the app"""
  self.hide()
  self.destroy()

 def delete_event(self, event, data=None):
  """Closes the app through window manager signal"""
  gtk.main_quit()
  return False

# FUNCTIONS #
#############
 def row_selection(self, event):
  """Row change detector"""
  (model, iter) = self.treeselection.get_selected()
  if(iter is not None): # Hay algún nodo seleccionado
   row_name = self.treestore.get_value(iter, 0)
   print 'Selected row/node: ' + row_name

 def create_main_window(self):
  """Creates the main window with all it's widgets"""
  self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
  self.window.set_title("2 level tree example")
  self.window.set_size_request(250, 200)
  self.window.connect("delete_event", self.delete_event)
  self.treestore = self.populate_feeds() # Propaga los feeds del usuario
  self.treeview = gtk.TreeView(self.treestore)
  self.treeselection = self.treeview.get_selection()
  self.treeselection.connect("changed", self.row_selection)
  self.tvcolumn = gtk.TreeViewColumn('Column')
  self.treeview.append_column(self.tvcolumn)

  self.cellpb = gtk.CellRendererPixbuf()
  self.cell = gtk.CellRendererText()
  self.tvcolumn.pack_start(self.cellpb, False)
  self.tvcolumn.pack_start(self.cell, True)
  if gtk.gtk_version[1] < 2:
     self.tvcolumn.set_cell_data_func(self.cellpb, self.make_pb)
  else:
     self.tvcolumn.set_attributes(self.cellpb, stock_id=1)
  self.tvcolumn.set_attributes(self.cell, text=0)

  self.tvcolumn.set_sort_column_id(0)
  # Allow drag and drop reordering of rows
  self.treeview.set_reorderable(True)
  self.treeview_setup_dnd(self.treeview)
 
  self.window.add(self.treeview)
  self.window.show_all()

 def populate_feeds(self):
  """Create the tree node structure"""
  rootnodes = ['root1', 'root2']
  leafnodes = ['leaf1', 'leaf2']
  
  self.treestore = gtk.TreeStore(str, str, 'gboolean')
  king_iter = self.treestore.append(None, ['The King', gtk.STOCK_OPEN, True])
  for root in rootnodes:
   category_list.append(root)
   dad_iter = self.treestore.append(king_iter, [root, gtk.STOCK_OPEN, True])
   for leaf in leafnodes:
    feed_list.append(leaf)
    son_iter = self.treestore.append(dad_iter, [leaf, gtk.STOCK_NEW, True])
  return self.treestore

 def treeview_expand_to_path(self, treeview, path):
  """Expand row at path, expanding any ancestors as needed."""
  for i in range(len(path)):
   treeview.expand_row(path[:i+1], open_all=False)

 def treeview_copy_row(self, treeview, model, source, target, drop_position):
  """Copy tree model rows from treeiter source into, before or after treeiter target.
  The expanded/collapsed status of each row is maintained."""
  source_row = model[source]
  if drop_position == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE:
   new = model.prepend(parent=target, row=source_row)
  elif drop_position == gtk.TREE_VIEW_DROP_INTO_OR_AFTER:
   new = model.append(parent=target, row=source_row)
  #elif drop_position == gtk.TREE_VIEW_DROP_BEFORE:
  # print 'Insert before'
  # new = model.insert_before(parent=None, sibling=target, row=source_row)
  #elif drop_position == gtk.TREE_VIEW_DROP_AFTER:
  # print 'Insert after'
  # new = model.insert_after(parent=None, sibling=target, row=source_row)

  # If the source row is expanded, expand the newly copied row
  # also.  We must add at least one child before we can expand,
  # so we expand here after the children have been copied.
  source_is_expanded = treeview.row_expanded(model.get_path(source))
  if source_is_expanded:
   self.treeview_expand_to_path(treeview, model.get_path(new))

 def checkSanity(self, model, iter_to_copy, target_iter):
  """Prevents that a node can be copied inside himself (anti-recursivity!),
  and also checks for application node logic (only leaf nodes can be moved
  to root nodes, and these leaf nodes SHOULD NOT become root nodes!)."""
  iter_to_copy_value = model.get_value(iter_to_copy, 0)
  target_iter_value = model.get_value(target_iter, 0)

  path_of_iter_to_copy = model.get_path(iter_to_copy)
  print 'iter_to_copy_value: ' + iter_to_copy_value + ', path_of_iter_to_copy: ' + str(path_of_iter_to_copy)
  path_of_target_iter = model.get_path(target_iter)
  print 'target_iter_value: ' + target_iter_value + ', path of target_iter: ' + str(path_of_target_iter) + '\n'

  #if((path_of_target_iter[0:len(path_of_iter_to_copy)] == path_of_iter_to_copy) or # anti-recursive
  if((iter_to_copy_value in category_list) or # source is parent
    (target_iter_value not in category_list)): # dest is child
     return False
  else:
   return True

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
  # Drag start operation (origin)
  treeview.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, target_entries, gtk.gdk.ACTION_MOVE)
  # Drag end operation (destination)
  treeview.enable_model_drag_dest(target_entries, gtk.gdk.ACTION_MOVE)
  treeview.connect('drag-data-received', self.treeview_on_drag_data_received)

 # INIT #
 ########
 def __init__(self):

  # Creamos la ventana principal
  self.create_main_window()

def main():
 gtk.main()
 
if __name__ == "__main__":
 hello = Naufrago()
 main()

