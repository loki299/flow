import socket, threading, json, websocket,\
    functions.other as other,\
    functions.encryption as encryption,\
    functions.conection as con

class MSGClient(threading.Thread):
    def __init__(self, root):
        threading.Thread.__init__(self)
        self.ip = other.get_private_ip()
        self.root = root

    def run(self):
        server_msg_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_msg_socket.bind((self.ip, 6001))
        server_msg_socket.listen(999)

        while True:
            server, addr = server_msg_socket.accept()
            raw = server.recv(4096)
            raw = raw.split(b"\n\n\n")
            packet = encryption.decrypt_message(raw[0], f"{self.root}private.key", raw[1])
            packet = json.loads(packet)

            select = other.execute_db_command(
                f"{self.root}.db",
                "SELECT name FROM conversations WHERE id = ?",
                (packet["idConv"],)
            )
            try:
                convName = select.fetchall[0][0]
            except:
                convName = con.get_ip(packet["idSender"], addr[0])
                other.execute_db_command(
                    f"{self.root}.db",
                    "INSERT INTO conversations VALUES (?,?,?,?,?)",
                    (packet["idConv"], f'{packet["idSender"]},{packet["idReceiver"]}', convName, packet["content"], packet["time"])
                )

            other.execute_db_command(
                f"{self.root}.db",
                "INSERT INTO messages VALUES (?,?,?,?,?,?)",
                (packet["idMessage"], packet["idConv"], packet["idSender"], packet["idReceiver"], packet["content"], packet["time"])
            )

            other.execute_db_command(
                f"{self.root}.db",
                "UPDATE conversations SET lastMsg = ?, lastMsgTime = ? WHERE id = ?",
                (packet["content"], packet["time"], packet["idConv"])
            )
            

            ws = websocket.WebSocket()
            ws.connect(f"ws://{self.ip}:6004")
            ws.send("/n/n".join([packet["idSender"], packet["idReceiver"], packet["content"], packet["time"], packet["idConv"], convName]))
            ws.close()

            RPacket = {
                "status": "ok"
            }
            RPacket = json.dumps(RPacket)
            server.sendall(bytes(RPacket, "utf-8"))
            server.close()