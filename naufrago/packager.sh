#!/bin/sh
#
# WARNING: To be run from root svn dir!

svn_path='/home/jors/sources/proyectos/naufrago'
desktop_path='/home/jors/Desktop/naufrago-rss-reader-deb'

# DEB
cp -a $svn_path/content/*.html $svn_path/naufrago-rss-reader-deb/debian/usr/share/naufrago/content/
cp -a $svn_path/media/*.png $svn_path/media/*.gif $svn_path/media/*.svg $svn_path/naufrago-rss-reader-deb/debian/usr/share/naufrago/media/
cp -a $svn_path/naufrago.py $svn_path/naufrago-rss-reader-deb/debian/usr/share/naufrago/
xgettext --language=Python --keyword=_ --output=$svn_path/naufrago.pot $svn_path/naufrago.py
for i in ca es it fr pl; do
 msgmerge -U $svn_path/locale/${i}/${i}.po $svn_path/naufrago.pot
 msgfmt $svn_path/locale/${i}/${i}.po -o $svn_path/locale/${i}/LC_MESSAGES/naufrago.mo
 cp -a $svn_path/locale/${i}/${i}.po $svn_path/naufrago-rss-reader-deb/debian/usr/share/naufrago/locale/${i}/
 cp -a $svn_path/locale/${i}/LC_MESSAGES/naufrago.mo $svn_path/naufrago-rss-reader-deb/debian/usr/share/naufrago/locale/${i}/LC_MESSAGES/
done
cp -a $svn_path/naufrago.desktop $svn_path/naufrago-rss-reader-deb/debian/usr/share/applications/
cp -a $svn_path/README* $svn_path/naufrago-rss-reader-deb/debian/usr/share/doc/naufrago/
for i in README README.es README.ca; do
 gzip -f -9 $svn_path/naufrago-rss-reader-deb/debian/usr/share/doc/naufrago/${i}
done
svn export $svn_path/naufrago-rss-reader-deb $desktop_path
#cd $desktop_path/debian
#find . ! -type d -print0 | xargs -0 md5sum | grep -v DEBIAN > $desktop_path/debian/DEBIAN/md5sum
cd $desktop_path
chown -R root.root *
dpkg-deb -z9 -b debian naufrago-0.3-1_all.deb
lintian -i naufrago-0.3-1_all.deb

# TAR
# ...
