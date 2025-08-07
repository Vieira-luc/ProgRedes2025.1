import socket
import threading
import os
import hashlib
import glob

HOST = '0.0.0.0'
PORT = 57432
BUFFER_SIZE = 4096
PASTAARQSERVER = os.path.realpath("server/arquivos") #para o usuario não acessar uma pasta indevida

def envia_dados(conn, dados:bytes):     #função para auxiliar na garantia que todos os dados foram enviados
    total_enviado = 0
    while total_enviado < len(dados):
        enviado = conn.send(dados[total_enviado:])
        if enviado == 0:
            raise RuntimeError("ERRO: ENVIO DE DADOS FALHOU")
        total_enviado += enviado

def recebe_linha(conn):  #função necessaria para a resposta do cliente, pois ao finalizar(enter) isso é um \n
                         #alem disso é como se o servidor esperasse o comando todo chegar (ele só vai parar quando ver um \n, e seguir adiante)
    dados = b''
    while True:
        parte = conn.recv(1)
        if not parte:
            return None
        if parte == b'\n':
            break
        dados += parte
    return dados.decode()

def lista_arquivos():   #COMANDO DIR
    arquivos = []       #lista com os arquivos do servidor
    for nome in os.listdir(PASTAARQSERVER):
        caminho = os.path.realpath(os.path.join(PASTAARQSERVER, nome)) 
        if os.path.isfile(caminho):
            tamanho = os.path.getsize(caminho)      
            arquivos.append(f"{nome} ({tamanho} bytes)")
    return "\n".join(arquivos)              #adicionar na lista de arquivos




def enviar_arquivo(conn, nome_arquivo, inicio=0):
    caminho = os.path.realpath(os.path.join(PASTAARQSERVER, nome_arquivo))
    if not caminho.startswith(PASTAARQSERVER) or not os.path.isfile(caminho):           #apenas para garantir que é valido
        envia_dados(conn, b"ERRO: Arquivo nao encontrado\nFIM\n")
        return

    with open(caminho, 'rb') as f:
        f.seek(inicio)
        while True:
            dados = f.read(4096)
            if not dados:
                break
            envia_dados(conn, dados)
    envia_dados(conn, b"\nFIM\n")       #enviando um finalizador para o cliente identificar que acabou o envio







def calcular_md5(caminho, posicao=None):         
    hash_md5 = hashlib.md5()
    try:
        with open(caminho, "rb") as f:
            if posicao:
                dados = f.read(int(posicao))         #o usuario vai informar até onde ele recebeu(ate quantos bytes)
            else:
                dados = f.read()
            hash_md5.update(dados)
        return hash_md5.hexdigest()                 
    except:
        return None






def tratar_cliente(conn, addr):
    print(f"Conexão de {addr}")
    envia_dados(conn, b"Bem-vindo ao servidor de arquivos!\n")
    try:
        while True:
            linha = recebe_linha(conn)    #o separador de linha
            if not linha:
                break
            partes = linha.strip().split() #as partes são uma variavel auxiliar para separar o COMANDO dos argumentos do comando         

            if not partes:
                continue

            cmd = partes[0] 

            if cmd == 'DIR':
                resposta = lista_arquivos() + "\nFIM\n"   #sempre usando o "\nFIM\n" para identificar o fim da mensagem
                envia_dados(conn, resposta.encode())

            elif cmd == 'DOW' and len(partes) == 2:     #como o comando dow precisa do dow e de um arquivo são 2 partes
                enviar_arquivo(conn, partes[1])

            elif cmd == 'MD5' and len(partes) == 3:  #como o comando MD5 precisa do dow,de um arquivo, e de quantos bytes o usuario tem são 3 partes
                nome = partes[1]
                posicao = int(partes[2])
                caminho = os.path.realpath(os.path.join(PASTAARQSERVER, nome))
                if not caminho.startswith(PASTAARQSERVER):
                    envia_dados(conn, b"ERRO,DIRETORIO NAO ENCONTRADO\n")
                else:
                    hash_md5 = calcular_md5(caminho, posicao)
                    if hash_md5:
                        envia_dados(conn, f"MD5 {hash_md5}\n".encode())
                    else:
                        envia_dados(conn, b"ERRO, HASH NAO ENCONTRADO\n")

            elif cmd == 'DRA' and len(partes) == 4: #parte 1: comando parte 2: arquivo parte 3: ate onde recebeu parte 4: hash
                nome, pos, hash_cliente = partes[1], int(partes[2]), partes[3]
                caminho = os.path.realpath(os.path.join(PASTAARQSERVER, nome))
                if not caminho.startswith(PASTAARQSERVER) or not os.path.isfile(caminho):
                    envia_dados(conn, b"ERRO\n")
                    continue
                hash_servidor = calcular_md5(caminho, pos)
                if hash_servidor == hash_cliente:
                    envia_dados(conn, b"CONTINUE\n")
                    enviar_arquivo(conn, nome, pos)
                else:
                    envia_dados(conn, b"ERRO\n")

            elif cmd == 'DMA' and len(partes) == 2: #comando e extensão pretendida para o download
                padrao = os.path.realpath(os.path.join(PASTAARQSERVER, partes[1]))
                lista = glob.glob(padrao)
                nomes = [os.path.basename(f) for f in lista if os.path.isfile(f)]
                if nomes:
                    resposta = "ARQUIVOS " + " ".join(nomes) + "\n"
                else:
                    resposta = "ARQUIVOS\n"
                envia_dados(conn, resposta.encode())

            else:
                envia_dados(conn, b"ERRO: Comando invalido\n")
    except Exception as e:
        print(f"Erro com {addr}: {e}")
    finally:
        conn.close()
        print(f"[-] Conexão encerrada: {addr}")

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"[+] Servidor ouvindo em {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=tratar_cliente, args=(conn, addr)).start()


main()
