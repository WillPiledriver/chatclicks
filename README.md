# chatclicks
Python package for the Twitch extension "Chat Clicks"

## Installation
```pip install chatclicks```

[Click here for the extension](https://dashboard.twitch.tv/extensions/g04l3i51oq6lqvvxpz6iaqt7rrm9eb-0.0.85)

## Setup
This is relatively simple to setup. Using the example below, you can really just do whatever you want with it. I will explain the main features. 

The main idea is to allow chat to essentially "vote" on clicks. This is done by waiting an arbitrary amount of time (polling time) to collect clicks from viewers. The program then uses math that I do not understand to find the center of the most dense cluster of clicks, and then send that data over to your code. I decided not to add code that handles clicking for the simple reason that there are many different packages that do this (pyautogui, pydirectinput, etc) and they each have their own use cases so I leave that up to you. The example below uses the package pydirectinput-rgx which i recommend to use for it's compatibility with modern games.

The extension does support bits. There are three different bits products: Chaos, Order, and Priority Clicks. Chaos reduces the polling time, and order increases the polling time. Priority Clicks gives the user's clicks more weight for their next X clicks, as defined by you. Be sure to define the bits cost in your program if you don't want people to cheat (there is no server-side verification for bits cost)

To find your channel ID, there are many 3rd party websites where you can get this channel ID with your username.

Initializing the package with your settings is as follows:
```python
cc = ChatClicks(
    channel_id="12345678",             # Channel ID of the broadcaster.
    sub_only=False,                    # Only allow subscribers to click
    allow_anonymous=False,             # Allow anonymous users to click (users that are not logged in)
    max_poll_time=10,                  # Amount of time in seconds to poll clicks
    sub_boost=1,                       # Amount of extra weight a subscriber has
    priority_boost=19,                 # Extra weight a priority user has
    priority_votes=20,                 # Amount of priority clicks a priority user gets
    tug_weight=10,                     # The weight of the tug for the chaos/order bits transaction
    dimensions="1920x1080",            # Dimensions of the screen to click on
    ban_list=[],                       # List of banned usernames
    check_coords_func=check_coords,    # Function that verifies if a click coordinates are valid
    poll_callback=poll_handler         # Function that is called after polling time
)
```
Many of these settings are for bits. If you don't have bits enabled, you do not need to worry about them. They have default settings that will have no effect on your program. the ```poll_callback``` setting will be called after polling time. It contains the center point as well as all clicks if you want to do your own calculations with that data.

This package should be used with a twitch plays chat bot, maybe even a browser source or OBS web sockets for more viewer engagement. You can do this pretty easily using asyncio. In the example, the Test class could be replaced with chat bot code. My recommendation would be to allow users to increment/decrement the ```ChatClicks.tug_of_war``` property using a chat command or something like that.

## Example

All you need is the channel ID of the broadcaster to get this to work.

You must use asyncio for your program. 

The following is a basic example:
```python
from chatclicks import ChatClicks
import asyncio
import pydirectinput as pdi

# This is where you want to check if a click coordinates are valid.
# This is just a small example that disables drag.
async def check_coords(data):
    if data["type"] == "drag":
        return False
        # check drag coordinates
    else:
        # check left/right click
        pass
    return True


# poll_dict contains all the clicks from all the users within the polling time.
# This is where you would decide where to click.
# The minimum polling time is 1/20th of a second (0.05s), and initiates at half of the max_poll_time.
async def poll_handler(center, poll_dict):
    print(center)
    print(poll_dict)
    '''if center["type"] == "drag":
        pdi.moveTo(center["start"]["x"], center["start"]["y"])
        pdi.dragTo(center["end"]["x"], center["end"]["y"], duration=0.025)
    else:
        pdi.moveTo(center["x"], center["y"], duration=0.025)
        pdi.click(center["x"], center["y"], button=center["type"])'''


cc = ChatClicks(
    channel_id="12345678",             # Channel ID of the broadcaster.
    sub_only=False,                    # Only allow subscribers to click
    allow_anonymous=False,             # Allow anonymous users to click (users that are not logged in)
    max_poll_time=10,                  # Maximum amount of time in seconds to poll clicks (initiates at half of this number)
    sub_boost=1,                       # Amount of extra weight a subscriber has
    priority_boost=19,                 # Extra weight a priority user has
    priority_votes=20,                 # Amount of priority clicks a priority user gets
    tug_weight=5,                      # The weight of the tug for the chaos/order bits transaction
    dimensions="1920x1080",            # Dimensions of the screen to click on
    ban_list=[],                       # List of banned usernames
    check_coords_func=check_coords,    # Function that verifies if click coordinates are valid
    poll_callback=poll_handler         # Function that is called after polling time
)


# bits_cost must match the config of the chat clicks extension or user bits will be wasted.
# Leave them as None if you don't care about cheaters. 
# It is technically possible for a user to change the bit cost if they know javascript.
cc.bits_cost = {
    "priority": None,
    "chaos": None,
    "order": None
}


# You can use whatever class or function (like a chat bot for example) alongside chat clicks asynchronously like this:
class Test:
    def __init__(self) -> None:
        self.loop = asyncio.get_event_loop()

    async def test_run(self):
        c = 0
        while True:
            await asyncio.sleep(1)
            print(c := c+1)
    
    def run(self):
        return self.loop.create_task(self.test_run())

# Time to run the software.

async def main():
    await cc.ban_username("barrycarlyon")
    await cc.unban_username("barrycarlyon")
    # cc.tug_of_war = 100 # This will force the poll time to be max_poll_time
    await asyncio.gather(cc.run(), Test().run())

# These are the event handlers. You can do whatever you want with these. If you remove them, the program will still work.

@cc.event(name="init")
async def on_init(data):
    pass
    #print(data)

@cc.event(name="leftClick")
async def on_left_click(data):
    pass
    #print("Left Click Data:", data)

@cc.event(name="rightClick")
async def on_right_click(data):
    pass
    #print("Right Click Data:", data)

@cc.event(name="drag")
async def on_drag(data):
    pass
    #print("Drag Data:", data)

@cc.event(name="bits")
async def on_bits(data):
    print("Bits Data:", data)
    print(cc.tug_of_war, cc.poll_time)

if __name__ == "__main__":
    asyncio.run(main())
```
