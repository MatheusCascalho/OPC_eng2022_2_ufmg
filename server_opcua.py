import asyncio
import copy
import logging
from datetime import datetime
import time
from math import sin
import serial
import numpy as np
import configparser

from asyncua import ua, uamethod, Server
from opc.fake_arduino import FakeArduino


# Configurações de log
logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger('asyncua')

async def main():
    # Setup our server
    server = Server()
    await server.init()
    server.disable_clock()  # for debugging
    server.set_endpoint("opc.tcp://0.0.0.0:48401/freeopcua/server_curso/")
    server.set_server_name("FreeOpcUa Example Server Curso")

    # set all possible endpoint policies for clients to connect through
    server.set_security_policy([
        ua.SecurityPolicyType.NoSecurity,
        ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt,
        ua.SecurityPolicyType.Basic256Sha256_Sign
    ])

    # setup out own namespace
    uri = "http://curso.opcua.ufmg.io"
    idx = await server.register_namespace(uri=uri)

    # create a new node type we can instantiate in our addres space
    dev = await server.nodes.base_object_type.add_object_type(idx, "Processo")

    # populating our address space
    # instantiate one instance of our device
    unidade001 = await server.nodes.objects.add_object(idx, "Unidade001", dev)
