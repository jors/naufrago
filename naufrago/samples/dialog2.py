#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gtk

#def lala(spinbutton, data):
# if data == 'num_entradas':
#  if(spinbutton.get_value_as_int() % 10 == 0):
#   print spinbutton.get_value_as_int()
# elif data == 'frecuencia':
#  print spinbutton.get_value_as_int()

dialog = gtk.Dialog("Preferencias",
                   None,
                   gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                   (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                    gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

dialog.set_border_width(5)
dialog.set_resizable(False)

hbox = gtk.HBox()
label = gtk.Label("Número de entradas por feed")
hbox.pack_start(label, True, True, 2)
# Spin button
adjustment = gtk.Adjustment(value=10, lower=10, upper=100, step_incr=10, page_incr=10, page_size=0)
spin_button = gtk.SpinButton(adjustment=adjustment, climb_rate=0.0, digits=0)
spin_button.set_numeric(numeric=True) # Only numbers can be typed
spin_button.set_update_policy(gtk.UPDATE_IF_VALID) # Only update on valid changes
#spin_button.connect("value-changed", lala, 'num_entradas')
hbox.pack_start(spin_button, True, True, 2)
dialog.vbox.pack_start(hbox)

hbox2 = gtk.HBox()
label2 = gtk.Label("Actualizar cada (en horas)")
hbox2.pack_start(label2, True, True, 2)
# Spin button 2
adjustment2 = gtk.Adjustment(value=1, lower=1, upper=24, step_incr=1, page_incr=1, page_size=0)
spin_button2 = gtk.SpinButton(adjustment=adjustment2, climb_rate=0.0, digits=0)
spin_button2.set_numeric(numeric=True) # Only numbers can be typed
spin_button2.set_update_policy(gtk.UPDATE_IF_VALID) # Only update on valid changes
#spin_button2.connect("value-changed", lala, 'frecuencia')
hbox2.pack_start(spin_button2, True, True, 2)
label3 = gtk.Label("h")
hbox2.pack_start(label3, True, True, 0)
dialog.vbox.pack_start(hbox2)

hbox3 = gtk.HBox()
checkbox = gtk.CheckButton("Iniciar con árbol desplegado")
hbox3.pack_start(checkbox, True, True, 5)
dialog.vbox.pack_start(hbox3)

hbox4 = gtk.HBox()
checkbox2 = gtk.CheckButton("Iniciar como Tray Icon")
hbox4.pack_start(checkbox2, True, True, 5)
dialog.vbox.pack_start(hbox4)

dialog.show_all()
response = dialog.run() # Dialog loop
dialog.destroy()

if(response == gtk.RESPONSE_ACCEPT):
 print 'Spinbutton value: ' + str(spin_button.get_value_as_int())
 print 'Spinbutton2 value: ' + str(spin_button2.get_value_as_int())
 print 'Árbol desplegado: ' + str(checkbox.get_active())
 print 'Inicio en Tray: ' + str(checkbox2.get_active())
else:
 print 'Otra cosa fue pulsada'
