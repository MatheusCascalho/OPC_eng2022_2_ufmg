from asyncua import Client
import asyncio
import time
import logging

_logger = logging.getLogger(__name__)


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

async def main():
    url = "opc.tcp://localhost:48401/freeopcua/server_curso/"
    async with Client(url) as client:
        _logger.info(f"Root node is {client.nodes.root}")
        _logger.info(f"Object node is {client.nodes.objects}")
        children = await client.nodes.root.get_children()
        _logger.info(f"Children of root are {children}")

        uri = "http://curso.opcua.ufmg.io"
        idx = await client.get_namespace_index(uri)
        _logger.info(f"Info of our namespace is {idx}")

        grandson = await children[0].get_children()
        myvar = await client.nodes.root.get_child([f"0:Objects", f"{idx}:Unidade001", f"{idx}:controlador", f"{idx}:modo"])
        path = await client.get_node('ns=2;i=16').get_path(as_string=True)
        obj = await client.nodes.root.get_child([f"0:Objects", f"{idx}:Unidade001"])
        value = await myvar.read_value()
        # _logger.info(f"myvar is: {myvar.get_value()}")

        # subscribing to a variable node
        handler = SubHandler()
        sub = await client.create_subscription(10, handler)
        handle = await sub.subscribe_data_change(myvar)
        await asyncio.sleep(0.1)

        # we can also subscribe to events from server
        await sub.subscribe_events()
        # await sub.unsubscribe(handle)
        # await sub.delete()

        # calling a method on server
        res = await obj.call_method("2:multiply", 3, "klk")
        _logger.info("method result is: %r", res)
        while True:
            await asyncio.sleep(1)

        print(".")
    # # try:
    # client.connect()
    # root = client.get_root_node()
    # temperatura = asyncio.create_task(root.get_child(path=['0:Objects', '2:controlador', '2:PV']))
    # t = await temperatura
    # print(f"Temperatura: {temperatura}")
    # while True:
    #     print(f"Temperatura: {temperatura.get_value()}")
    # except:
    #     client.disconnect()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())