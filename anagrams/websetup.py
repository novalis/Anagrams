# Copyright 2011, David Turner <novalis@novalis.org>
#
# This program is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of
# the License, or (props, at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Setup the anagrams application"""

import logging
import os
import pylons.test

from paste.deploy import appconfig

from anagrams.config.environment import load_environment
from anagrams.model import *


log = logging.getLogger(__name__)

def setup_app(command, conf, vars):
    """Place any commands to setup anagrams here"""
    # Don't reload the app if it was loaded under the testing environment
    if not pylons.test.pylonsapp:
        load_environment(conf.global_conf, conf.local_conf)
    else:
        for table in soClasses[::-1]:
            table.dropTable(ifExists=True)
    for table in soClasses:
        table.createTable(ifNotExists=True)

    lock_path = os.path.join(conf.local_conf['cache_dir'], 'locks')
    if not os.path.exists(lock_path):
        os.mkdir(lock_path)
