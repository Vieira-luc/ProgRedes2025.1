import sys
import subprocess
import struct

if len(sys.argv) < 2:
    print("Erro, coloque 2 argumentos")

img = sys.argv[1]

dadosImg = open(sys.argv[1], 'rb').read()

Indice_saida = 2 
latitude = longitude = 0

while Indice_saida < len(dadosImg):
    if dadosImg[Indice_saida] != 0xFF:  #só para verificar se está sendo percorrido direito, pois depois do ff d8 vem o ff.
        break

    i = 2

for i in range(len(dadosImg)):
    if dadosImg[i:i+6] == b'Exif\x00\x00':
        inicio_exif = i  #se achar o inicio do quadro exif
        break 

after_exif = inicio_exif + 6

formato = '<'


pos = struct.unpack(formato + 'I', dadosImg[after_exif+4:after_exif+8])[0] 
ifd = after_exif + pos #posição para pular


num_entradas = struct.unpack(formato + 'H', dadosImg[ifd:ifd+2])[0] # para verificar o numero de blocos,


for i in range(num_entradas):
    entrada = ifd + 2 + i * 12
    tag = struct.unpack(formato + 'H', dadosImg[entrada:entrada+2])[0]
    
    if tag == 0x8825:
    
        inicio_gps = after_exif + struct.unpack(formato + 'I', dadosImg[entrada+8:entrada+12])[0]
        num_tags_gps = struct.unpack(formato + 'H', dadosImg[inicio_gps:inicio_gps+2])[0]
        gps = {} #dicionario para informação do gps

        for j in range(num_tags_gps):
            entrada_gps = inicio_gps + 2 + j * 12
            tag_gps = struct.unpack(formato + 'H', dadosImg[entrada_gps:entrada_gps+2])[0]
            tipo = struct.unpack(formato + 'H', dadosImg[entrada_gps+2:entrada_gps+4])[0]
            ponteiro_valor = dadosImg[entrada_gps+8:entrada_gps+12]

            if tipo == 5: #segundos, minutos e graus do gps
                
                pos_real = after_exif + struct.unpack(formato + 'I', ponteiro_valor)[0]
                
                valores = []
                for k in range(3):
                    n_bytes = dadosImg[pos_real + k*8 : pos_real + k*8+4]
                    d_bytes = dadosImg[pos_real + k*8+4 : pos_real + k*8+8]
                    num = struct.unpack(formato + 'I', n_bytes)[0]
                    den = struct.unpack(formato + 'I', d_bytes)[0]
                    valores.append(num / den if den != 0 else 0)
                gps[tag_gps] = valores
            
            elif tipo == 2: # String para norte sul leste e oeste
                gps[tag_gps] = ponteiro_valor.decode('ascii').strip('\x00')
        
        
        if 1 in gps and 2 in gps and 3 in gps and 4 in gps:
            lat = gps[2][0] + gps[2][1]/60 + gps[2][2]/3600
            lon = gps[4][0] + gps[4][1]/60 + gps[4][2]/3600
            if gps[1] == 'S': lat = -lat
            if gps[3] == 'W': lon = -lon
            
            print(f"Lat: {lat}, Lon: {lon}")
            url = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=16/{lat}/{lon}"
            subprocess.run(['start', url], shell=True)
            sys.exit()

print("Não foram encontrados os dados de GPS.")