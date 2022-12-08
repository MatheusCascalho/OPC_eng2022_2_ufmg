import asyncio
from asyncua.client import Client
from asyncua.client.ua_file import UaFile
class SubHandler(object):
    """
    Subscription Handler. To receive events from server for a subscription
    data_change and event methods are called directly from receiving thread.
    Do not do expensive, slow or network operation there. Create another
    thread if you need to do such a thing
    """

    def datachange_notification(self, node, val, data):
        print("New data change event", node, val)

    def event_notification(self, event):
        print("New event", event)



async def read_file():
    """ read file example """

    url = "opc.tcp://desktop-kmb3vdt:51210/UA/SampleServer"
    async with Client(url=url) as client:
        root = client.nodes.root
        print("Objects node is: %r", root)
        print("Children of root are: %r", await root.get_children())
        node = client.get_node("ns=2;i=10219")
        value = await node.read_value()
        print(value)

       # # async with UaFile(file_node, 'r') as ua_file:
       #      contents = await ua_file.read()  # read file
       #      print(contents)

# subscribing to a variable node
        handler = SubHandler()
        sub = await client.create_subscription(10, handler)
        handle = await sub.subscribe_data_change(node)
        await asyncio.sleep(0.1)



        # we can also subscribe to events from server
        await sub.subscribe_events()

        while True:
            print(f"valor: {await node.get_value()}")
            await asyncio.sleep(1)

asyncio.run(read_file())