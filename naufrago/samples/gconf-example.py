#!/usr/bin/env python
# -*- coding: utf-8 -*-
import gconf

client = gconf.client_get_default()
 
# Guardar valor...
#anchura = 10
#client.set_int('/app/prueba/anchura', anchura) 
 
# Recuperar, 'valor' será None si la clave no existe
#valor = client.get_int('/app/prueba/anchura') 
print client.get_string('/desktop/gnome/interface/font_name')
