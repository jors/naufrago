#!/usr/bin/env python

import feedparser
import time
import datetime
import sys

d = feedparser.parse("http://feeds2.feedburner.com/AscoDeVida")
#d = feedparser.parse("http://www.hacktimes.com/feeds")
#print d
#sys.exit()

#d = feedparser.parse("http://www.hacktimes.com/feeds")
#d = feedparser.parse("http://packetstormsecurity.org/headlines.xml")
#d = feedparser.parse("http://www.mozillazine.org/contents.rdf")
#d = feedparser.parse("http://planet.debian.org/rss20.xml")
#d = feedparser.parse("http://feeds.feedburner.com/ElLadoDelMal")
#d = feedparser.parse("http://enchufado.com/rss2.php")
#d = feedparser.parse("http://www.hispasec.com/rss/unaaldia.xml")
#d = feedparser.parse("http://meneame.net/rss2.php")
#d = feedparser.parse("http://www.meloquitandelasmanos.es/rss2.php")
#d = feedparser.parse("http://badopi.net/rss20.xml")
#d = feedparser.parse("http://planet.gnome.org/atom.xml")
#d = feedparser.parse("http://elladodelmal.blogspot.com/feeds/posts/default")
#d = feedparser.parse("http://feedparser.org/docs/examples/atom10.xml")
#print d.feed.title                    # get values attr-style or dict-style
#print d.feed.subtitle                 # parses escaped HTML
#print d.feed.description
#print d.feed.link
#print d.feed.date
#print d.feed.date_parsed

#print 'Feed encoding: ' + d.encoding.encode('utf-8')
#print 'Feed type/version: ' + d.version.encode('utf-8')

if(hasattr(d.feed,'title')): print 'Feed title: ' + d.feed.title.encode('utf-8')
else: print 'Sin titulo'
#print 'Feed subtitle: ' + d.feed.subtitle.encode('utf-8')
#print 'Description: ' + d.feed.description.encode('utf-8')
if(hasattr(d.feed,'link')): print 'Link: ' + d.feed.link.encode('utf-8')
else: print 'Sin link'

count = len(d.entries)
print '\nSearching... ' + str(count) + ' entries found:\n\n'
for i in range(0, count):
 print d.entries[i]
 print ''

 ###print 'Title: ' + d.entries[i].title.encode('utf-8')
 if(hasattr(d.entries[i],'title')): print 'Entry title: '+d.entries[i].title.encode('utf-8')
 else: print 'Sin titulo'
 ###print 'Link: ' + d.entries[i].link.encode('utf-8')
 if(hasattr(d.entries[i],'link')): print 'Entry link: '+d.entries[i].link.encode('utf-8')
 else: print 'Sin link'
 ###print 'Description: ' + d.entries[i].description.encode('utf-8')
 if(hasattr(d.entries[i],'description')): print 'Entry description: '+d.entries[i].description.encode('utf-8')
 else: print 'Sin description'
 ###print 'Date: ' + d.entries[i].date.encode('utf-8')
 if(hasattr(d.entries[i],'date')): print 'Entry date: '+str(d.entries[i].date.encode('iso8859-1'))
 else: print 'Sin date'
 ###dp = d.entries[i].date_parsed
 ###print 'Date parsed: ' + str(dp)
 if(hasattr(d.entries[i],'date_parsed')):
  print 'Entry date_parsed: '+str(d.entries[i].date_parsed).encode('utf-8')
 else:
  print 'No date found, the current was built: ' + str(datetime.datetime.now())
  split = str(datetime.datetime.now()).split(' ')
  ds = split[0].split('-')
  ts = split[1].split(':')
  t = datetime.datetime(int(ds[0]), int(ds[1]), int(ds[2]), int(ts[0]), int(ts[1]), int(float(ts[2])))
  secs = time.mktime(t.timetuple())
  print "Epoch Seconds: ", secs  
 #t = datetime.datetime(dp[0], dp[1], dp[2], dp[3], dp[4], dp[5])
 #secs = time.mktime(t.timetuple())
 ###secs = time.mktime(datetime.datetime(dp[0], dp[1], dp[2], dp[3], dp[4], dp[5], dp[6]).timetuple())
 ###print 'Date epoch\'ed: ' + str(secs) + ' secs'
 #print 'ID: ' + d.entries[i].id.encode('utf-8')
 if(hasattr(d.entries[i],'id')): print 'Entry id: '+d.entries[i].id.encode('utf-8')
 else: print 'Sin ID'

 print '\n- - - - - - - - - -\n'

