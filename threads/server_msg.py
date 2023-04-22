import socket, threading, json, datetime,\
    functions.other as other,\
    functions.encryption as encryption,\
    functions.conection as con

# Este servidor se encarga de recibir mensajes de los clientes, procesarlos y enviarlos 
# al cliente destino. Usa técnicas de encriptación mixta para garantizar la máxima seguridad 
# en los intercambios. Las funciones de encriptación explicadas en detalle están en /functions/encryption.py

class MSGServer(threading.Thread):
    def __init__(self, root):
        threading.Thread.__init__(self)
        self.ip = other.get_private_ip()
        self.root = root

    def run(self):
        server_msg_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_msg_socket.bind((self.ip, 6002))
        server_msg_socket.listen(999)

        while True:
            server, addr = server_msg_socket.accept()
            raw = server.recv(4096)
            raw = raw.split(b"\n\n\n")
            packet = encryption.decrypt_message(raw[0], f"{self.root}private.key", raw[1])
            packet = json.loads(packet)
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            if packet["idReceiver"] == "server":
                RPacket = {
                        "type": "con_test",
                        "status": "ok"
                    }
                server.sendall(json.dumps(RPacket).encode())

            else:
                conv_id = other.get_conv_id(packet["idSender"], packet["idReceiver"], f"{self.root}.db")
                other.execute_db_command(
                    f"{self.root}.db",
                    "INSERT INTO messages VALUES (?,?,?,?,?,?)",
                    (packet["idMessage"], conv_id, packet["idSender"], packet["idReceiver"], packet["content"], packet["time"])
                )
                select = other.execute_db_command(
                    f"{self.root}.db",
                    "SELECT ip FROM users WHERE id = ? AND status = 'online'",
                    (packet["idReceiver"],)
                )
                result = select.fetchall()
                
                if len(result):
                    try:
                        con.send_message(
                            ip = result[0][0],
                            port = 6001,
                            idMessage = packet["idMessage"],
                            idSender = packet["idSender"],
                            idReceiver = packet["idReceiver"],
                            content = packet["content"],
                            time = packet["time"],
                            key_file = f"{self.root}client_keys/{packet['idReceiver']}.key"
                        )
                        print(f"{now} {addr[0]} to {result[0][0]}: Message sended")
                    
                    except:
                        other.execute_db_command(
                            f"{self.root}",
                            "INSERT INTO waiting VALUES (?,?)",
                            (packet["idMessage"], packet["idReceiver"])
                        )
                        other.execute_db_command(
                            f"{self.root}",
                            "UPDATE users SET status='disconnected' WHERE id=?",
                            (packet["idReceiver"])
                        )
                        print(f"{now} {addr[0]} to {result[0][0]}: Client {result[0][0]} disconnected. Message in queue.")
                
                else:
                    other.execute_db_command(
                            f"{self.root}",
                            "INSERT INTO waiting VALUES (?,?)",
                            (packet["idMessage"], packet["idReceiver"])
                        )
                    other.execute_db_command(
                        f"{self.root}",
                        "UPDATE users SET status='disconnected' WHERE id=?",
                        (packet["idReceiver"])
                    )
                    print(f"{now} {addr[0]} to {result[0][0]}: Client {result[0][0]} disconnected. Message in queue.")

            server.close()