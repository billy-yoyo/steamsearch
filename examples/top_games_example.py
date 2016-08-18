"""
This is example shows how to use steamsearch to get the top games in different categories
"""

import steamsearch

steamsearch.set_key("STEAM-API-KEY", "anotherSession", cache=True)

popular = steamsearch.top_sellers(limit=5)  # type: list[steamsearch.TopResult]
print(" --- TOP SELLERS --- ")
for result in popular:
    print(result.title)

print("")

most_played = steamsearch.top_game_playercounts(limit=5)
print(" --- TOP PLAYERCOUNTS --- ")
for result in most_played:  # result is a tuple (current_playercount, peak_playercount, game, link)
    print("{0[2]} : {0[3]}".format(result))