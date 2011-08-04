#!/usr/bin/python

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


# Based on Hookbox's producer.py, which was under the following license:

# --- License: MIT ---

# Copyright (c) 2010 Hookbox

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


import simplejson as json
import paste.deploy
import os
import pylons
import time
import urllib 
import urllib2

from datetime import datetime, timedelta
from sqlobject import sqlhub, connectionForURI
from sqlobject.sqlbuilder import Update
from traceback import print_exc

config = paste.deploy.appconfig('config:' + 'development.ini', relative_to=os.getcwd())
secret = config['server_user']

pylons.config = config

connection = connectionForURI(config['dburi'])
sqlhub.processConnection = connection

#can't import these until config and SQLObject stuff is in place
from anagrams.lib.hookbox_client import send, create_channel
from anagrams.model import *

base_url = "http://127.0.0.1:%s" % config['hookbox_rest_port']

def get_channel_info(channel_name):
    url = base_url + "/get_channel_info?channel_name=%s&security_token=%s" % (channel_name, secret)

    req = urllib2.Request(url)
    resp = urllib2.urlopen(req)
    body = resp.read()

    success, info = json.loads(body)

    if not success:
        return None
    else:
        return info

def get_subscribers(channel_name):
    info = get_channel_info(channel_name)
    if info:
        return info['subscribers']
    else:
        return None

def check_for_heartbeat():
    #check for heartbeat
    
    subscribers = get_subscribers("/heartbeat")
    if subscribers is not None:
        for subscriber in subscribers:
            try:
                user = User.selectBy(display_name=subscriber)[0]
            except IndexError:
                pass
            user.heartbeat()


        connection = User._connection
        now = datetime.now()
        update = Update(User.q, {'logged_out' : now, 'game_id' : None}, 
                        where=(now - User.q.last_ping >= timedelta(0,3 * 60,0)) & (User.q.logged_out < User.q.logged_in))
        connection.query(connection.sqlrepr(update))

    else:
        print "can't get users from heartbeat"
            

def main ():

    # assume the hookbox server is on localhost:8001
    url = base_url + "/publish"

    values = { "channel_name" : "/lobby",
               "security_token" : secret,
             }

    #
    #send("/heartbeat", {})
    create_channel("/heartbeat")
    create_channel("/lobby")

    time.sleep(60) #when you start up, give everyone a minute to check in

    while True:
        try:
            sqlhub.doInTransaction(check_for_heartbeat)
        except:
            print_exc()
            time.sleep(10)
        time.sleep(1)
                


if __name__ == "__main__":
    main()
