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

from pylons import request, url

from simplejson import dumps

from anagrams.lib.base import BaseController
from anagrams.model import *


ALLOW = dumps([True, {}])
FORBID = dumps([False, {}])
#handles hookbox authentication
class HookboxController(BaseController):
    def connect(self):
        user = self.user
        if not user:
            print ("forbid");
            return FORBID

        return dumps([True, {"name":user.display_name}])


    def disconnect(self):
        return ALLOW

    def unsubscribe(self):
        return ALLOW

    def subscribe(self):
        user = self.user
        if not user:
            return dumps([False, {}])

        channel = request.params.get("channel_name") 

        print "sub", channel          

        return dumps([True, {"initial_data": {'foo' : 'bar'}}])
        return ALLOW

    def publish(self):
        #FIXME
        return ALLOW

    def destroy_channel(self):
        return ALLOW

    def create_channel(self):

        channel = request.params.get('channel_name')

        #is it a user channel?
        user = self.user
        if user and user.password == channel:
            return dumps([ True, { "history_size" : 0,
                                   "reflective" : False,
                                   "presenceful" : False } ])

        #is it a game channel
        if user and user.game and user.game.channel == channel:
            return dumps([ True, { "history_size" : 0,
                                   "reflective" : False,
                                   "presenceful" : False } ])


        if channel == '/lobby' or channel == "/heartbeat":
            
            return dumps([ True, { "history_size" : 3,
                                   "reflective" : True,
                                   "presenceful" : True } ])
        else:
            print "forbbiden: ", request.params
            return FORBID
