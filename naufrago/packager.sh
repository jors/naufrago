#!/bin/sh
#
# WARNING: To be run from root svn dir!

svn_path='/home/jors/sources/proyectos/naufrago'
desktop_deb_path='/home/jors/Desktop/naufrago-deb'
desktop_tar_path='/home/jors/Desktop/naufrago-tar'

case $1 in
 deb)
  # DEB
  cp -a $svn_path/content/*.html $svn_path/naufrago-deb/debian/usr/share/naufrago/content/
  cp -a $svn_path/media/*.png $svn_path/media/*.gif $svn_path/media/*.svg $svn_path/naufrago-deb/debian/usr/share/naufrago/media/
  cp -a $svn_path/naufrago.py $svn_path/naufrago-deb/debian/usr/share/naufrago/
  xgettext --language=Python --keyword=_ --output=$svn_path/naufrago.pot $svn_path/naufrago.py
  for i in ca es it fr pl; do
   msgmerge -U $svn_path/locale/${i}/${i}.po $svn_path/naufrago.pot
   msgfmt $svn_path/locale/${i}/${i}.po -o $svn_path/locale/${i}/LC_MESSAGES/naufrago.mo
   cp -a $svn_path/locale/${i}/${i}.po $svn_path/naufrago-deb/debian/usr/share/naufrago/locale/${i}/
   cp -a $svn_path/locale/${i}/LC_MESSAGES/naufrago.mo $svn_path/naufrago-deb/debian/usr/share/naufrago/locale/${i}/LC_MESSAGES/
  done
  cp -a $svn_path/naufrago.desktop $svn_path/naufrago-deb/debian/usr/share/applications/
  cp -a $svn_path/README* $svn_path/naufrago-deb/debian/usr/share/doc/naufrago/
  for i in README README.es README.ca; do
   gzip -f -9 $svn_path/naufrago-deb/debian/usr/share/doc/naufrago/${i}
  done
  rm -rf $desktop_deb_path
  svn export $svn_path/naufrago-deb $desktop_deb_path
  cd $desktop_deb_path
  chown -R root.root *
  dpkg-deb -z9 -b debian naufrago-0.3-1_all.deb
  lintian -i naufrago-0.3-1_all.deb
 ;;

 tar)
  # TAR: ¡OJO, el tar depende de haber generado ya el deb correctamente!
  cp -a $svn_path/content/*.html $svn_path/naufrago-tar/content/
  cp -a $svn_path/media/*.png $svn_path/media/*.gif $svn_path/media/*.svg $svn_path/naufrago-tar/media/
  cp -a $svn_path/naufrago.py $svn_path/naufrago-tar/
  for i in ca es it fr pl; do
   cp -a $svn_path/locale/${i}/${i}.po $svn_path/naufrago-tar/locale/${i}/
   cp -a $svn_path/locale/${i}/LC_MESSAGES/naufrago.mo $svn_path/naufrago-tar/locale/${i}/LC_MESSAGES/
  done
  cp -a $svn_path/naufrago.desktop $svn_path/naufrago-tar/
  cp -a $svn_path/README* $svn_path/naufrago-tar/doc/
  cp -a $svn_path/naufrago-deb/debian/usr/share/doc/naufrago/changelog.Debian.gz $svn_path/naufrago-tar/doc/
  gzip -d $svn_path/naufrago-tar/doc/changelog.Debian.gz
  mv $svn_path/naufrago-tar/doc/changelog.Debian $svn_path/naufrago-tar/doc/changelog
  rm -rf $desktop_tar_path
  svn export $svn_path/naufrago-tar $desktop_tar_path
  cd $desktop_tar_path
  chown -R root.root *
  # Y el tar a manija, que es tiene que cambiar:
  # - el valor del package = False!
  # - el script de update de la bd.
 ;;

 *)
  echo "Uso: $0 {deb|tar}"
 ;;

esac
