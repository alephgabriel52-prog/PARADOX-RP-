   import discord
de discordia.extensao importar comandos
importar os
importar threading
de flask importar Flask

aplicativo = Flask('')

@aplicativo.rota('/')
def lar():
    devolver "Bot PARADOX-RP está online"

def correr():
    aplicativo.correr(hospedar="0.0.0.0", porta=10000)

def manter_vivo():
    t = threading.Fio(alvo=correr)
    t.iniciar()

manter_vivo()


quero = discordia.quero.todos()
robô = comandos.Robô(prefixo_de_comando="!")

@robô.evento
assincrono definicao pronto():
    imprimir(f'PARADOX RP ONLINE:{robô.usuario}')

@robô.comando()
assincrono definicao ping(ctx):
    aguardar ctx.enviar('Pong! Bot online')

FICHA = os.pegar_var_ambiente('TOKEN')
robô.correr(FICHA)
