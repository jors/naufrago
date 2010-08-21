#!/usr/bin/env python
# 
# My thanks for the _great_ DnD stuff to:
#
# - Doug Quale (quale1 at charter.net )
# - Walter Anger ( WalterAnger at aon.at )

import pygtk
pygtk.require("2.0")
import gtk

def treeview_expand_to_path(treeview, path):
    """Expand row at path, expanding any ancestors as needed.
    This function is provided by gtk+ >=2.2, but it is not yet wrapped
    by pygtk 2.0.0."""
    for i in range(len(path)):
        treeview.expand_row(path[:i+1], open_all=False)

def treeview_copy_row(treeview, model, source, target, drop_position):
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
        treeview_copy_row(treeview, model, child, new,
                          gtk.TREE_VIEW_DROP_INTO_OR_BEFORE)

    # If the source row is expanded, expand the newly copied row
    # also.  We must add at least one child before we can expand,
    # so we expand here after the children have been copied.
    source_is_expanded = treeview.row_expanded(model.get_path(source))
    if source_is_expanded:
        treeview_expand_to_path(treeview, model.get_path(new))

def checkSanity(model, iter_to_copy, target_iter):
   """Prevents that a node can be copied inside himself (anti-recursivity!)"""
   path_of_iter_to_copy = model.get_path(iter_to_copy)
   print 'Iter to copy:'
   print path_of_iter_to_copy
   path_of_target_iter = model.get_path(target_iter)
   print 'Target iter:'
   print path_of_target_iter
   if ((path_of_target_iter[0:len(path_of_iter_to_copy)] == path_of_iter_to_copy) or # anti-recursive
      (len(path_of_iter_to_copy) == 1) or # source is parent
      (model.iter_depth(target_iter) == 0) or # dest is root node
      (len(path_of_target_iter) == 2)): # dest is child
       return False
   else:
       return True

def treeview_on_drag_data_received(treeview, drag_context, x, y,
                                   selection_data, info, eventtime):
    """Handler for 'drag-data-received' that moves dropped TreeView rows.  """
    target_path, drop_position = treeview.get_dest_row_at_pos(x, y)
    #print target_path # DEST
    model, source = treeview.get_selection().get_selected()
    #print model.get_path(source) # SOURCE
    target = model.get_iter(target_path)
    if checkSanity(model, source, target):
        treeview_copy_row(treeview, model, source, target, drop_position)
        # If the drop has created a new child (drop into), expand
        # the parent so the user can see the newly copied row.
        if (drop_position == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE
            or drop_position == gtk.TREE_VIEW_DROP_INTO_OR_AFTER):
            treeview.expand_row(target_path, open_all=False)
        # Finish the drag and have gtk+ delete the drag source rows.
        drag_context.finish(success=True, del_=True, time=eventtime)
    else:
        drag_context.finish(success=False, del_=False, time=eventtime)

def treeview_setup_dnd(treeview):
    """Setup a treeview to move rows using drag and drop.  """
    target_entries = [('example', gtk.TARGET_SAME_WIDGET, 0)]
    #         [(drag type string, target_flags, application integer ID used for identification purposes)]

    # Drag start operation (origin)
    treeview.enable_model_drag_source(
        gtk.gdk.BUTTON1_MASK, target_entries, gtk.gdk.ACTION_MOVE)
    #   1st mouse button, target_entries (ver arriba), type of action to do

    # Drag end operation (destination)
    treeview.enable_model_drag_dest(target_entries, gtk.gdk.ACTION_MOVE)
    #                               target_entries (ver arriba), type of action to do

    treeview.connect('drag-data-received', treeview_on_drag_data_received)

if __name__ == '__main__':
    window = gtk.Window()
    window.connect("delete_event", gtk.main_quit)
    window.set_default_size(250, 350)

    data = [['Uno'], ['Dos'], ['Tres']]
    data2 = [['lala'], ['tralari']]

    model = gtk.TreeStore(str)
    for item in data:
        dad = model.append(parent=None, row=item)
	for item2 in data2:
	    model.append(parent=dad, row=item2)

    treeview = gtk.TreeView(model)
    window.add(treeview)

    cell = gtk.CellRendererText()
    tv_insert = treeview.insert_column_with_attributes
    tv_insert(-1, 'String', cell, text=0)

    treeview_setup_dnd(treeview)
    window.show_all()
    gtk.main()

