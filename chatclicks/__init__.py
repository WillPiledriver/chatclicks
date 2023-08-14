import socketio

class ChatClicks():
    def __init__(self, channel_id):
        self.channel_id = channel_id
        self.sio = socketio.AsyncClient()

        self.event_handlers = {}
        # Register events with decorated methods
        self.sio.on("connect", handler=self.connect)
        self.sio.on("message", handler=self.message)
        self.sio.on("leftClick", handler=self.leftClick)
        self.sio.on("rightClick", handler=self.rightClick)
        self.sio.on("init", handler=self.init)
        self.sio.on("connect_error", handler=self.connect_error)
        self.sio.on("disconnect", handler=self.disconnect)

    def event(self, name):
        # Decorator function that takes the event name
        def decorator(func):
            # Inner decorator to wrap the event handler function
            async def async_wrapper(data):
                await func(data)  # Ensure you await the async function inside the event handler

            self.event_handlers[name] = async_wrapper  # Store the event handler
            return async_wrapper
        return decorator

    async def connect(self):
        print("Websocket connected.")
        await self.sio.emit("init", self.channel_id)

    async def message(self, data):
        print('Received message:', data)

    async def leftClick(self, data):
        if "leftClick" in self.event_handlers:
            await self.event_handlers["leftClick"](data)

    async def rightClick(self, data):
        if "rightClick" in self.event_handlers:
            await self.event_handlers["rightClick"](data)

    async def init(self, data):
        if "init" in self.event_handlers:
            await self.event_handlers["init"](data)
        else:
            if data == self.channel_id:
                print("Echo received: " + self.channel_id)

    async def connect_error(self, data):
        print("The websocket connection failed!")

    async def disconnect(self):
        print("Disconnected from websocket.")

    async def run(self):
        await self.sio.connect("https://willpile.com:8080")
        await self.sio.wait()
