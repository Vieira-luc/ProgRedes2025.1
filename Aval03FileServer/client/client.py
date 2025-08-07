import socket
import os

HOST = '127.0.0.1'
PORT = 57432
TAM_LEITURA = 4096
PASTAARQCLIENTE = os.path.realpath("arquivos") #para o usuario não acessar uma pasta indevida

def envia_dados(sock, dados: bytes):
    total_enviado = 0
    while total_enviado < len(dados):
        enviado = sock.send(dados[total_enviado:])
        if enviado == 0:
            raise RuntimeError("ERRO, NENHUM DADO ENVIADO")
        total_enviado += enviado

def recebe_linha(sock):     #para identificar a quebra de linhas
    dados = b''
    while True:
        parte = sock.recv(1)
        if not parte:
            return None
        if parte == b'\n':
            break
        dados += parte
    return dados.decode()

def receber_ate_fim(sock): #para saber até onde vai o fim da mensagem 
    dados = b''
    while True:
        parte = sock.recv(TAM_LEITURA)
        if not parte:
            break
        dados += parte
        if b'\nFIM\n' in dados:
            dados = dados.replace(b'\nFIM\n', b'')
            break
    return dados

def lista_arquivos(sock):       #ENVIO DO COMANDO DIR E RESPOSTA
    envia_dados(sock, b'DIR\n')
    resposta = receber_ate_fim(sock)
    print("Arquivos disponíveis:\n" + resposta.decode())

def download_arquivo(sock, nome_arquivo): #ENVIO DO COMANDO DOW E RESPOSTA
    comando = f"DOW {nome_arquivo}\n".encode()
    envia_dados(sock, comando)

    caminho = os.path.join(PASTAARQCLIENTE, nome_arquivo)

    with open(caminho, 'wb') as f:
        while True:
            dados = sock.recv(TAM_LEITURA)
            if not dados:
                print("Conexão fechada inesperadamente")            #se não houver dados
                break
            if b'\nFIM\n' in dados:  
                dados = dados.replace(b'\nFIM\n', b'')
                f.write(dados)
                break
            f.write(dados)

    print(f"Arquivo '{nome_arquivo}' baixado com sucesso.")         #download concluido

def obter_md5(sock, nome_arquivo, posicao):
    envia_dados(sock, f"MD5 {nome_arquivo} {posicao}\n".encode())
    resposta = recebe_linha(sock)
    if resposta and resposta.startswith("MD5 "):
        print(f"MD5 parcial: {resposta[4:]}")       #hash de ate onde foi o BYTE recebido
        return resposta[4:]
    else:
        print("Erro ao obter MD5.")
        return None

def continuar_download(sock, nome, posicao, hash_parcial):      #para continuar o download apartir dos parametros concedidos
    envia_dados(sock, f"DRA {nome} {posicao} {hash_parcial}\n".encode())
    resposta = recebe_linha(sock)
    if resposta == "CONTINUE":
        caminho = os.path.join(PASTAARQCLIENTE, nome)
        with open(caminho, 'ab') as f:
            while True:
                dados = sock.recv(TAM_LEITURA)
                if not dados:
                    break
                if b'\nFIM\n' in dados:
                    dados = dados.replace(b'\nFIM\n', b'')
                    f.write(dados)
                    break
                f.write(dados)
        print("Download continuado com sucesso.")
    else:
        print("Erro ao continuar download.")

def download_multiplo(sock, mascara):
    envia_dados(sock, f"DMA {mascara}\n".encode())
    resposta = recebe_linha(sock)
    if resposta.startswith("ARQUIVOS "):
        arquivos = resposta[8:].split()
        for nome in arquivos:
            caminho = os.path.join(PASTAARQCLIENTE, nome)
            if os.path.exists(caminho):
                sobrescrever = input(f"O arquivo '{nome}' já existe. Sobrescrever? (s/n): ").lower() #para a resposta em minuscula
                if sobrescrever != 's':
                    continue
            download_arquivo(sock, nome)
    else:
        print("Nenhum arquivo encontrado.")

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.connect((HOST, PORT))
        except ConnectionRefusedError:          #se a conexão falhar
            print("Erro: servidor não está ativo.")
            return

        print(recebe_linha(sock))  #boas-vindas do servidor

        while True:
            print("\nComandos:")
            print("1 - DIR")
            print("2 - DOW <arquivo>")
            print("3 - MD5 <arquivo> <posição>")
            print("4 - DRA <arquivo> <posição> <hash>")
            print("5 - DMA <máscara>")
            print("0 - Sair")

            entrada = input("Digite o comando: ").strip()
            if entrada == '1':
                lista_arquivos(sock)
            elif entrada.startswith('2 '):
                _, nome = entrada.split(' ', 1)
                download_arquivo(sock, nome)
            elif entrada.startswith('3 '):
                _, nome, limite = entrada.split()
                obter_md5(sock, nome, int(limite))
            elif entrada.startswith('4 '):
                _, nome, pos, hashp = entrada.split()
                continuar_download(sock, nome, int(pos), hashp)
            elif entrada.startswith('5 '):
                _, mascara = entrada.split(' ', 1)
                download_multiplo(sock, mascara)
            elif entrada == '0':
                break
            else:
                print("Comando inválido.")

if __name__ == "__main__":
    main()
