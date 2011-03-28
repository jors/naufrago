import time
loop_count = 1000000

def method0():
 s = 'lalala'
 out_str = ''
 for num in xrange(loop_count):
  out_str = "<html>" + s + "</html>"

def method1():
 s = 'lalala'
 out_str = ''
 for num in xrange(loop_count):
  out = "<html>%s</html>" % (s)

t0 = time.time()
method0()
print 'method0(): ' + `time.time()-t0`

t0 = time.time()
method1()
print 'method1(): ' + `time.time()-t0`
