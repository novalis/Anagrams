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

import os
from pylons import config

def lock_file_path(game_id):
    lock_path = os.path.join(config['app_conf']['cache_dir'], 'locks')
    lock_file_path = os.path.join(lock_path, str(game_id) + ".lock")
    return lock_file_path

