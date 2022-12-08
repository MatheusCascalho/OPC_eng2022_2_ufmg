import pywintypes

import OpenOPC

import time

pywintypes.datetime = pywintypes.TimeType

opc = OpenOPC.client()

#opc.connect(opc.servers()[0], 'localhost')
opc.connect('Matrikon.OPC.Simulation.1', 'localhost')
tags = ['Random.Int1', 'Random.Int2']
while True:
    alarmes = opc.read(tags, group='Teste', update=1)
    print(alarmes)
    time.sleep(1)