import re, time
from htmlentitydefs import name2codepoint

def htmlentitydecode(s):
 return re.sub('&(%s);' % '|'.join(name2codepoint), lambda m: unichr(name2codepoint[m.group(1)]), s)

t0 = time.time()
for i in range(10000):
 #print htmlentitydecode("Rep&aacute;mpanos")
 htmlentitydecode('Rep&aacute;mpanos')
print 'method0(): ' + `time.time()-t0`
