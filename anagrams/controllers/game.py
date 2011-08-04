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
from anagrams.lib.lock_file import *
from anagrams.lib.hookbox_client import send
from anagrams.model import *
from anagrams.model.dictionary import dictionary

from pylons import request, url
from pylons.controllers.util import redirect
from pylons.decorators import rest

from simplejson import dumps


class GameController(BaseController):
    def game(self):

        user = self.user
        c.game = user.game
        if user.game_state != 'playing':
            user.game = None #we are mistakenly in this game
            user.game_state = None

            return redirect(url(action="lobby", controller="lobby"))

        return render("game/game.mako")

    def status(self):

        user = self.user
        game = user.game
        status = []
        for player in game.users:
            for word in player.words:
                status.append({'type' : 'add', 
                              'word' : word, 
                              'user' : player.to_dict(),
                              })
        status.append({'type' : 'center',
                       'letters' : game.center,
                       'bag' : len(game.bag)})
        return dumps(status)
    
    @rest.restrict('POST')
    def chat(self):
        user = self.user
        game = user.game
        message = "&lt;%s&gt; %s" % (user.display_name, 
                                     request.params.get('chat'))
        send(game.channel, {'type' : 'message', 'message' : message})

    @rest.restrict('POST')
    def turnup(self):
        user = self.user
        game = user.game
        with LockFile(lock_file_path(game.id)):
            letter = game.turnup()
            if letter:
                send(game.channel, dumps({
                            'type' : 'center',
                            'letters' : game.center,
                            'bag' : len(game.bag)
                            }))

                if len(game.bag) == 0:
                    send(game.channel, dumps({
                                'type' : 'bag_empty'
                                }))
            else:
                send(game.channel, dumps({
                            'type' : 'message',
                            'message' : "The bag is empty."
                            }))

    @rest.restrict('POST')
    def play(self):

        user = self.user
        game = user.game

        with LockFile(lock_file_path(game.id)):
            word_param = request.params.getall("word")

            to_destroy_by_id = [player_word.split("_") for player_word in word_param]
            to_destroy = [player_word[1] for player_word in to_destroy_by_id]

            center = game.center
            to_make = request.params.get("play").upper().split()
            if not to_make:
                return dumps({'type' : 'failure', 'message' : "You didn't enter any words"})

            #are all new words in the dictionary and long enough?
            nonwords = []
            tooshort = []
            for word in to_make:
                if not len(word) >= game.min_word_len:
                    tooshort.append(word)
                elif not word in dictionary:
                    nonwords.append(word)

            if nonwords or tooshort:
                message = []
                if nonwords:
                    message.append('words not in dictionary: %s' % ", ".join(nonwords))
                if tooshort:
                    message.append('too short words: %s (min length is %s)' % (", ".join(tooshort), game.min_word_len))
                return dumps({'type' : 'failure', 'message' : " and ".join(message)})


            #check that the letters match up
            destroy_letters = []
            for word in to_destroy:
                destroy_letters += list(word)
            make_letters = []
            for word in to_make:
                make_letters += list(word)
            center_letters = list(center)

            check_make_letters = make_letters[:]
            for letter in destroy_letters:
                try:
                    check_make_letters.remove(letter)
                except ValueError:
                    #a letter from the destroyed word does not appear
                    #in the made words
                    return dumps({
                            'type' : 'failure', 
                            'message' : 'not enough of ' + letter + ' in new words'
                            })

            #remaining letters in check_make_letters must appear in the center

            check_center_letters = center_letters[:]
            for letter in check_make_letters:
                try:
                    check_center_letters.remove(letter)
                except ValueError:
                    return dumps(
                        {'type' : 'failure', 
                         'message' : 'not enough ' + letter + 's in destroyed words or center'
                         })


            remaining_center_letters = check_center_letters
            used_center_letters = check_make_letters

            if len(to_make) > len(used_center_letters):
                return dumps({'type' : 'failure', 'message' : 'each word needs at least one letter from the center'})


            #figure out how to apportion letters in accordance with the rules.

#             def apportion(to_make, to_destroy, used_center_letters, destroy_letters):
#                 if len(to_make) == 0:
#                     return True #we made it!
#                 word = to_make.pop()

#                 for word in to_destroy:
#                     dup = True
#                     dup_letters = []
#                     i = 0
#                     for di, letter in enumerate(destroy):
#                         while letter != make[i]:
#                             i += 1
#                             if i == len(make):
#                                 dup = False
#                                 break 
#                         if dup = False:
#                             break
#                         dup_letters.append(letter)

#                         if di == len(destroy) - 1:
#                             #we have found all the letters in destroy,
#                             #so this is a dup
#                             break
#                         i += 1

#                         #this will cause us to fall off the end
#                         if i >= len(make):
#                             dup = False
#                             break
#                     if dup:
#                         #the made word may be (tile rule) a dup of this word.
#                         #for now, we'll say it is and return a total failure
#                         return dumps(
#                             {'type' : 'failure', 
#                              'message' : 'same letters in same order: %s, %s' % (make, destroy)
#                              })
                
#                 #but let's say it's not a dup
#                 #we still need to figure out how to apportion the center letters.
#                 for letter in center_letters:
#                     if letter in word:
#                         new_center_letters = center_letters[:]
#                         center_letters.remove(letter)
                        

#             result = apportion(to_make[:], to_destroy[:], used_center_letters[:], destroy_letters[:])

            def check_for_same_letters(make, destroy):
                dup_letters = []
                i = 0
                for di, letter in enumerate(destroy):
                    while letter != make[i]:
                        i += 1
                        if i >= len(make):
                            return []

                    dup_letters.append(letter)

                    if di == len(destroy) - 1:
                        #we have found all the letters in destroy,
                        #so this is a dup
                        return dup_letters
                    i += 1
                    #this will cause us to fall off the end
                    if i >= len(make):
                        return []


            #check each new word to see that it is not an old word in disguise
            for make in to_make:
                for destroy in to_destroy:
                    dup_letters = check_for_same_letters(make, destroy)
                    if dup_letters:
                        found_tileswap = False
                        for letter in dup_letters:
                            #are here multiple copies of this letter that
                            #we can swap around?
                            if make_letters.count(letter) > 1:
                                found_tileswap = True
                                break
                        if not found_tileswap:
                            #a real, genuine duplicate!
                            return dumps(
                                {'type' : 'failure', 
                                 'message' : 'same letters in same order: %s, %s' % (make, destroy)
                                 })

            #all is right with the world.  Let's implement it
            def implement():
                statuses = []
                players = game.users
                players_by_id = {}
                for player in players:
                    if player.id == user.id:
                        players_by_id[str(player.id)] = user
                    else:
                        players_by_id[str(player.id)] = player

                game.center = "".join(remaining_center_letters)
                for id, word in to_destroy_by_id:
                    player = players_by_id.get(id)
                    player.remove_word(word)
                    statuses.append({
                            'type' : 'remove',
                            'user' : player.to_dict(),
                            'word' : word
                            })

                for word in to_make:
                    user.add_word(word)
                    statuses.append({
                            'type' : 'add',
                            'user' : user.to_dict(),
                            'word' : word
                            })

                #send messages
                destroyed = ''
                if to_destroy:
                    destroyed = "destroyed %s and " % ", ".join(to_destroy)

                send(game.channel, {'type' : 'message', 'message' : '%s %s made %s ' % (user.display_name, destroyed, ", ".join(to_make))})

                message = {'type' : 'status', 'status' : statuses}
                send(game.channel, message)
                send(game.channel, dumps({
                            'type' : 'center',
                            'letters' : game.center,
                            'bag' : len(game.bag)
                            }))
                if len(game.center) == 0 and len(game.bag) == 0:
                    send(game.channel, dumps({
                                'type' : 'game_over'
                                }))
            sqlhub.doInTransaction(implement)

        return dumps({"status" : "OK"})

    #this will return the user to the lobby and quit them out of the game
    #which at the end of the game I guess is what you want.
    @rest.restrict('POST')
    def done(self):
        user = self.user
        user.game = None
        user.word_json = None
        user.game_state = None

        return redirect(url(action="lobby", controller="lobby"))

