# chatclicks
Python package for the Twitch extension "Chat Clicks"

## Installation
```pip install chatclicks```

## Example

All you need is the channel ID of the broadcaster to get this to work.

You must use asyncio for your program. 

The following is a basic example:
```python
from chatclicks import ChatClicks
import asyncio

# This is where you want to check if a click coordinates are valid.
# This is just a small example that disables drag.
async def check_coords(data):
    if data["action"] == "drag":
        print("fail")
        return False
    print("pass")
    return True


# poll_dict contains all the clicks from all the users within the polling time.
# This is where you would decide where to click.
# The minimum polling time is 1/20th of a second (0.05s), and initiates at half of the max_poll_time.
async def poll_handler(poll_dict):
    print(poll_dict)

cc = ChatClicks(
    channel_id="23728793",             # Channel ID of the broadcaster.
    sub_only=False,                    # Only allow subscribers to click
    allow_anonymous=False,             # Allow anonymous users to click (users that are not logged in)
    max_poll_time=10,                  # Amount of time in seconds to poll clicks
    sub_boost=1,                       # Amount of extra weight a subscriber has
    priority_boost=19,                 # Extra weight a priority user has
    priority_votes=20,                 # Amount of priority clicks a priority user gets
    tug_weight=50,                     # The weight of the tug for the chaos/order bits transaction
    ban_list=[],                       # List of banned usernames
    check_coords_func=check_coords,    # Function that verifies if a click coordinates are valid
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
            # print(c := c+1)
    
    def run(self):
        return self.loop.create_task(self.test_run())

# Time to run the software.

async def main():
    await cc.ban_username("barrycarlyon")
    await cc.unban_username("barrycarlyon")
    await asyncio.gather(cc.run(), Test().run())

# These are the event handlers. You can do whatever you want with these. If you remove them it will just default to printing data.

@cc.event(name="init")
async def on_init(data):
    print(data)

@cc.event(name="leftClick")
async def on_left_click(data):
    print("Left Click Data:", data)

@cc.event(name="rightClick")
async def on_right_click(data):
    print("Right Click Data:", data)

@cc.event(name="drag")
async def on_drag(data):
    print("Drag Data:", data)

@cc.event(name="bits")
async def on_bits(data):
    print("Bits Data:", data)

if __name__ == "__main__":
    asyncio.run(main())
```