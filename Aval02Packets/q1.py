import sys 
import struct


#não consegui lembrar uma forma de formatar propriamente o endereço MAC, mas ele está sendo informado.

if len(sys.argv) < 2:
    print("Erro: informe o arquivo pcap.")
else:
    pcapFile = sys.argv[1]
    print("o nome do arquivo é",pcapFile)

fd = open(pcapFile, "rb")
header = fd.read(24)
contador_pacote = 0  

if header[0:4] in [ b'\xD4\xC3\xB2\xA1', b'\xD4\x3C\xB2\xA1']:
    hPacket = fd.read(16)
    
    while hPacket != b'':
        contador_pacote += 1
        (time, msec, capLen, origLen) = struct.unpack("<IIII", hPacket)
        pacote = fd.read(capLen)
        print("Pacote numero: ", contador_pacote)
        if pacote[12:14] == b'\x08\x06':
            
            arpType = pacote[20:22]
            if arpType == b'\x00\x01':       #se for arp 00 01 é solicitação se for 00 02 é resposta
                print("Arp de solicitação (request)")
                print("MAC de origem : ",[hex(x) for x in  pacote[22:28]],"IP de origem : ",[x for x in pacote[28:32]])
                print("MAC de destino : ",[hex(x) for x in  pacote[32:38]],"IP de destino : ", [x for x in pacote[38:42]])
            else:
                print("Arp de resposta (reply)")
                print("MAC de origem : ",[hex(x) for x in pacote[22:28]],"IP de origem : ",[x for x in pacote[28:32]])
                print("MAC de destino : ",[hex(x) for x in pacote[32:38]],"IP de destino : ", [x for x in pacote[38:42]])
        
        if pacote [12:14] == b'\x08\x00': #se for ipv4
            
            #os 4 campos escolhidos para exibição:
            print("Pacote IPV4")
            print("IP de origem : ",[x for x in pacote[26:30]],"IP de destino : ",[x for x in pacote[30:34]])
            print("Total length:",struct.unpack('>H',pacote[16:18])[0])
            print("Identification:",struct.unpack('>H', pacote[18:20])[0])
            print("Time to live", pacote[22])
            print("Protocol:",pacote[23])
            
            
            if pacote [23] == 1: 
                print("É um ICMP")       #se for icmp
                if pacote [34] == 8:
                    typeICMP = "Echo request"
                    print("o identificador é:",[x for x in pacote[38:40]],"o numero de sequencia é: ",[x for x in pacote[40:42]])
                if pacote [34] == 0:
                    typeICMP = "Echo reply"
                    print("o identificador é:",[x for x in pacote[38:40]],"o numero de sequencia é: ",[x for x in pacote[40:42]])
                if pacote [34] == 3:
                    typeICMP = "Port is unreachable"
                if pacote [34] == 5:
                    typeICMP = "Redirect"
                if pacote [34] == 11:
                    typeICMP = "time exceed"
            if pacote [23] == 17:
                print("É um UDP, com a porta de origem:",struct.unpack('>H',pacote[34:36])[0],"e a porta de destino:",struct.unpack('>H',pacote[36:38])[0])
            if pacote [23] == 6:
                print("É um TCP, com a porta de origem:",struct.unpack('>H',pacote[34:36])[0],"e a porta de destino:",struct.unpack('>H',pacote[36:38])[0])
                print("flags:",[x for x in pacote[46:48]],"checksum:",[x for x in  pacote[50:52]],"window:",[x for x in pacote[48:50]],"sequence number:",[x for x in pacote[38:42]])
           
        hPacket = fd.read(16)            
        