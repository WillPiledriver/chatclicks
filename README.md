# chatclicks
Python package for the Twitch extension "Chat Clicks"

## Installation
```pip install chatclicks```

## Example

All you need is the channel ID of the broadcaster to get this to work.

You must use asyncio for your program. 

The following is the most basic example:
```python
from chatclicks import ChatClicks
import asyncio

cc = ChatClicks("Your Channel ID here", sub_only=False, allow_anonymous=True, ban_list=[])

async def run():
    await cc.ban_username("barrycarlyon")
    await cc.unban_username("barrycarlyon")
    await cc.run()

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

if __name__ == "__main__":
    asyncio.run(run())
```