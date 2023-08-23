import socketio

class ChatClicks():
    def __init__(self, channel_id, sub_only=False, allow_anonymous=True, ban_list=[]):
        self.channel_id = channel_id
        self.allow_anonymous = allow_anonymous
        self.sub_only = sub_only
        self.ban_list = set([name.lower() for name in ban_list])
        self.sio = socketio.AsyncClient()

        self.event_handlers = {}
        # Register events with decorated methods
        self.sio.on("connect", handler=self.connect)
        self.sio.on("message", handler=self.message)
        self.sio.on("leftClick", handler=self.leftClick)
        self.sio.on("rightClick", handler=self.rightClick)
        self.sio.on("drag", handler=self.drag)
        self.sio.on("init", handler=self.init)
        self.sio.on("connect_error", handler=self.connect_error)
        self.sio.on("disconnect", handler=self.disconnect)

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

    async def leftClick(self, data: dict) -> None:
        if self.sub_only and not data["subscribed"]:
            return
        if data["login_name"] in self.ban_list:
            return
        if not self.allow_anonymous:
            if data["opaque_id"].startswith("A"):
                return
        if "leftClick" in self.event_handlers:
            await self.event_handlers["leftClick"](data)

    async def rightClick(self, data: dict) -> None:
        if self.sub_only and not data["subscribed"]:
            return
        if data["login_name"] in self.ban_list:
            return
        if not self.allow_anonymous:
            if data["opaque_id"].startswith("A"):
                return
        if "rightClick" in self.event_handlers:
            await self.event_handlers["rightClick"](data)
    
    async def drag(self, data: dict) -> None:
        if self.sub_only and not data["subscribed"]:
            return
        if data["login_name"] in self.ban_list:
            return
        if not self.allow_anonymous:
            if data["opaque_id"].startswith("A"):
                return
        if "rightClick" in self.event_handlers:
            await self.event_handlers["drag"](data)

    async def init(self, data: dict) -> None:
        if "init" in self.event_handlers:
            await self.event_handlers["init"](data)
        else:
            if data == self.channel_id:
                print("Echo received: " + self.channel_id)

    async def connect_error(self, data: dict) -> None:
        print("The websocket connection failed!")

    async def disconnect(self) -> None:
        print("Disconnected from websocket.")
    
    async def ban_username(self, name: str) -> None:
        self.ban_list.add(name.lower())
    
    async def unban_username(self, name: str) -> None:
        if name.lower() in self.ban_list:
            self.ban_list.remove(name.lower())

    async def run(self):
        await self.sio.connect("https://willpile.com:8080")
        await self.sio.wait()
