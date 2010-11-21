import time
loop_count = 100000

def method_cgi():
 import cgi
 for i in xrange(loop_count):
  cgi.escape('<&>')

def method_sax():
 from xml.sax import saxutils
 for i in xrange(loop_count):
  saxutils.escape('<&>')

t0 = time.time()
method_cgi()
print 'method_cgi(): ' + `time.time()-t0`

t0 = time.time()
method_sax()
print 'method_sax(): ' + `time.time()-t0`
