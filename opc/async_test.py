import asyncio
import time

async def outrafuncao():
    await asyncio.sleep(2)
    print(f"Momento outra funcao {time.strftime('%X')}")
    print("Minha mensagem 1")


async def outrafuncao2():
    await asyncio.sleep(1)
    print(f"Momento outra funcao 2 {time.strftime('%X')}")
    print("Minha mensagem 2")


async def funcao():
    print(f"Iniciou {time.strftime('%X')}")
    task = asyncio.create_task(outrafuncao())
    print(f"Terminou {time.strftime('%X')}")

    await task
    task1 = asyncio.create_task(outrafuncao2())
    await task1
    print(f"Terminou TUDO {time.strftime('%X')}")

asyncio.run(funcao())
