from channels.generic.websocket import AsyncJsonWebsocketConsumer


class ContainerConsumer(AsyncJsonWebsocketConsumer):
    group_name = "containers"

    async def connect(self):
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def container_event(self, event):
        # event["data"] и event["event"] приходят из group_send
        await self.send_json(
            {
                "event": event["event"],
                "data": event["data"],
            }
        )
