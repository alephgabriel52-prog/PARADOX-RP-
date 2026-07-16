importar discórdia
de discórdia.extensão importar comandos
importar os
importar threading
de flask importar Flask

app = Flask('')

@app.rota('/')
def home():
    devolver "Bot PARADOX-RP tá online"

def run():
    app.correr(host='0.0.0.0', porta=10000)

def keep_alive():
    t = threading.Thread(alvo=run)
    t.iniciar()

keep_alive()


intenções = discórdia.intenções.todos()
robô = comandos.Robô(prefixo_de_comando="!")

@robô.evento
assíncrono definição pronto():
    imprimir(f'PARADOX RP ONLINE:{robô.usuário}')

@robô.comando()
assíncrono definição ping(ctx):
    aguardar ctx.enviar('Pong! Bot online')

TOKEN = os.pegar_var_ambiente('TOKEN')
robô.correr(TOKEN)
