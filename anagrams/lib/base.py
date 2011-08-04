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

"""The base Controller API

Provides the BaseController class for subclassing.
"""

from pylons import request, session, url, config
from pylons import tmpl_context as c
from pylons.controllers import WSGIController
from pylons.controllers.util import redirect
from pylons.decorators.secure import authenticate_form
from pylons.templating import render_mako as render
from urlparse import urlparse

import webhelpers.pylonslib.secure_form as secure_form

from anagrams.model import User

class BaseController(WSGIController):

    def __before__(self):
        environ = request.environ
        controller = environ['pylons.routes_dict'].get('controller')
        if controller != 'auth' and controller != 'user' and controller != 'hookbox':
            if c.user is None:
                redirect("/user/show_login")

    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']

        environ = request.environ
        controller = environ['pylons.routes_dict'].get('controller')
        if request.method == "POST" and controller != "auth" and controller != "hookbox" and controller != 'error':
            params = request.params
            submitted_token = params.get(secure_form.token_key)
            if submitted_token != secure_form.authentication_token():
                #raise RuntimeError("Not secure")
                pass #FIXME: uncomment above

        user_id = session.get("user_id")
        if user_id:
            c.user = self.user = User.get(user_id)
            if not self.user.is_logged_in():
                del session["user_id"]
                c.user = self.user = None
        else:
            c.user = self.user = None


        #generate hookbox server url
        hookbox_server = url('/', qualified=True)
        parsed = urlparse(hookbox_server)
        #a really fancy way of saying host:8001
        c.hookbox_server = parsed.scheme + "://" + parsed.hostname + ":" + config["hookbox_js_port"]

        return WSGIController.__call__(self, environ, start_response)
