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
from fake_arduino import FakeArduino

# Configurações de log
logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger('asyncua')

# Objetos e Variáveis monitoradas
idx_saidas = {}

# Use a compound data type for structured arrays
bd_dados = np.zeros(20, dtype={
    'names': ('Tag', 'valor', 'valor_escrever', 'idx_valores', 'eh_escrita', 'tipo', 'escrever', 'canal'),
    'formats': ('a16', 'f8', 'i4', 'i2', 'a1', 'a2', 'a1', 'i2')
})


class SubHandler(object):
    """
    Subscription handler. To receive events from server for a subscription
    """

    def datachange_notification(self, node, val, data):
        global bd_dados
        global num_pts
        global arduino

        print("Python: New data change event", node, val)
        print("Valor recebido via OPC")

        _logger.info('datachange_notification %r %s', val, node)
        try:
            if (str(node) in idx_saidas.keys()):
                _logger.info(f'Indice da saída: {idx_saidas[str(node)]}')
                if (
                        ((bd_dados[idx_saidas[str(node)]]['eh_escrita']).decode('utf-8') == 'S') &
                        (bd_dados[idx_saidas[str(node)]]['valor'] != val)
                ):
                    bd_dados[idx_saidas[str(node)]]['valor_escrever'] = val
                    bd_dados[idx_saidas[str(node)]]['escrever'] = 'S'
        except Exception as e:
            print(e)

    def event_notification(self, event):
        print('Python: New event: ', event)


# Method to be exposed through server
# uses as decorator to automatically convert to and from variants


@uamethod
def multiply(parent, x, y):
    print(f"Multiply method call with parameters: {x=}, {y=}")
    return x*y


def le_arduino():
    global bd_dados
    global num_pts
    global arduino

    # Faz escrita antes de ler
    for i in range(num_pts):
        if ((bd_dados[i]['escrever']).decode('utf-8') == 'S'):
            canal = (bd_dados[i]['canal'])
            valor = bd_dados[i]['valor_escrever']
            if ((bd_dados[i]['tipo']).decode('utf-8') == 'DO'):
                write_DO(canal, valor)
                # bd_dados[i]['escrever'] = 'N'
            if ((bd_dados[i]['tipo']).decode('utf-8') == 'AO'):
                write_AO(canal, valor)
                # bd_dados[i]['escrever'] = 'N'

    DI = []
    DO = []
    AI = []
    AO = []

    for i in range(5):
        DI.append(0)
    for i in range(2):
        DO.append(0)
    for i in range(3):
        AI.append(0)
    for i in range(2):
        AO.append(0)

    value = write_read(1)
    print(value)
    if (len(value) > 0):
        caux = value.decode('utf-8').split(';')
        for i in range(5):
            DI[i] = bool(int(caux[i + 1].split(',')[1]))
        for i in range(2):
            DO[i] = bool(int(caux[i + 6].split(',')[1]))
        for i in range(3):
            AI[i] = float(int(caux[i + 8].split(',')[1]))
        for i in range(2):
            AO[i] = float(int(caux[i + 11].split(',')[1]))

        valores = {}
        valores["DI"] = DI
        valores["DO"] = DO
        valores["AI"] = AI
        valores["AO"] = AO

        for i in range(num_pts):
            bd_dados[i]['valor'] = valores[bd_dados[i]['tipo'].decode('utf-8')][bd_dados[i]['idx_valores']]
    return valores


async def main():
    global bd_dados
    global num_pts
    global arduino

    # Setup our server
    server = Server()
    await server.init()
    server.disable_clock()  # for debugging
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server_curso/")
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
    await (await dev.add_variable(idx, "Temperatura1", 1.0)).set_modelling_rule(True)
    await (await dev.add_property(idx, "Descricao", "Separacao")).set_modelling_rule(True)

    ctrl = await dev.add_object(idx, "controlador")
    await ctrl.set_modelling_rule(True)
    await (await ctrl.add_property(idx, "modo", "MAN")).set_modelling_rule(True)
    await (await ctrl.add_variable(idx, "PV", 0.0)).set_modelling_rule(True)
    await (await ctrl.add_variable(idx, "SP", 0.0)).set_modelling_rule(True)

    motor = await dev.add_object(idx, "motor")
    await motor.set_modelling_rule(True)
    await (await motor.add_variable(idx, "Estado", False)).set_modelling_rule(True)
    await (await motor.add_variable(idx, "Partir", False)).set_modelling_rule(True)
    await (await motor.add_variable(idx, "Parar", False)).set_modelling_rule(True)

    # populating our address space
    # instantiate one instance of our device
    unidade001 = await server.nodes.objects.add_object(idx, "Unidade001", dev)

    # get proxy to our device state variable
    ctrl_modo001 = await unidade001.get_child([f"{idx}:controlador", f"{idx}:modo"])
    ctrl_pv001 = await unidade001.get_child([f"{idx}:controlador", f"{idx}:PV"])
    ctrl_sp001 = await unidade001.get_child([f"{idx}:controlador", f"{idx}:SP"])
    temperatura001 = await unidade001.get_child([f"{idx}:Temperatura1"])
    motor_estado001 = await unidade001.get_child([f"{idx}:motor", f"{idx}:Estado"])
    motor_partir001 = await unidade001.get_child([f"{idx}:motor", f"{idx}:Partir"])
    motor_parar001 = await unidade001.get_child([f"{idx}:motor", f"{idx}:Parar"])

    # Set MyVariable to be writable by clients
    await ctrl_sp001.set_writable()
    await ctrl_modo001.set_writable()
    await motor_partir001.set_writable()
    await motor_parar001.set_writable()

    multiply_node = await unidade001.add_method(
        idx,
        "multiply",
        multiply,
        [ua.VariantType.Int64, ua.VariantType.Int64],
        [ua.VariantType.Int64],
    )

    # create directly some objects and variables
    idx_saidas[str(ctrl_sp001)] = 10  # AO-0 - A11
    idx_saidas[str(motor_partir001)] = 5  # DO-0 - D6
    idx_saidas[str(motor_parar001)] = 6  # DO-1 - D7
    idx_saidas[str(ctrl_modo001)] = 2  # DI-2 - D2

    # creating a default event object
    # The event object automatically will have member for all events properties
    # you probably want to create a custom event type, see other examples
    myevgen = await server.get_event_generator()
    myevgen.event.Severity = 300

    # starting!
    async with server:
        print(f"Available loggers are: {logging.Logger.manager.loggerDict.keys()}")
        # enable following if you want to subscribe to nodes on server side
        handler = SubHandler()
        sub = await server.create_subscription(period=500, handler=handler)
        nos_saidas = [
            ctrl_modo001,
            ctrl_sp001,
            motor_partir001,
            motor_parar001
        ]
        handle = await sub.subscribe_data_change(nodes=nos_saidas)

        # we can also subscrive to events from server
        await sub.subscribe_events()
        server.subscribe_server_callback(event=4, handle=handler)

        await myevgen.trigger(message="This is BaseEvent")

        contador = 0
        while True:
            await asyncio.sleep(2.0)
            valores = le_arduino()
            contador += 1
            if contador > -1:
                await server.write_attribute_value(temperatura001.nodeid, ua.DataValue(valores['AI'][1]))
                await server.write_attribute_value(ctrl_pv001.nodeid, ua.DataValue(valores['AI'][0]))
                await server.write_attribute_value(ctrl_sp001.nodeid, ua.DataValue(valores['AO'][0]))
                if valores['DI'][1]:
                    await server.write_attribute_value(ctrl_modo001.nodeid, ua.DataValue('MAN'))
                else:
                    await server.write_attribute_value(ctrl_modo001.nodeid, ua.DataValue('AUTO'))
                await server.write_attribute_value(motor_estado001.nodeid, ua.DataValue(valores['DI'][0]))
                await server.write_attribute_value(motor_partir001.nodeid, ua.DataValue(valores['DO'][0]))
                await server.write_attribute_value(motor_parar001.nodeid, ua.DataValue(valores['DO'][1]))
                contador = 0


def write_read(x):
    global arduino
    arduino.write_lines([b'?', b'\n'])
    time.sleep(2.0)
    data = arduino.read_line()
    return data


def write_DO(canal, val):
    global arduino
    if (int(val) != 0):
        comando_str1 = 'SD' + str(canal) + ' ' + '1\n'
    else:
        comando_str1 = 'SD' + str(canal) + ' ' + '0\n'
    comando_str1_byte = str.encode(comando_str1)
    arduino.write_lines([comando_str1_byte])
    time.sleep(2.0)
    return


def write_AO(canal, val):
    global arduino
    valor = val
    ivalor = int(valor)
    canal = str(canal) if canal > 9 else '0' + str(canal)

    if ivalor > 255:
        ivalor = 255
    elif ivalor <= 0:
        ivalor = 0
    comando_str1 = 'SA' + str(canal) + ' ' + str(ivalor) + '\n'
    comando_str1_byte = str.encode(comando_str1)
    arduino.write_lines([comando_str1_byte])
    time.sleep(2.0)
    return


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.optionxform(str())
    config.read('server-example.ini')
    config.sections()
    if 'ARDUINO' not in config:
        print('As configurações do executor não foram definidas.')
    if 'DI' not in config:
        print("Nada a ser lido DI.")
    if 'DO' not in config:
        print("Nada a ser lido DO.")
    if 'AI' not in config:
        print("Nada a ser lido AI.")
    if 'AO' not in config:
        print("Nada a ser lido AO.")

    porta_com = config['ARDUINO'].get('PORTA', 'COM4')
    periodo_arduino_Str = config['ARDUINO'].get('PERIODO', '2')

    try:
        periodo_arduino = float(periodo_arduino_Str)
    except:
        periodo_arduino = 2.0
    try:
        arduino = serial.Serial(port=porta_com, baudrate=9600, timeout=periodo_arduino)
    except serial.SerialException:
        print("Porta USB não detectada. O sistema irá constinuar funcionando com um arduino FAKE")
        arduino = FakeArduino()

    # pontoa
    tag_list = dict(config['DI'])
    num_ent = len(tag_list)
    num_pts = 0
    i = 0
    for tag in tag_list:
        bd_dados[num_pts]['Tag'] = tag
        bd_dados[num_pts]['eh_escrita'] = 'S'
        bd_dados[num_pts]['idx_valores'] = i
        bd_dados[num_pts]['tipo'] = 'DI'
        bd_dados[num_pts]['escrever'] = 'S'
        bd_dados[num_pts]['canal'] = i
        i += 1
        num_pts += 1
    tag_list = dict(config['DO'])
    i = 0
    for tag in tag_list:
        bd_dados[num_pts]['Tag'] = tag
        bd_dados[num_pts]['eh_escrita'] = 'S'
        bd_dados[num_pts]['idx_valores'] = i
        bd_dados[num_pts]['tipo'] = 'DO'
        bd_dados[num_pts]['escrever'] = 'S'
        bd_dados[num_pts]['canal'] = i + 5
        i += 1
        num_pts += 1
    tag_list = dict(config['AI'])
    i = 0
    for tag in tag_list:
        bd_dados[num_pts]['Tag'] = tag
        bd_dados[num_pts]['eh_escrita'] = 'S'
        bd_dados[num_pts]['idx_valores'] = i
        bd_dados[num_pts]['tipo'] = 'AI'
        bd_dados[num_pts]['escrever'] = 'N'
        bd_dados[num_pts]['canal'] = i + 7
        i += 1
        num_pts += 1
    tag_list = dict(config['AO'])
    i = 0
    for tag in tag_list:
        bd_dados[num_pts]['Tag'] = tag
        bd_dados[num_pts]['eh_escrita'] = 'S'
        bd_dados[num_pts]['idx_valores'] = i
        bd_dados[num_pts]['tipo'] = 'AO'
        bd_dados[num_pts]['escrever'] = 'N'
        bd_dados[num_pts]['canal'] = i + 10
        i += 1
        num_pts += 1

    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())


