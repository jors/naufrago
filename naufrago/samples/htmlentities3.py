#!/usr/bin/python

import re, htmlentitydefs, time

# Removes HTML or XML character references and entities from a text string (October 28, 2006 | Fredrik Lundh).
#
# @param text The HTML (or XML) source text.
# @return The plain text, as a Unicode string, if necessary.

def unescape(text):
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

t0 = time.time()
#a = 'Michal &#268;iha&#345;: Looking for VServer alternative'
#b = '&iexcl;Esta linea est&aacute; con acento!'
for i in range(10000):
 #print unescape('&#268;iha&#345;')
 #unescape('&#268;iha&#345;')
 unescape('Rep&aacute;mpanos')
#print unescape(b)
print 'method0(): ' + `time.time()-t0`
