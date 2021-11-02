import requests
import urllib.parse
import m3u8
import os
import math
import asyncio
import aiohttp
import time


url_api = "https://gql.twitch.tv/gql"

cabecera_token = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'es-ES',
            'Authorization': 'undefined',
            'Client-Id': 'kimne78kx3ncx6brgo4mv6wki5h1ko',
            'Connection': 'keep-alive',
            'Content-Length': '662',
            'Content-Type': 'text/plain;charset=UTF-8',
            'Device-Id': '0xuvWh0J2XUXQo78MMqtsAdD4xGPZ1ON',
            'Host': 'gql.twitch.tv',
            'Origin': 'https://www.twitch.tv',
            'Referer': 'https://www.twitch.tv/',
            'sec-ch-ua': '"Chromium";v="93", " Not A;Brand";v="99", "Google Chrome";v="93"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/92.0.4515.131 Safari/537.36'
            }

cabecera_m3u8 = {
            'Accept': 'application/x-mpegURL, application/vnd.apple.mpegurl, application/json, text/plain',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/92.0.4515.131 Safari/537.36'
            }

cabecera_data = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'es-ES',
            'Authorization': 'undefined',
            'Client-Id': 'kimne78kx3ncx6brgo4mv6wki5h1ko',
            'Connection': 'keep-alive',
            'Content-Length': '287',
            'Content-Type': 'text/plain;charset=UTF-8',
            'Device-Id': '0xuvWh0J2XUXQo78MMqtsAdD4xGPZ1ON',
            'Host': 'gql.twitch.tv',
            'Origin': 'https://www.twitch.tv',
            'Referer': 'https://www.twitch.tv/',
            'sec-ch-ua': '"Chromium";v="93", " Not A;Brand";v="99", "Google Chrome";v="93"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/92.0.4515.131 Safari/537.36'
            }

lst_nomSim = {
    '|': '.l.',
    '>': '.M.',
    '<': '.m.',
    '"': '.__.',
    '?':  '.!.',
    '*': '.x.',
    ':': '.-.',
    '/': '.).',
    '\\': '.(.',
    }


def solicitarToken(vodID):
    global url_api
    global cabecera_token

    bdy_token = [
        {
            'operationName':'PlaybackAccessToken_Template',
            'query': 'query PlaybackAccessToken_Template($login: String!, $isLive: Boolean!, $vodID: ID!, $isVod: '
                     'Boolean!, $playerType: String!) {  streamPlaybackAccessToken(channelName: $login, params: '
                     '{platform: \"web\", playerBackend: \"mediaplayer\", playerType: $playerType}) '
                     '@include(if: $isLive) {    value    signature    __typename  }  videoPlaybackAccessToken'
                     '(id: $vodID, params: {platform: \"web\", playerBackend: \"mediaplayer\", playerType: '
                     '$playerType}) @include(if: $isVod) {    value    signature    __typename  }}',
            'variables':{
                'isLive':False,
                'login':'',
                'isVod': True,
                'vodID': vodID,
                'playerType': 'site'
            }
        }
    ]

    respuesta_token = requests.post(url_api, json=bdy_token, headers=cabecera_token)
    contenido_token = respuesta_token.json()

    firma = contenido_token[0]['data']['videoPlaybackAccessToken']['signature']
    token = contenido_token[0]['data']['videoPlaybackAccessToken']['value']
    token_cod = urllib.parse.quote(token, safe='')

    return firma, token_cod


def obtenerReso(vodID, firma, token_cod):
    global cabecera_m3u8
    
    url_reso = 'https://usher.ttvnw.net/vod/' + vodID + '.m3u8?allow_source=true& player_backend=mediaplayer&' \
               'playlist_include_framerate=true&reassignments_supported=true&sig=' + firma + '&supported_codecs=' \
               'avc1&token=' + token_cod + '&cdm=wv&player_version=1.5.0'

    arch_reso = requests.get(url_reso, headers=cabecera_m3u8)

    m3u8_reso = m3u8.loads(arch_reso.text)

    return m3u8_reso.data['playlists'][0]['uri']


def obtenerFrag(url_frag):
    global cabecera_m3u8

    arch_frag = requests.get(url_frag, headers=cabecera_m3u8)

    m3u8_frag = m3u8.loads(arch_frag.text)

    return m3u8_frag.data['segments']


def obtenerJSON(vodID):
    global url_api
    global cabecera_data
    
    bdy_data = [
        {
            'operationName':'ComscoreStreamingQuery',
            'variables':{
                'channel':'',
                'clipSlug':'',
                'isClip': False,
		'isLive': False,
		'isVodOrCollection':  True,
                'vodID': vodID,
            },
	    'extensions': {
		    'persistedQuery': {
			    'version': 1,
			    'sha256Hash': 'e1edae8122517d013405f237ffcc124515dc6ded82480a88daef69c83b53ac01'
			}
		}
        }
    ]

    respuesta_data = requests.post(url_api, json=bdy_data, headers=cabecera_data)
    data = respuesta_data.json()

    return data[0]['data']['video']


async def descargarFrag(session, url, i):
    async with session.get(url, timeout=1000) as respuesta:
        if respuesta.status == 200:
            contenido = await respuesta.content.read()
            with open("./ts/" + str(i) + ".ts", "wb") as fragmento:
                fragmento.write(contenido)
        else:
            os.system("echo URL: " + url)
            os.system("echo status: " + str(respuesta.status))


async def realizarTareas(url_ts, lista_frag):
    async with aiohttp.ClientSession() as session:
        tareas = [descargarFrag(session, url_ts + item['uri'], i) for i, item in enumerate(lista_frag)]
        await asyncio.gather(*tareas)


def crearTxtProp(dir_vid):
    lista_arch = os.listdir(dir_vid)
    nom_vid = lista_arch[0]
    segnd_creac = os.path.getctime(dir_vid + "/" + nom_vid)
    fech_creac = time.ctime(segnd_creac)
    segnd_modi = os.path.getmtime(dir_vid + "/" + nom_vid)
    fech_modi = time.ctime(segnd_modi)
    segnd_accs = os.path.getatime(dir_vid + "/" + nom_vid)
    fech_accs = time.ctime(segnd_accs)

    with open(dir_vid + "/atrib.txt", "w", encoding = 'utf-8') as archivo:
        archivo.write("nomvid=" + nom_vid + "\n")
        archivo.write("screac=" + str(segnd_creac) + "\n")
        archivo.write("smodi=" + str(segnd_modi) + "\n")
        archivo.write("saccs=" + str(segnd_accs) + "\n\n")
        archivo.write("======================================================\n")
        archivo.write("Nombre: " + nom_vid + "\n\n")
        archivo.write("Fecha de Creacion: " + fech_creac + "\n")
        archivo.write("Segundos de Creacion: " + str(segnd_creac) + "\n\n")
        archivo.write("Fecha de Modificacion: " + fech_modi + "\n")
        archivo.write("Segundos de Modificacion: " + str(segnd_modi) + "\n\n")
        archivo.write("Fecha de Acceso: " + fech_accs + "\n")
        archivo.write("Segundos de Acceso: " + str(segnd_accs) + "\n")


def main(vodID: str):
    global lst_nomSim

    dat_vid = obtenerJSON(vodID)
    
    nom_orig = dat_vid['title']
    fecha = dat_vid['createdAt'][:10]
    streamer = dat_vid['owner']['displayName']
    
    os.system("echo Nombre Original: " + nom_orig)
    nom_modf = nom_orig
    nom_strmr = streamer
    for simbolo in lst_nomSim:
        nom_modf = nom_modf.replace(simbolo, lst_nomSim[simbolo])
        nom_strmr = nom_strmr.replace(simbolo, lst_nomSim[simbolo])
    os.system("echo Nombre Modificado:  " + nom_modf)
    
    firma, token_cod = solicitarToken(vodID)
    url_frag = obtenerReso(vodID, firma, token_cod)
    lista_frag = obtenerFrag(url_frag)

    url_ts = url_frag[:len(url_frag)- url_frag[::-1].index('/')]
    os.system("echo -------------------------------------------------")
    os.system("echo URL HLS Fragmentos: " + url_frag)
    os.system("echo URL HLS Base TS: " + url_ts)

    if len(nom_modf + "_XX.ts") > 58:
        nom_vid = nom_modf[:58] + " [...]"
    else:
        nom_vid = nom_modf
    os.system("echo -------------------------------------------------")
    os.system("echo Nombre de archivo recortado: \n")
    os.system("echo " + nom_vid)
    
    os.system("echo -------------------------------------------------")
    os.system("echo Descarga de Fragmentos. Errores:")
    os.system("mkdir ts")
    asyncio.run(realizarTareas(url_ts, lista_frag))

    os.system("echo -------------------------------------------------")
    os.system("echo Union de archivos TS")
    os.system("mkdir " + nom_strmr + "_" + fecha)
    dir_vid = nom_strmr + "_" + fecha
    cont_frag = 0
    for i in range(len(lista_frag)):
        with open("./" + dir_vid + "/" + nom_vid + "_" + str(cont_frag) + ".ts", "ab") as arch_ts:
            peso_arch = os.stat("./" + dir_vid + "/" + nom_vid + "_" + str(cont_frag) + ".ts").st_size
            peso_arch = peso_arch/1024/1024/1024
            with open("./ts/" + str(i) + ".ts", "rb") as fragmento:
                peso_frag = os.stat("./ts/" + str(i) + ".ts").st_size
                peso_frag = peso_frag/1024/1024/1024
                if peso_arch + peso_frag > 1.8:
                    cont_frag += 1
                arch_ts.write(fragmento.read())
            os.remove("./ts/" + str(i) + ".ts")
    os.rmdir("ts")
    crearTxtProp("./" + dir_vid + "/")

main("1131249228")
