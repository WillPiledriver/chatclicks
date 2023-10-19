import socketio
import asyncio
import numpy as np
from sklearn.cluster import DBSCAN

class ChatClicks():
    def __init__(self, channel_id, sub_only=False, allow_anonymous=True, ban_list=[], max_poll_time=10, sub_boost=1, priority_boost=4, priority_votes=5, tug_weight=10, dimensions="1920x1080", check_coords_func=None, poll_callback=None):
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
        self.dimensions = [int(size) for size in dimensions.split("x")]
        self.tug_weight = tug_weight
        self._tug_of_war = 50
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
        # Clamp the value to be between -100 and 100
        self._tug_of_war = max(-100, min(100, value))
    
    @property
    def poll_time(self):
        if self.tug_of_war < 1:
            return 0.05
        return max(0, (self._tug_of_war / 100) * self.max_poll_time - 1) + 1

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
            if not 0 <= data["x"] < 1:
                return
            if not 0 <= data["y"] < 1:
                return
        else:
            if not 0 <= data["start"]["x"] < 1:
                return
            if not 0 <= data["start"]["y"] < 1:
                return
            if not 0 <= data["end"]["x"] < 1:
                return
            if not 0 <= data["end"]["y"] < 1:
                return
        
        
        data["type"] = {"leftClick": "left", "rightClick": "right", "drag": "drag"}[data["action"]]

        if data["type"] != "drag":
            data["x"] = round(data["x"] * self.dimensions[0])
            data["y"] = round(data["y"] * self.dimensions[1])
        else:
            data["start"]["x"] = round(data["start"]["x"] * self.dimensions[0])
            data["start"]["y"] = round(data["start"]["y"] * self.dimensions[1])
            data["end"]["x"] = round(data["end"]["x"] * self.dimensions[0])
            data["end"]["y"] = round(data["end"]["y"] * self.dimensions[1])

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

    async def find_center_cluster(self, poll_dict: dict) -> dict:
        # Extract coordinates and click information from the click_dict
        x_coordinates = []
        y_coordinates = []
        click_counts = {
            "left": 0,
            "right": 0,
            "drag": 0,
        }
        drag_start_coordinates = []  # For start cluster
        drag_end_coordinates = []    # For end cluster

        for user, data in poll_dict.items():
            coords = data["coords"]
            n = data["n"]

            if data["click"] == "drag":
                # For drag, separate the start and end coordinates
                x_start = coords["start"]["x"]
                y_start = coords["start"]["y"]
                x_end = coords["end"]["x"]
                y_end = coords["end"]["y"]
                
                drag_start_coordinates.extend([(x_start, y_start)] * n)
                drag_end_coordinates.extend([(x_end, y_end)] * n)
                
                click_counts["drag"] += n
            else:
                # For regular clicks
                x_coordinates.extend([coords["x"]] * n)
                y_coordinates.extend([coords["y"]] * n)
                click_counts[data["click"]] += n

        most_clicked_key = max(click_counts, key=click_counts.get)

        # Check if coordinates are empty before applying DBSCAN
        if len(x_coordinates) > 0:
            coordinates = np.column_stack((x_coordinates, y_coordinates))
            # Define the DBSCAN parameters for regular clicks
            eps = 150  # Distance threshold for clustering
            min_samples = 1  # Minimum number of points in a cluster

            # Perform DBSCAN clustering for regular clicks
            dbscan = DBSCAN(eps=eps, min_samples=min_samples)
            labels = dbscan.fit_predict(coordinates)

            # Find the cluster with the most points for regular clicks
            unique_labels, counts = np.unique(labels, return_counts=True)
            most_populated_cluster_label = unique_labels[np.argmax(counts)]

            # Get the center coordinates of the most populated cluster for regular clicks
            most_populated_cluster = coordinates[labels == most_populated_cluster_label]
            center = np.mean(most_populated_cluster, axis=0)


            x, y = (round(center[0]), round(center[1]))

        # Now, calculate centers for drag start and end coordinates
        if len(drag_start_coordinates) > 0:
            drag_start_coordinates = np.array(drag_start_coordinates)
            center_start = np.mean(drag_start_coordinates, axis=0)
            x_start, y_start = (round(center_start[0]), round(center_start[1]))

        if len(drag_end_coordinates) > 0:
            drag_end_coordinates = np.array(drag_end_coordinates)
            center_end = np.mean(drag_end_coordinates, axis=0)
            x_end, y_end = (round(center_end[0]), round(center_end[1]))
        
        if most_clicked_key.startswith("drag"):
            return {"type": "drag", "start": {"x": x_start, "y": y_start}, "end": {"x": x_end, "y": y_end}}
        elif most_clicked_key in ["left", "right"]:
            return {"type": most_clicked_key, "x": x, "y": y}
        else:
            return None

    async def click_loop(self):
        while True:
            try:
                await asyncio.sleep(self.poll_time)
                # TODO: put DBSCAN here and verify coordinates are valid
                if len(self.poll_dict) > 0:
                    result = await self.find_center_cluster(self.poll_dict)
                    if self.poll_callback is not None and await self.check_coords_func(result):
                        await self.poll_callback(result, self.poll_dict)
                    else:
                        print(result)
                    self.poll_dict = dict()
            except Exception as e:
                self.poll_dict = dict()
                print(e)
    
    async def start(self):
        self.loop.create_task(self.click_loop())
        await self.sio.connect("https://willpile.com:8080")
        await self.sio.wait()

    def run(self):
        self.loop = asyncio.get_event_loop()
        return self.loop.create_task(self.start())
        