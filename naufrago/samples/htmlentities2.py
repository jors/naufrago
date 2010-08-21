import re
from htmlentitydefs import name2codepoint

def htmlentitydecode(s):
 return re.sub('&(%s);' % '|'.join(name2codepoint), lambda m: unichr(name2codepoint[m.group(1)]), s)

print htmlentitydecode("Rep&aacute;mpanos")
