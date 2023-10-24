import asyncio
import websockets
import uuid

def get_mac_address():
    mac_num = hex(uuid.getnode()).replace('0x', '').upper()
    mac = '-'.join(mac_num[i: i + 2] for i in range(0, 11, 2))
    return mac

async def client():
    uri = "ws://192.168.0.0:8765"
    async with websockets.connect(uri) as websocket:
        mac_address = get_mac_address()
        await websocket.send(mac_address)

        response = await websocket.recv()
        print(f"Respuesta del servidor: {response}")

        if response == "MAC Address validada. Comenzando a enviar datos.":
            while True:
                # Enviar mensaje al servidor
                client_msg = input("Ingrese su mensaje: ")
                await websocket.send(client_msg)

                # Recibir mensaje del servidor
                server_msg = await websocket.recv()
                print(f"Mensaje del servidor: {server_msg}")

asyncio.get_event_loop().run_until_complete(client())
