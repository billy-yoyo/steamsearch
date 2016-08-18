"""
This example shows how to use steamsearch to get information about a user and some information about what games they own.
"""

import steamsearch

steamsearch.set_key("STEAM-API-KEY", "exampleSession", cache=True)

user = steamsearch.get_user("billyoyo")  # type: steamsearch.UserResult
print("{0.id} :: {0.name}".format(user))  # print the user's ID and name

library = steamsearch.get_user_library(user.id)  # type: steamsearch.UserLibrary

gameid, gamename = steamsearch.get_app("civilisation 5")  # returns the gameid and gamename of civilisation 5
game = library.games.get(gameid, None)  # type: steamsearch.UserGame
print("{0} has {1} on {2}".format(user.name, game.get_playtime_string(), game.name))  # print information about playtime

top_games = library.get_top_games(limit=10)  # type: list[steamsearch.UserGame]
print(" --- TOP 10 GAMES --- ")
for game in top_games:
    print(game.name)  # prints the game's name