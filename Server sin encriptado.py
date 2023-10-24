import asyncio
import websockets

async def server(websocket, path):
    mac_address = await websocket.recv()
    print(f"MAC Address recibida: {mac_address}")

    # Validar la dirección MAC
    if mac_address == "00-00-00-00-00-00":
        await websocket.send("MAC Address validada. Comenzando a enviar datos.")

        while True:
            # Recibir mensaje del cliente
            client_msg = await websocket.recv()
            print(f"Mensaje del cliente: {client_msg}")

            # Enviar mensaje al cliente
            server_msg = input("Ingrese su mensaje: ")
            await websocket.send(server_msg)
    else:
        await websocket.send("MAC Address no validada.")
start_server = websockets.serve(server, "localhost", 8765) #utilizamos la direccion ip de la raspberry pi

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
