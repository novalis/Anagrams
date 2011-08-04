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

import urllib
import urllib2

from pylons import config
from simplejson import dumps

# assume the hookbox server is on localhost
base_url = "http://127.0.0.1:%s/" % config['hookbox_rest_port']
secret = config['server_user']

def http_request(path, values):
    url = base_url + path

    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    resp = urllib2.urlopen(req)
    body = resp.read()
    return body

def create_channel(channel_name):

    values = { "channel_name" : channel_name,
               "security_token" : secret,
             }

    try:
        resp = http_request("get_channel_info", values)    
    except urllib2.HTTPError:
        #channel does not exist, create it
        values = { "channel_name" : channel_name,
                   "security_token" : secret,
                   }

        http_request("create_channel", values)    

def send(channel_name, payload):

    payload = dumps(payload)

    values = { "channel_name" : channel_name,
               "security_token" : secret,
               "payload" : payload,
             }

    http_request("publish", values)
    #page = resp.read()
    #print page
    print "sent to %s, %s" % (channel_name, payload)
                
