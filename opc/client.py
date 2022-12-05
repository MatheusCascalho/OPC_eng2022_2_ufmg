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
    url = "opc.tcp://localhost:4840/freeopcua/server_curso/"
    async with Client(url) as client:
        _logger.info(f"Root node is {client.nodes.root}")
        _logger.info(f"Object node is {client.nodes.objects}")
        children = await client.nodes.root.get_children()
        _logger.info(f"Children of root are {children}")

        uri = "http://curso.opcua.ufmg.io"
        idx = await client.get_namespace_index(uri)
        _logger.info(f"Info of our namespace is {idx}")

        modo = await client.nodes.root.get_child(
            [f"0:Objects", f"{idx}:Unidade001", f"{idx}:controlador", f"{idx}:modo"]
        )
        sp = await client.nodes.root.get_child(
            [f"0:Objects", f"{idx}:Unidade001", f"{idx}:controlador", f"{idx}:SP"]
        )

        pv = await client.nodes.root.get_child(
            [f"0:Objects", f"{idx}:Unidade001", f"{idx}:controlador", f"{idx}:PV"]
        )


        temperatura = await client.nodes.root.get_child(
            [f"0:Objects", f"{idx}:Unidade001", f"{idx}:Temperatura1"]
        )

        estado = await client.nodes.root.get_child(
            [f"0:Objects", f"{idx}:Unidade001", f"{idx}:motor", f"{idx}:Estado"]
        )

        partir = await client.nodes.root.get_child(
            [f"0:Objects", f"{idx}:Unidade001", f"{idx}:motor", f"{idx}:Partir"]
        )

        parar = await client.nodes.root.get_child(
            [f"0:Objects", f"{idx}:Unidade001", f"{idx}:motor", f"{idx}:Parar"]
        )

        obj = await client.nodes.root.get_child([f"0:Objects", f"{idx}:Unidade001"])
        # _logger.info(f"myvar is: {myvar.get_value()}")

        # subscribing to a variable node
        handler = SubHandler()
        sub = await client.create_subscription(10, handler)
        handle = await sub.subscribe_data_change(pv)
        await asyncio.sleep(0.1)

        # we can also subscribe to events from server
        await sub.subscribe_events()
        # await sub.unsubscribe(handle)
        # await sub.delete()

        # calling a method on server
        res = await obj.call_method("2:multiply", 3, "klk")
        _logger.info("method result is: %r", res)
        while True:
            data = f"\nControle:\n(1)Modo: {await modo.get_value()}\t"
            data += f"(2)PV: {await pv.get_value()}\t"
            data += f"(3)SP: {await sp.get_value()}\n"
            data += "-"*30
            data += f"\nMotor:\n(4)Estado: {await estado.get_value()}\t(5)Partir: {await partir.get_value()}\t(6)Parar: {await parar.get_value()}\n"
            data += "-" * 30
            data += f"\n(7)Temperatura: {await temperatura.get_value()}\n"
            data += "=-=" * 30
            print(data)
            alterar = input(f"Deseja alterar algum valor? (s/n): ")
            if alterar[0].lower() == 's':
                variavel = int(input(f"Selecione o a variável? "))
                novo_valor = input(f"Novo valor: ")
                if int(variavel) == 3:
                    await sp.set_value(float(novo_valor))
                elif int(variavel) == 1:
                    await modo.set_value(str(novo_valor))
                elif int(variavel) == 5:
                    await partir.set_value(bool(int(novo_valor)))
                elif int(variavel) == 6:
                    await parar.set_value(bool(int(novo_valor)))
                print("Feito!")
            else:
                print(f"Continuando...")
            await asyncio.sleep(1)
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
    logging.basicConfig(level=logging.WARNING)
    asyncio.run(main())