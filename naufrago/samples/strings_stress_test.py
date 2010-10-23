import time
loop_count = 100000

def method0():
 out_str = ''
 for num in xrange(loop_count):
  out_str += str(num)

def method1():
 out_str = ''
 for num in xrange(loop_count):
  out_str += `num`

def method2():
 from UserString import MutableString
 out_str = MutableString()
 for num in xrange(loop_count):
  out_str += `num`

def method3():
 from array import array
 char_array = array('c') 
 for num in xrange(loop_count):
  char_array.fromstring(`num`)
 char_array.tostring()

def method4():
 str_list = []
 for num in xrange(loop_count):
  str_list.append(`num`)
 ''.join(str_list)

def method5():
 from cStringIO import StringIO
 file_str = StringIO()
 for num in xrange(loop_count):
  file_str.write(`num`)
 file_str.getvalue()

def method6():
 ''.join([`num` for num in xrange(loop_count)])

t0 = time.time()
method0()
print 'method0(): ' + `time.time()-t0`

t0 = time.time()
method1()
print 'method1(): ' + `time.time()-t0`

t0 = time.time()
method2()
print 'method2(): ' + `time.time()-t0`

t0 = time.time()
method3()
print 'method3(): ' + `time.time()-t0`

t0 = time.time()
method4()
print 'method4(): ' + `time.time()-t0`

t0 = time.time()
method5()
print 'method5(): ' + `time.time()-t0`

t0 = time.time()
method6()
print 'method6(): ' + `time.time()-t0`
