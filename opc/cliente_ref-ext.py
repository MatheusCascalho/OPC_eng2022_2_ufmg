packages = ["gui", "sys", "appJar", "os", "OpenOPC", "path", "threading", "Pyro"]
# import the library
#!/usr/bin/python
# -*- coding: cp1252 -*-
import OpenOPC
from os import path
import sys
from appJar import gui
import time
import threading
import Pyro

#Solucao do Github para erro "modulo path nao encontrado" ao gerar exe
sys.modules['win32com.gen_py.os'] = None
sys.modules['win32com.gen_py.pywintypes'] = None
sys.modules['win32com.gen_py.pythoncom'] = None

#Variáveis globais
appIniciado = 0
threadViva = 0

# create a GUI variable called app
app = gui("Grid Demo", "800x600")

#Servidor MANU
lista_itens = "ED1,ED2,ED3,ED4,SD6,SD7,SD8,EA0,EA1,EA2,SA10,SA11"
lista_itens_nova = ""
#Servidor Bonfim
#lista_itens = ['MOT1.ENTDIG1', 'MOT1.ENTDIG2', 'MOT1.ENTDIG3', 'MOT1.LIGAR', 'MOT1.DESLIGAR', 'MOT1.BLOQUEAR', 'TQ1.Nivel', 'MOT1.Vazao', 'CORRENTE', 'TQ1.FV1004', 'TQ2.FV1004']

def conexaoOPC (opc, ip, servidor):
    while True:
        try:        
            opc.connect(servidor,ip)
            break
        except:
            print "Não foi possível conectar ao servidor OPC. Tente novamente!"
            time.sleep(3)
            break

def desconectarOPC (opc):
    while True:
        try:        
            opc.remove(opc.groups())
            opc.close()
            break
        except:
            print "Não foi possível desconectar do servidor OPC. Tentando novamente..."
            time.sleep(3)    
        
def atualiza():
    opc = OpenOPC.client()
    global appIniciado
    global threadViva
    global lista_itens_nova
    threadViva = 1
    servidor = app.getOptionBox("Servidores")
    ip = app.getEntry('IP servidor')
    conexaoOPC(opc, ip, servidor)
    while appIniciado == 1:
        try:            
            j=0
            print "Lendo dados..."
            for item in lista_itens_nova:
                valor, quality, time_ = opc.read(item)
                app.setEntry(item, str(valor))
                app.setEntry('q_' + item, str(quality))
                app.setEntry('t_' + item, str(time_))
                j+=1
            time.sleep(0.1)
        except:
            print "Não foi possível ler do servidor OPC. Tentando novamente... "
            time.sleep(2)
    desconectarOPC(opc)
            
t = threading.Thread(target=atualiza)
            
# handle button events
def pressC(button):
    global appIniciado
    global lista_itens_nova

    if button == "CONECTAR":
        appIniciado = 1
        opc = OpenOPC.client()
        servidor = app.getOptionBox("Servidores")
        ip = app.getEntry('IP servidor')
        conexaoOPC(opc, ip, servidor)
        
        lista_itens_nova = app.getEntry("Itens").split(",")

        i=4
        for item in lista_itens_nova:
            app.addLabelEntry(item, i, 0)
            app.addLabelEntry('q_' + item, i, 1)
            app.addLabelEntry('t_' + item, i, 2)
            i+=1

        #Caixa de opções para selecionar o item a ser escrito
        app.addLabelOptionBox("Options", lista_itens_nova)
        #valor a ser escrito no item
        app.addLabelEntry("Valor")
        app.setEntry("Valor", "0")

        # link the buttons to the function called press
        app.addButtons(["ESCREVER", "FECHAR", "LER"], press)
        
        if app.getOptionBox("Tipo conexao") == 'Sincrona':
            app.setButton("LER","-")
            t.start()
        else: #app.getOptionBox("Tipo conexao") == 'Assincrona'
            app.setButton("LER","LER")

    else: #button == "DESCONECTAR":
        opc = OpenOPC.client()
        desconectarOPC(opc)
    

def pressLS(button):
    opc = OpenOPC.client()
    ip = app.getEntry('IP servidor')
    servidores = opc.servers(ip)
    app.changeOptionBox("Servidores", servidores, 1, 0)
    
def press(button):
    global appIniciado
    global threadViva
    global lista_itens_nova
    if button == "FECHAR":
        appIniciado = 0
        if(threadViva == 1):
            t.join()
        app.stop()         
        
    elif button == "LER":
        opc = OpenOPC.client()
        try:
            servidor = app.getOptionBox("Servidores")
            ip = app.getEntry('IP servidor')
            conexaoOPC(opc, ip, servidor)
            print "Lendo dados..."
            item = app.getOptionBox("Options")
            valor, quality, time_  = opc.read(item)
            app.setEntry(item, str(valor))
            app.setEntry('q_' + item, str(quality))
            app.setEntry('t_' + item, str(time_))
            desconectarOPC(opc)
        except:
            print "Não foi possível ler do servidor OPC. Tente novamente."
        
    else:# button == "ESCREVER":
        opc = OpenOPC.client()
        try:
            servidor = app.getOptionBox("Servidores")
            ip = app.getEntry('IP servidor')
            conexaoOPC(opc, ip, servidor)
            opc.write( (app.getOptionBox("Options"), app.getEntry("Valor")) )
            print "Escrevendo dados..."
            app.setEntry("Valor", "0")
            desconectarOPC(opc)
        except:
            print "Não foi possível escrever no servidor OPC. Tente novamente."           

if __name__=='__main__':

    # add & configure widgets - widgets get a name
    app.addLabel("title", "Cliente OPC para ServUFMGAluno")
    app.addLabelEntry('IP servidor', 0, 0)
    app.setEntry('IP servidor', 'localhost')
    app.addButtons(["Listar Servidores"], pressLS, 0, 1)
    app.addLabelOptionBox("Servidores", [], 1, 0)
    app.addLabelEntry("Itens",2,0)
    app.setEntry('Itens', lista_itens)
    app.addLabelOptionBox("Tipo conexao", ['Sincrona','Assincrona'])    
    app.addButtons(["CONECTAR"], pressC, 3, 1)    
    app.addButtons(["DESCONECTAR"], pressC, 3, 2)
    
    # start the GUI
    app.go()
