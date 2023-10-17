import socketio
import asyncio

class ChatClicks():
    def __init__(self, channel_id, sub_only=False, allow_anonymous=True, ban_list=[], max_poll_time=10, sub_boost=1, priority_boost=4, priority_votes=5, tug_weight=50, check_coords_func=None, poll_callback=None):
        self.channel_id = channel_id
        self.allow_anonymous = allow_anonymous
        self.sub_only = sub_only
        self.ban_list = set([name.lower() for name in ban_list])
        self.sub_boost = sub_boost
        self.priority_boost = priority_boost
        self.priority_votes = priority_votes
        self.sio = socketio.AsyncClient()
        self.max_poll_time = max_poll_time
        self.poll_dict = dict()
        self.priority_dict = dict()
        self.loop = None
        self.check_coords_func = check_coords_func
        self.poll_callback = poll_callback
        self.bits_cost = None
        self.tug_weight = tug_weight
        self._tug_of_war = 500
        self.event_handlers = {}
        # Register events with decorated methods
        self.sio.on("connect", handler=self.connect)
        self.sio.on("message", handler=self.message)
        self.sio.on("leftClick", handler=self.leftClick)
        self.sio.on("rightClick", handler=self.rightClick)
        self.sio.on("drag", handler=self.drag)
        self.sio.on("bits", handler=self.bits)
        self.sio.on("init", handler=self.init)
        self.sio.on("connect_error", handler=self.connect_error)
        self.sio.on("disconnect", handler=self.disconnect)
    
    @property
    def tug_of_war(self):
        return self._tug_of_war

    @tug_of_war.setter
    def tug_of_war(self, value):
        # Clamp the value to be between 0 and 1000
        self._tug_of_war = max(0, min(1000, value))
    
    @property
    def poll_time(self):
        return max(0.05, (self._tug_of_war / 1000) * self.max_poll_time)

    def event(self, name: str):
        # Decorator function that takes the event name
        def decorator(func):
            # Inner decorator to wrap the event handler function
            async def async_wrapper(data):
                await func(data)  # Ensure you await the async function inside the event handler

            self.event_handlers[name] = async_wrapper  # Store the event handler
            return async_wrapper
        return decorator

    async def connect(self) -> None:
        print("Websocket connected.")
        await self.sio.emit("init", self.channel_id)
    
    async def message(self, data: dict) -> None:
        print('Received message:', data)

    async def add_data(self, data: dict, click: str) -> None:
        """
        Add data to poll_dict
        :param data: This is the user's data sent from the server.
        :param click: This is the user's click.
        """
        if data["opaque_id"] in self.poll_dict:
            return
        
        if click != "drag":
            if not 0 <= data["x"] <= 1:
                return
            if not 0 <= data["y"] <= 1:
                return
        else:
            if not 0 <= data["start"]["x"] <= 1:
                return
            if not 0 <= data["start"]["y"] <= 1:
                return
            if not 0 <= data["end"]["x"] <= 1:
                return
            if not 0 <= data["end"]["y"] <= 1:
                return

        if self.check_coords_func is not None:
            if not await self.check_coords_func(data):
                return

        n = 1
        if data["opaque_id"] in self.priority_dict:
            n += self.priority_boost
            self.priority_dict[data["opaque_id"]]["n"] -= 1
            if self.priority_dict[data["opaque_id"]]["n"] == 0:
                del self.priority_dict[data["opaque_id"]]
        
        if data["subscribed"]:
            n += self.sub_boost

        if click != "drag":
            new_data = {
                "login_name": data["login_name"],
                "click": click,
                "coords": {
                    "x": data["x"],
                    "y": data["y"]
                },
                "n": n
            }
        else:
            new_data = {
                "login_name": data["login_name"],
                "click": click,
                "coords": {
                    "start": data["start"],
                    "end": data["end"]
                },
                "n": n
            }

        self.poll_dict[data["opaque_id"]] = new_data

    async def leftClick(self, data: dict) -> None:
        """
        Called when a user clicks on the screen.
        :param data: This is the user's data sent from the server.
        """
        if self.sub_only and not data["subscribed"]:
            return
        if data["login_name"] in self.ban_list:
            return
        if not self.allow_anonymous:
            if data["opaque_id"].startswith("A"):
                return

        await self.add_data(data, "left")

        if "leftClick" in self.event_handlers:
            await self.event_handlers["leftClick"](data)

    async def rightClick(self, data: dict) -> None:
        """
        Called when a user right clicks on the screen.
        :param data: This is the user's data sent from the server.
        """
        if self.sub_only and not data["subscribed"]:
            return
        if data["login_name"] in self.ban_list:
            return
        if not self.allow_anonymous:
            if data["opaque_id"].startswith("A"):
                return

        await self.add_data(data, "right")

        if "rightClick" in self.event_handlers:
            await self.event_handlers["rightClick"](data)
    
    async def drag(self, data: dict) -> None:
        """
        Called when a user drags on the screen.
        :param data: This is the user's data sent from the server.
        """
        if self.sub_only and not data["subscribed"]:
            return
        if data["login_name"] in self.ban_list:
            return
        if not self.allow_anonymous:
            if data["opaque_id"].startswith("A"):
                return

        await self.add_data(data, "drag")

        if "drag" in self.event_handlers:
            await self.event_handlers["drag"](data)
    
    async def bits(self, data: dict) -> None:
        """
        Called when a user uses bits.
        :param data: This is the user's data sent from the server.
        """
        if "transaction" in data:
            print("Test Bits:", data)
        else:
            if self.bits_cost is not None:
                if self.bits_cost[data["type"]] != int(data["cost"]) and self.bits_cost[data["type"]] is not None:
                    print(f"Bits cost mismatch for user {data['display_name']} - expected {self.bits_cost[data['type']]} but got {data['cost']}")
                    return
            if data["type"] == "priority":
                if data["opaque_id"] not in self.priority_dict:
                    self.priority_dict[data["opaque_id"]] = {
                        "n": self.priority_votes,
                        "login_name": data["display_name"],
                    }
                else:
                    self.priority_dict[data["opaque_id"]]["n"] += self.priority_votes
            elif data["type"] == "chaos":
                self.tug_of_war -= self.tug_weight
            elif data["type"] == "order":
                self.tug_of_war += self.tug_weight
            if "bits" in self.event_handlers:
                await self.event_handlers["bits"](data)
            else:
                print("Bits Data:", data)

    async def init(self, data: dict) -> None:
        if "init" in self.event_handlers:
            await self.event_handlers["init"](data)
        else:
            if data == self.channel_id:
                print("Echo received: " + self.channel_id)

    async def connect_error(self, data) -> None:
        print("The websocket connection failed!", data)

    async def disconnect(self) -> None:
        print("Disconnected from websocket.")
    
    async def ban_username(self, name: str) -> None:
        self.ban_list.add(name.lower())
    
    async def unban_username(self, name: str) -> None:
        if name.lower() in self.ban_list:
            self.ban_list.remove(name.lower())

    async def click_loop(self):
        while True:
            await asyncio.sleep(self.poll_time)
            # Calculations for clicks
            if self.poll_callback is not None:
                await self.poll_callback(self.poll_dict)
            self.poll_dict = dict()
    
    async def start(self):
        self.loop.create_task(self.click_loop())
        await self.sio.connect("https://willpile.com:8080")
        await self.sio.wait()

    def run(self):
        self.loop = asyncio.get_event_loop()
        return self.loop.create_task(self.start())
        