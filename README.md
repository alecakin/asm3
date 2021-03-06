Animal Shelter Manager v3 (sheltermanager3)
===========================================

This program is covered by the terms of the GNU General Public Licence v3. 
See the file LICENSE in this directory for details.

Dependencies
------------

If you are using a Debian-based system (eg: Ubuntu), then the following
will install all the software you need to run ASM. If you are using the 
sheltermanager3 deb package it already has dependencies set for these
and will install them for you.

* apt-get install make python3 python3-webpy python3-pil python3-mysqldb python3-psycopg2

Extra, non-mandatory packages:

* apt-get install imagemagick (for scaling/compressing PDFs to save on storage)
* apt-get install wkhtmltopdf (for creating PDFs from HTML document templates)
* apt-get install python3-reportlab (for creating mailing label PDFs)
* apt-get install python3-requests (needed for all HTTPS publishers - PetLink, MeetAPet, VetEnvoy)
* apt-get install python3-boto3 (needed for Amazon S3 media storage)

Packages necessary for building static checkers, installers and manuals:

* apt-get install exuberant-ctags nodejs pychecker python3-sphinx python3-sphinx-rtd-theme texlive-latex-base texlive-latex-extra latexmk

If you're using Debian and want to do development, you can use "make deps"
to install the needed dependencies.

Logging
-------

ASM logs to the Unix syslog USER facility (/var/log/user.log for most installs)
by default. This can be changed in the configuration.

Configuring ASM
---------------

If you used the debian package, edit the file /etc/asm3.conf

If you did not, copy scripts/asm3.conf.example to /etc/asm3.conf and edit it.

Set the following values:

asm3_dbtype = (POSTGRESQL, MYSQL or SQLITE)

asm3_dbhost = (hostname of your server)

asm3_dbport = (port of your server if using tcp)

asm3_dbusername = 

asm3_dbpassword = 

asm3_dbname = (name of the database, can be file path if type is SQLITE)

If you are using MySQL or POSTGRESQL, make sure you have issued a CREATE DATABASE
and the database already exists (however the schema can be empty).

ASM will look for it's config file in this order until it finds one:

1. In an environment variable called ASM3_CONF
2. In $INSTALL_DIR/asm3.conf (the folder asm3 python modules are installed in)
3. In $HOME/.asm3.conf (the home directory of the user running asm3)
4. In /etc/asm3.conf

Setting up Apache/WSGI
----------------------

Set up Apache to serve the application.

1. Install apache2 with mod_wsgi. Make sure mod_wsgi is enabled.

   * apt-get install apache2 libapache2-mod-wsgi-py3
   * a2enmod wsgi

2. Add the WSGI config to your Apache site config. The default site config
   as installed by Debian is in /etc/apache2/sites-available/default
   
   Add this at the bottom of the file (outside of the VirtualHost tag).

```
WSGIScriptAlias /asm /usr/lib/sheltermanager3/code.py/
Alias /asm/static /usr/lib/sheltermanager3/static
AddType text/html .py
<Directory /usr/lib/sheltermanager3>
    Require all granted
</Directory>
```

   This assumes that your ASM3 is located at /usr/lib/sheltermanager3
   (the default for our Debian package)

3. Restart Apache and navigate to http://localhost/asm

    * service apache2 restart

Creating the default database
-----------------------------

After the ASM service has started, visit http://localhost/asm/database
to create the database schema (hitting just http://localhost/asm will
redirect there if no database has been setup yet).

Daily tasks
-----------

ASM has a batch of routines that need to be run every day. These
should be run a few hours before people will start inputting for the
day.

These routines include recalculating denormalised data such as animal age, time
on shelter, updating the waiting list and publishing to the internet.

To run them, make sure the environment is setup as before and run
python3 cron.py all

See the cron.py file for more information on mode parameters to run 
specific tasks only.

The Debian package automatically adds the daily tasks to /etc/cron.daily 


