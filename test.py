from chatclicks import ChatClicks
import asyncio
import pydirectinput as pdi

# This is where you want to check if a click coordinates are valid.
# This is just a small example that disables drag.
async def check_coords(data):

    print("CHECK COORDS:")
    print(data)
    whitelist = ["thepiledriver", "random_username", "twitchplaysspeedruns"]
    whitelist = [user.lower() for user in whitelist]
    if "login_name" in data and data["login_name"] is not None and data["login_name"].lower() not in whitelist:
        return False
    return True


# poll_dict contains all the clicks from all the users within the polling time.
# This is where you would decide where to click.
# The minimum polling time is 1/20th of a second (0.05s), and initiates at half of the max_poll_time.
async def poll_handler(center, poll_dict):
    print(center)
    print(poll_dict)
    


cc = ChatClicks(
    channel_id="23728793",             # Channel ID of the broadcaster.
    sub_only=False,                    # Only allow subscribers to click
    allow_anonymous=False,             # Allow anonymous users to click (users that are not logged in)
    max_poll_time=10,                  # Maximum amount of time in seconds to poll clicks (initiates at half of this number)
    sub_boost=1,                       # Amount of extra weight a subscriber has
    priority_boost=19,                 # Extra weight a priority user has
    priority_votes=20,                 # Amount of priority clicks a priority user gets
    tug_weight=5,                      # The weight of the tug for the chaos/order bits transaction
    monitor=1,
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
    # print("Left Click Data:", data)

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