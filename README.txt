Anagrams!  Well, according to my half-remembered rules, anyway.



Installation and Setup
======================

Install ``anagrams`` using easy_install::

    easy_install anagrams

Make a config file as follows::

    paster make-config anagrams config.ini

Tweak the config file as appropriate and then setup the application::

    paster setup-app config.ini

Edit hookbox.sh

Then you are ready to go.


Running
======================
./hookbox.sh&
python hookserver.py&
paster serve [ini file]
