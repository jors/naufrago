#!/usr/bin/env python
# -*- coding: utf-8 -*-

import locale
import gettext

APP = 'translate'
DIR = 'locale'

locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext

print _('Hola mundo!')
