#!/usr/bin/env python
# -*- coding: utf-8 -*-

import locale
import gettext
import pygtk
pygtk.require('2.0')
import gtk

APP = 'translate2'
DIR = 'locale'

locale.setlocale(locale.LC_ALL, '')
print locale.getdefaultlocale()[0]
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext

class Test:
 #print _('Hola mundo!')
 window = gtk.Window(gtk.WINDOW_TOPLEVEL)
 label = gtk.Label("TXT: "+_('You must choose a category folder or feed to edit!'))
 window.add(label)
 window.show_all()

def main():
 gtk.main()

if __name__ == "__main__":
 test = Test()
 main()
