22/12/2010

=========
Contenido
=========

1. Introducción.
2. Características y lista de deseos.
3. Requisitos (mínimos).
4. ¿Por qué reinventar la rueda?
5. Instalación y uso.
6. Problemas / Soporte.
7. Licencia.
8. Autores.
9. Agradecimientos.

================
1. Introducción
================

Náufrago! es un lector simple de RSS que permite ver noticias
con sus imágenes aún sin mantenerse a flote, o dicho de otro modo,
sin estar online. Esto es porque hay gente, como el autor, que no
siempre tiene una conexión a mano y, sin embargo, quiere poder leer
artículos/entradas/posts con las imágenes que puedan acompañarlos.
Este es el leit motiv de la aplicación.

===================
2. Características
===================

Las destacadas serían:

 - Categorización de feeds de un único nivel en árbol.
 - Organización de feeds por categorías mediante drag & drop.
 - Lectura online/offline de feeds (incluyendo imágenes).
 - Apertura/cierre inteligente de categorias.
 - Modo pantalla completa para la lectura de feeds.
 - Marcación de feeds como importantes/permanentes (grabación).
 - Inclusión de los favicons de los feeds.
 - Iconización de la aplicación en la Tray.
 - Importación/exportación de feeds en formato OPML.
 - Carpeta de Importantes y No leídos.
 - Buscador de términos.
 - Multiidioma (de momento Inglés, Francés, Polaco, Italiano, Catalán y Castellano).
 - Autocomprobador de actualizaciones.

Lista de deseos:

 - Traducciones a más idiomas.

========================
3. Requisitos (mínimos)
========================

A nivel de software:

 - GNU/Linux (Squeeze/Testing o superior para el paquete Debian).
 - Python 2.5 o superior.
 - python-gtk2 (bindings de gtk2 para Python).
 - python-pysqlite2 (bindings de sqlite3 para Python).
 - python-feedparser (bindings de feedparser para Python).
 - python-webkit (bindings de Webkit para Python).

A nivel de hardware, cualquier cosa que pueda moverlo. El autor
lo ha desarrollado y lo usa a diario desde un Netbook con un Intel
Atom a 1,6Ghz con 1GB de RAM.

=================================
4. ¿Por qué reinventar la rueda?
=================================

Si es un cliente clavado (con excepciones) a Liferea (en lo que al diseño
se refiere), ¿por qué reinventar la rueda? Por muchos motivos. Principalmente
porque el autor no supo encontrar un cliente RSS que funcionara offline con
imágenes incluidas, los desarrolladores de Liferea no admiten feature
requests (algo totalmente respetable) y mirar código fuente ajeno
requiere doble esfuerzo que crearlo uno mismo (ojo, ¡opinión
personal!). Reinventando la rueda también se aprende, y además pueden
surgir mejoras o nuevas formas de hacer las cosas que de otro modo no
hubieran aparecido.

=====================
5. Instalación y uso
=====================

Si usas el PAQUETE DEBIAN, probablemente ya lo tengas instalado y con
las dependencias resueltas. Para iniciar la aplicación, existe un icono
en el menú de Internet de Gnome. En todo caso, para usar la aplicación
necesitas Debian Squeeze/Testing o superior (al menos hasta que Squeeze
pase a ser la siguiente Stable ;)

Si usas el TARBALL, habiendolo desempaquetado e instalado las dependencias
mencionadas en el punto anterior, sólo queda ejecutar -preferiblemente-
el script "naufrago_launcher.sh". Todos los archivos y directorios que
necesite la aplicación seran creados en el directorio dónse se ejecute.
Opcionalmente, si quieres usar un icono/lanzador para iniciar la aplicación,
puedes usar el proporcionado (naufrago.desktop) cambiando la ruta hacia el 
script de inicio "naufrago_launcher.sh" y poniéndolo en el directorio
correspondiente (para Debian con GNOME, la ubicación es /usr/share/applications/).

=======================
6. Problemas / Soporte
=======================

La aplicación intenta de buen grado llevar a cabo su cometido, pero muy
seguramente no está exenta de errores. En caso de que ocurran, puedes
contactarme detallando el problema del modo más preciso posible, e intentaré
ver qué sucede para correjirlo.

============
7. Licencia
============

Esta aplicación se ampara en la GPLv3. Deberías haber recibido una copia
con la misma. De no ser así o detectar una infracción a los términos de
la misma, por favor, ponte en contacto con el autor o la FSF. ¡Está en
juego tu libertad!

===========
8. Autores
===========

Por el momento, sólo hay uno: Jordi Oliveras ( worbynet at gmail dot com ).

===================
9. Agradecimientos
===================

Debo agradecer a los que me aguantaron durante el desarrollo,
especialmente a mi pareja, y además:

- Canales Python de irc.freenode.net & irc.hispano.org.
- El maravilloso svg usado como logo de GMcGlinn
  (http://www.openclipart.org/user-detail/GMcGlinn).
- El necesario svg de RSS de SRD
  (http://www.openclipart.org/user-detail/SRD).
- El simple pero claro svg del aspa roja de raemi
  (http://www.openclipart.org/user-detail/raemi).
- Doug Quale ( quale1 at charter dot net ) & 
  Walter Anger ( WalterAnger at aon dot at ).
  por el excelente material DnD.
- El estupendo tutorial de pygtk
  (http://www.pygtk.org/pygtk2tutorial/index.html).

