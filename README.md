# chatclicks
Python package for the Twitch extension "Chat Clicks"

All you need is the channel ID of the broadcaster to get this to work.

I Strongly recommend using asyncio or some other asynchronous method for your program. 
The following is the most basic example:
```python
from chatclicks import ChatClicks
import asyncio

cc = ChatClicks(channel_id="Your channel ID goes here")

async def run():
    await cc.run()

@cc.event(name="init")
async def on_init(data):
    print(data)

# Put your Left Click code here.
@cc.event(name="leftClick")
async def on_left_click(data):
    print("Left Click Data:", data)

# Put your Right Click code here.
@cc.event(name="rightClick")
async def on_right_click(data):
    print("Right Click Data:", data)

if __name__ == "__main__":
    asyncio.run(run())```
