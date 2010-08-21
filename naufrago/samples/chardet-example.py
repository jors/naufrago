import urllib
import chardet

urlread = lambda url: urllib.urlopen(url).read()

print chardet.detect(urlread("http://google.cn/"))
print chardet.detect(urlread("http://barrapunto.com/"))
print chardet.detect(urlread("http://enchufado.com/"))
print chardet.detect(urlread("http://www.mozillazine.org/"))
print chardet.detect(urlread("http://www.mozillazine.org/contents.rdf"))
