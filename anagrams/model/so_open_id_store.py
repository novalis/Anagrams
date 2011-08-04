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

import openid.store
from openid.store.interface import OpenIDStore
from openid.association import Association as OIDAssociation

from models import *
import base64
import time

class SOOpenIDStore(OpenIDStore):
    """
    Store OpenID authentication data.  Based on 
    http://stackoverflow.com/questions/4307677/django-google-federated-login
    """

    def storeAssociation(self, server_url, association):
        assoc = Association(
            server_url = server_url,
            handle = association.handle,
            secret = base64.encodestring(association.secret),
            issued = association.issued,
            lifetime = association.lifetime, #this still might be bad
            assoc_type = association.assoc_type
        )


    def getAssociation(self, server_url, handle=None):
        assocs = []
        if handle is not None:
            assocs = Association.selectBy (
                server_url = server_url, handle = handle
            )
        else:
            assocs = Association.selectBy (
                server_url = server_url
            )
        if not assocs:
            return None
        associations = []
        for assoc in assocs:
            association = OIDAssociation(
                assoc.handle, 
                base64.decodestring(assoc.secret), 
                assoc.issued,
                assoc.lifetime, 
                assoc.assoc_type
            )
            if association.expiresIn == 0:
                self.removeAssociation(server_url, assoc.handle)
            else:
                associations.append((association.issued, association))
        if not associations:
            return None
        return associations[-1][1]

    def removeAssociation(self, server_url, handle):
        assocs = list(Association.selectBy(
            server_url = server_url, handle = handle
        ))
        assocs_exist = len(assocs) > 0
        for assoc in assocs:
            assoc.destroySelf()
        return assocs_exist

    def useNonce(self, server_url, timestamp, salt):
        # Has nonce expired?
        if abs(timestamp - time.time()) > openid.store.nonce.SKEW:
            return False
        try:
            nonce = Nonce.selectBy(
                server_url = server_url,
                timestamp = timestamp,
                salt = salt
            )[0]
        except IndexError:
            nonce = Nonce(
                server_url = server_url,
                timestamp = timestamp,
                salt = salt
            )
            return True
        nonce.destroySelf()
        return False

    def cleanupNonce(self):
        Nonce.select(
            Nonce.q.timestamp < (int(time.time()) - openid.store.nonce.SKEW)
        ).destroySElf()

    def cleaupAssociations(self):
        Association.select(
            issued + lifetimeint < time.time()
        ).destroySelf()

    def getAuthKey(self):
        return md5_constructor.new(config.get['app_conf']['openid_secret']).hexdigest()

    def isDumb(self):
        return False
