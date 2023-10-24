import asyncio
import websockets
import uuid
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64

def get_mac_address():
    mac_num = hex(uuid.getnode()).replace('0x', '').upper()
    mac = '-'.join(mac_num[i: i + 2] for i in range(0, 11, 2))
    return mac

async def send_mac_to_server(server_ip, server_port):
    uri = f"ws://192.168.0.0:8765"
    async with websockets.connect(uri) as websocket:
        # Enviar la dirección MAC al inicio de la conexión.
        mac_address = get_mac_address()
        print(f"Enviando {mac_address}")
        await websocket.send(mac_address)

        # Recibir los parámetros Diffie-Hellman del servidor y deserializarlos.
        parameters_bytes = await websocket.recv()
        parameters = serialization.load_pem_parameters(
            parameters_bytes,
            backend=default_backend()
        )

        # Generar una clave privada para el cliente.
        client_private_key = parameters.generate_private_key()

        # Enviar la clave pública del cliente al servidor.
        client_public_key_bytes = client_private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        await websocket.send(client_public_key_bytes)

        # Recibir la clave pública del servidor y deserializarla.
        server_public_key_bytes = await websocket.recv()
        server_public_key = serialization.load_pem_public_key(
            server_public_key_bytes,
            backend=default_backend()
        )

        # Generar la clave compartida.
        shared_key = client_private_key.exchange(server_public_key)
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=None,
        ).derive(shared_key)
        derived_key = base64.urlsafe_b64encode(derived_key)

        cipher_suite = Fernet(derived_key)

        # Implementar la lógica del chat aquí.
        while True:
            data = input("Introduce un mensaje: ")
            # Encriptar el mensaje antes de enviarlo.
            encrypted_data = cipher_suite.encrypt(data.encode())
            await websocket.send(encrypted_data)

            # Recibir y desencriptar el mensaje del servidor.
            try:
                response = await websocket.recv()
                response = cipher_suite.decrypt(response).decode()  # No necesitas usar encode() aquí
                print(f"Recibido: {response}")
            except InvalidToken:  # Usa InvalidToken directamente
                print("Error al desencriptar el mensaje.")

asyncio.run(send_mac_to_server('localhost', 8765))
