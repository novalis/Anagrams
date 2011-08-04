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
from anagrams.lib.helpers import flash
from anagrams.lib.hookbox_client import send
from anagrams.model import *

from pylons import request, url, session
from pylons.controllers.util import redirect
from pylons.decorators import rest

#handles user signing and such
class LobbyController(BaseController):
    def lobby(self):
        user = self.user

        if user.game_state == 'playing':
            return redirect(url(controller="game", action="game"))


        send('/lobby', dict(type='enter',
                            user=user.to_dict()))

        #so, the lobby shows (somehow) a list of users not in games.
        #load the initial list
        free_users = User.select((User.q.game_state == None) & ((User.q.logged_in >= User.q.logged_out) | (User.q.logged_out == None)))

        free_users = [user for user in free_users if user.is_logged_in()]
        
        c.free_users = free_users

        c.initial_data = '""'
        #is there a pending invitation?
        if user.game and user.game.state == "invite":
            game = user.game
            user.game_state == "" #unaccept
            invited = [u.display_name for u in User.selectBy(game=game) if u != game.inviter]
            message = {'type' : 'invite', 'game' : game.channel, 
                       'inviter' : game.inviter.display_name, 
                       'min_word_len' : game.min_word_len,
                       'other_players' : invited}

            c.initial_data = dumps(message)
        return render("lobby/lobby.mako")

    @rest.restrict('POST')
    def invite(self):
        #create a new game

        min_word_len = int(request.params['min_word_len'])

        def invite():
            user = self.user
            game = Game.create(user, min_word_len)

            invited = request.params.getall("invite") + [user.id]

            users = []
            for id in invited:
                player = list(User.select(User.q.id==id, forUpdate=True))
                if not player:
                    print "no such user", player
                    return None, None #no such user
                else:
                    player = player[0]
                if player.game:
                    continue
                users.append(player)
                player.game = game

            return game, users

        game, users = sqlhub.doInTransaction(invite)

        user = self.user
        user.game = game

        if game is None:
            print "Could not create game"
            return {'status' : 'Failed'} #can't create game; user will see why soon
        channel = game.channel
        create_channel(game.channel)

        invited = [u.display_name for u in users]

        for player in users:
            my_invited = invited[:]
            my_invited.remove(player.display_name)
            if user.display_name in my_invited:
                my_invited.remove(user.display_name)
            send(player.password, {'type' : 'invite', 'game' : channel, 'inviter' : user.display_name, 'other_players' : my_invited, 'min_word_len' : min_word_len})
            send("/lobby", {'type' : 'disable', 'user': {'display_name' : user.display_name}})
        return {'status' : 'OK'}

    def accept(self):
        accepted = request.params.get('accept') == "accept"
        actor = self.user
        game = actor.game
        print "accept", game
        if not game:
            #game already cancelled or something
            if accepted:
                send(actor.password, {'type' : 'message', 'message' : 'that game does not exist'})
            return {'status' : 'OK' }
        
        if accepted:
            actor.game_state = "accepted"
            type = 'accepted'
        else:
            actor.game = None
            type = 'rejected'
            send("/lobby", {'type' : 'enable', 'user': {'display_name' : actor.display_name}})

        message = "%s %s" % (actor.display_name, type)
        users = User.select(User.q.game == game)
        ready = True
        for user in users:
            if user.game_state != 'accepted':
               ready = False
            send(user.password, {'type' : 'message', 'message' : message})

        if ready:
            game.state = "playing"
            for user in users:
                user.init_game()
                send("/lobby", {'type' : 'leave', 'user' : {'display_name' : user.display_name}})
                send(user.password, {'type' : 'begin', 'game' : user.game.channel})

