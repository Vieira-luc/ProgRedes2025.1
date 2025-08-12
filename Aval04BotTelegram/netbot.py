import socket, ssl, json, time
import subprocess 

TOKEN = "8392493604:AAHJNH20fPkLH-gAuIqbSnX8O7OrJn3xUoY" 
HOST  = "api.telegram.org"
PORT  = 443


def conn_to():
    sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_tcp.settimeout(15) 
    sock_tcp.connect((HOST, PORT))
    
    purpose = ssl.Purpose.SERVER_AUTH
    context = ssl.create_default_context(purpose)
    return context.wrap_socket(sock_tcp, server_hostname=HOST)

def send_get (sock_tcp, cmd):
    resource = "/bot"+TOKEN+"/"+cmd
    sock_tcp.send (("GET "+resource+" HTTP/1.1\r\n"+
                   "Host: "+HOST+"\r\n"+
                   "\r\n").encode("utf-8"))
        
def get_response(sock_tcp):
    try:
        response_raw = b"".join(iter(lambda: sock_tcp.recv(4096), b""))
        header_body = response_raw.split(b"\r\n\r\n", 1)
        if len(header_body) < 2: return (None, None, None)
        
        headers, body = header_body[0].decode().split("\r\n"), header_body[1]
        status_line = headers[0]
        if status_line.split()[1] == "200":
            if body:
                return (status_line, headers[1:], json.loads(body.decode()))
    except Exception as e:
        print(f"Erro em get_response: {e}")
    return (None, None, None)

def get_updates(offset = 0):
    sock_tcp = None
    try:
        sock_tcp = conn_to()
        send_get(sock_tcp, f"getUpdates?offset={offset}&timeout=20")
        status_line, headers, body = get_response(sock_tcp)
        if body and "result" in body:
            return body["result"]
    except Exception as e:
        print(f"Erro em get_updates: {e}")
    finally:
        if sock_tcp:
            sock_tcp.close()
    return []

def show_update(update):
    print (f"Processando ID {update['update_id']}: {update['message']['chat']['first_name']} -> {update['message']['text']}")

def handle_arp():
    #/arp para mostrat a tabela arp
    output = subprocess.check_output("arp -a", shell=True).decode('cp1252', errors='ignore')
    return f"Tabela ARP do Sistema:\n{output}"

def handle_traceroute(host):
    #para traçar uma rota ate um destino especificado
    if not host: return "Uso: /traceroute <host>"
    try:
        output = subprocess.check_output(f"tracert -4 {host}", shell=True, timeout=90).decode('cp1252', errors='ignore')
        return f"Resultado do Traceroute (IPv4) para {host}:\n{output}"
    except subprocess.TimeoutExpired:
        return "ERRO: O comando traceroute demorou mais de 90 segundos para responder."
    except Exception as e:
        return f"ERRO ao executar traceroute: {e}"

def handle_netstat():
    #para exibir portas ativas e conexoes
    output = subprocess.check_output("netstat -an", shell=True).decode('cp1252', errors='ignore')
    filtered_output = "\n".join([line for line in output.splitlines() if "ESTABLISHED" in line or "LISTENING" in line or "Proto" in line])
    return f"Conexoes Ativas e Portas em Escuta:\n{filtered_output}"

def handle_ping(host):
    #ping para um host especifico 
    if not host:
        return "Uso: /ping <host>\nExemplo: /ping 8.8.8.8"
    try:
        output_ping = subprocess.check_output(f"ping -4 {host}", shell=True).decode('cp1252', errors='ignore')
        return f"Resultado do Ping (IPv4) para {host}:\n\n{output_ping}"
    except Exception as e:
        return f"Ocorreu um erro ao executar o comando ping para {host}: {e}"

def handle_dns():
    #para exibir os servidores dns
    output = subprocess.check_output("ipconfig /all", shell=True).decode('cp1252', errors='ignore')
    dns_servers = [line.split(":")[-1].strip() for line in output.splitlines() if "servidores dns" in line.lower()]
    if not dns_servers: return "Nenhum servidor DNS encontrado."
    return "Servidores DNS:\n" + "\n".join(dns_servers)

def handle_scan(host):
   #/scan e o host para escanear as portas comuns que estão disponiveis
    if not host: return "Uso: /scan <host>"
    ports = [21, 22, 25, 53, 80, 110, 443, 3306, 3389, 8080]
    open_ports = []
    for port in ports:
        try:
            test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_sock.settimeout(0.5)
            test_sock.connect((host, port))
            test_sock.close()
            open_ports.append(str(port))
        except Exception: pass
    if not open_ports: return f"Nenhuma porta comum encontrada aberta em {host}."
    return f"Portas Abertas em {host}:\n" + ", ".join(open_ports)

def get_help_and_menu():
    #menu para o usuario final
    help_text = (
        "*Bot de Análise de Rede Windows*\n\n"
        "Comandos disponíveis:\n"
        "*/ping <host>* - Testa a latência para um host.\n"
        "*/dns* - Exibe os servidores DNS.\n"
        "*/arp* - Mostra a tabela ARP.\n"
        "*/netstat* - Exibe conexões e portas ativas.\n"
        "*/traceroute <host>* - Traça a rota até um destino.\n"
        "*/scan <host>* - Escaneia portas comuns."
    )
    menu_layout = {
        "keyboard": [
            ["/ping", "/dns"],
            ["/arp", "/netstat"],
            ["/traceroute", "/scan"]
        ],
        "resize_keyboard": True
    }
    return help_text, menu_layout

def answer_update(update):
    
    sock_tcp = None
    try:
        sock_tcp = conn_to()
        chat_id  = update["message"]["chat"]["id"]
        text = update["message"]["text"].strip()
        parts = text.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else None
        
        answer = ""
        menu_to_send = None

        if command in ["/start", "/help"]:
            answer, menu_to_send = get_help_and_menu()
        elif command == "/ping":
            answer = handle_ping(args)
        elif command == "/dns":
            answer = handle_dns()
        elif command == "/arp":
            answer = handle_arp()
        elif command == "/netstat":
            answer = handle_netstat()
        elif command == "/traceroute":
            answer = handle_traceroute(args)
        elif command == "/scan":
            answer = handle_scan(args)
        else:
            answer = "Comando nao reconhecido. Use /start para ajuda."

        payload_dict = {"chat_id": chat_id, "text": answer, "parse_mode": "Markdown"}
        if menu_to_send:
            payload_dict["reply_markup"] = menu_to_send
        response = json.dumps(payload_dict)
        
        resource = "/bot"+TOKEN+"/sendMessage"
        sock_tcp.send (("POST "+resource+" HTTP/1.1\r\n"+
                       "Host: "+HOST+"\r\n"+
                       "Content-Length: "+str(len(response))+"\r\n"+
                       "Content-Type: application/json\r\n"
                       "\r\n").encode("utf-8"))
        sock_tcp.send (response.encode("utf-8"))
        get_response(sock_tcp)
    except Exception as e:
        print(f"Erro em answer_update: {e}")
    finally:
        if sock_tcp:
            sock_tcp.close()

def main():

    print("Limpando a fila de mensagens antigas...")
    updates = get_updates(-1)
    
    if updates:
        last_update_id = updates[-1]['update_id']
        print(f"Fila limpa. Iniciando a partir do ID: {last_update_id}")
    else:
        last_update_id = 0
        print("Fila já estava limpa.")
    
    print ("Aceitando updates...")
    
    while True:
        try:
            updates = get_updates(last_update_id + 1)
            
            if updates:
                for update in updates:
                    last_update_id = update['update_id']
                    
                    show_update(update)
                    answer_update(update)
            else:
                print("Nenhuma mensagem nova.")
            
            print ("-------------")
            time.sleep(2)
        
        except KeyboardInterrupt:
            print("\nBot encerrado.")
            break
        except Exception as e:
            print(f"Ocorreu um erro crítico no loop principal: {e}")
            time.sleep(5)
    
main()