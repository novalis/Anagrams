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

from anagrams.lib.base import BaseController, render, c
from anagrams.model import *
from anagrams.model.so_open_id_store import SOOpenIDStore
from anagrams.lib.helpers import flash
from anagrams.lib.hookbox_client import send, create_channel

from openid.consumer.consumer import Consumer, SUCCESS, CANCEL, FAILURE, SETUP_NEEDED
from openid.consumer.discover import DiscoveryFailure

from pylons import request, url, session
from pylons.controllers.util import redirect
from pylons.decorators import rest

from simplejson import dumps

#handles user signin and such
class UserController(BaseController):
    def show_login(self):
        return render("user/show_login.mako")

    def show_setup(self):
        user = self.user
        if not user:
            return redirect("show_login")
        c.email = user.email
        c.display_name = user.display_name
        return render("user/show_setup.mako")

    @rest.restrict('POST')
    def setup(self):
        user = self.user
        if not user:
            return redirect("show_login")
        display_name = request.params["display_name"]
        if not display_name:
            flash("Please enter a display name")
            return redirect(url(controller="user", action="show_setup"))

        user.display_name = display_name

        create_channel(user.password)

        return redirect(url(controller="lobby", action="lobby"))
    @rest.restrict('POST')
    def login(self):

        consumer = Consumer(session, SOOpenIDStore())
        # catch Google Apps domain that is referring, if any 
        domain = None
        if 'domain' in request.POST:
            domain = request.POST['domain']
        elif 'domain' in request.GET:
            domain = request.GET['domain']

        try:
            # two different endpoints depending on whether the using is using Google Account or Google Apps Account
            if domain:
                auth_request = consumer.begin('https://www.google.com/accounts/o8/site-xrds?hd=%s' % domain)
            else:
                auth_request = consumer.begin('https://www.google.com/accounts/o8/id')
        except DiscoveryFailure as e:
            flash ("Google Accounts Error : Google's OpenID endpoint is not available.")
            return redirect("/user/show_login")

        # add requests for additional account information required, in my case: email
        auth_request.addExtensionArg('http://openid.net/srv/ax/1.0', 'mode', 'fetch_request')
        auth_request.addExtensionArg('http://openid.net/srv/ax/1.0', 'required', 'email')
        auth_request.addExtensionArg('http://openid.net/srv/ax/1.0', 'type.email', 'http://schema.openid.net/contact/email')

        return redirect(auth_request.redirectURL(url('/', qualified=True), url(controller='user', action='google_login_response', qualified=True)))

    def google_login_response(self):
        oidconsumer = Consumer(session, SOOpenIDStore())

        # parse GET parameters submit them with the full url to consumer.complete
        _params = dict((k, unicode(v).encode('utf-8')) for k, v in request.GET.items())
        info = oidconsumer.complete(_params, request.scheme + '://' + request.host + request.path)
        display_identifier = info.getDisplayIdentifier()

        if info.status == FAILURE and display_identifier:
            flash("Verification of %(user)s failed: %(error_message)s" % {'user' : display_identifier, 'error_message' : info.message})

        elif info.status == SUCCESS:
            email = info.message.args[('http://openid.net/srv/ax/1.0', 'value.email')]
            try:
                user = User.selectBy(email=email.lower())[0]
            except IndexError:
                # create a new account if one does not exist with the authorized email yet and log that user in
                user = User.create(email=email.lower())
                user.login()
                session['user_id'] = user.id
                session.save()
                return redirect(url(action="show_setup", controller="user"))
            else:
                user.login()
                session['user_id'] = user.id
                session.save()
                return redirect(url(action="show_setup", controller="user"))

        elif info.status == CANCEL:
            flash('Google account verification cancelled.')
            return redirect(url(action="show_login", controller="user"))

        elif info.status == SETUP_NEEDED:
            if info.setup_url:
                flash('<a href="%(url)s">Setup needed</a>' % { 'url' : info.setup_url })
            else:
                # This means auth didn't succeed, but you're welcome to try
                # non-immediate mode.
                flash('Setup needed')
                return redirect(url(action="show_login", controller="user"))
        else:
            # Either we don't understand the code or there is no
            # openid_url included with the error. Give a generic
            # failure message. The library should supply debug
            # information in a log.
            flash('Google account verification failed for an unknown reason.')
            return redirect(url(action="show_login", controller="user"))
