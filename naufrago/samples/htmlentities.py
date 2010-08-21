import htmllib
import xml.sax.saxutils as saxutils

def unescape(s):
    p = htmllib.HTMLParser(None)
    p.save_bgn()
    p.feed(s)
    return p.save_end()
#print unescape("Rep&aacute;mpanos")
print saxutils.unescape("Rep&aacute;mpanos")
print saxutils.unescape("A bunch of text with entities: &amp; &gt; &lt;")

