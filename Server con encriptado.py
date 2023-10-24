import asyncio
import websockets
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
import base64

connected = set()

# Lista de direcciones MAC permitidas
allowed_mac_addresses = ["00-00-00-00-00-00", "00:0a:95:9d:68:17"]  # Añade tus direcciones MAC aquí

# Generar los parámetros Diffie-Hellman
parameters = dh.generate_parameters(generator=2, key_size=512)

# Serializar los parámetros a bytes
parameters_bytes = parameters.parameter_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.ParameterFormat.PKCS3
)

async def server(websocket, path):
    connected.add(websocket)
    try:
        # Recibir la dirección MAC al inicio de la conexión
        mac_address = await websocket.recv()
        print(f"Recibido: {mac_address}")

        # Verificar la dirección MAC valida
        if mac_address in allowed_mac_addresses:
            await websocket.send(parameters_bytes)  # Enviar los parámetros Diffie-Hellman al cliente

            # Recibir la clave pública del cliente y deserializarla
            client_public_key_bytes = await websocket.recv()
            client_public_key = serialization.load_pem_public_key(
                client_public_key_bytes,
                backend=default_backend()
            )

            # Generar una clave privada para el servidor con los parámetros recibidos
            server_private_key = parameters.generate_private_key()

            # Enviar la clave pública del servidor al cliente
            server_public_key_bytes = server_private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            await websocket.send(server_public_key_bytes)

            # Generar la clave compartida
            shared_key = server_private_key.exchange(client_public_key)
            derived_key = HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=None,
                info=None,
            ).derive(shared_key)
            derived_key = base64.urlsafe_b64encode(derived_key)

            cipher_suite = Fernet(derived_key)

            # Chat de texto.
            async for message in websocket:
                try:
                    message = cipher_suite.decrypt(message).decode() 
                    print(f"Recibido: {message}")
                    
                    response = input("Introduce un mensaje para enviar al cliente: ")
                    encrypted_response = cipher_suite.encrypt(response.encode())
                    await websocket.send(encrypted_response)
                    
                except InvalidToken:  # Usa InvalidToken directamente
                    print("Error al desencriptar el mensaje.")
        else:
            print(f"Dirección MAC no permitida: {mac_address}")
    finally:
        connected.remove(websocket)

start_server = websockets.serve(server, '192.168.0.0', 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
