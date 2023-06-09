import socket, threading, json, sqlite3, time, functions.other as other, datetime,\
    functions.encryption as en, functions.conection as conn

# Este servidor se encarga de procesar todos los paquetes que no son mensajes, ni tienen
# relación con ellos y, por lo tanto, pueden ir sin encriptación. Estas conexiones son:

# - Control: El cliente envía cada minuto un paquete al servidor con información de su estado.
#       Esta conexión se usa para:
#           - Confirmar que el cliente está activo. 
#           - Actualizar la IP del cliente.
#           - Comprobar si hay mensajes que no le han llegado (porque estaba desconectado o por otro motivo)
#                y si los hubiese, enviarlos.

# - Key: El cliente, en cuanto se conecta, envía un paquete con su clave pública, el servidor la guarda
#       y responde con su clave pública, garantizando en todas las conexiones que las claves de ambas partes
#       están actualizadas

# - CheckID: Cuando hay que generar un nuevo ID en el cliente, envía un paquete a este servidor, que responde
#       si el ID está disponible o no. Esto casi siempre va a decir que está disponible ya que, al usar uuid4()
#       para generar los IDs, la probabilidad de colisiones es una entre mil millones, y teniendo en cuenta que
#       cada instalación de esta aplicación es completamente independiente de otra, es prácticamente imposible
#       que se repitan. Sin embargo, como no es completamente imposible, mejor confirmar que no se repiten.

class ControlServer(threading.Thread):
    def __init__(self, root):
        threading.Thread.__init__(self)
        self.ip = other.get_private_ip()
        self.root = root

    def run(self):
        mi_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        mi_socket.bind((self.ip, 6003))
        mi_socket.listen(999)

        while True:
            conexion, addr = mi_socket.accept()
            packet = conexion.recv(4096).decode()
            packet = json.loads(packet)

            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            try:
                packetID = str(packet["id"])
            except:
                pass
            
            if packet["type"] == "key":
                try:
                    with open(f'{self.root}client_keys/{packetID}.key', 'w') as file:
                        file.write(packet["key"])

                    with open(f'{self.root}public.key') as file:
                        public = file.read()
                        
                    RPacket = {
                        "type": "key",
                        "id": "server",
                        "key": public
                    }
                    
                except Exception as e:
                    conexion.close()
                    raise e
            
            elif packet["type"] == "control":
                with sqlite3.connect(f"{self.root}.db") as con:
                    try:
                        select = con.execute("SELECT id FROM users WHERE id=?", (packetID,))
                        result = select.fetchall()
                        
                        if len(result) == 0:
                            con.execute("INSERT INTO users VALUES (?,?,'online',?)", (packetID, addr[0], str(round(time.time() * 1000))))
                        else:
                            con.execute(
                                "UPDATE users SET ip = ?, status = 'online', lastCheck = ? WHERE id = ?",
                                (addr[0], str(round(time.time() * 1000)), packetID)
                            )

                        RPacket = {
                            "type": "control",
                            "id": "server",
                            "status": "ok"
                        }

                        select = con.execute("SELECT idMessage FROM waiting WHERE idReceiver = ?", (packetID,))
                        result = select.fetchall()
                        if result:
                            for message in result:
                                MSelect = con.execute("SELECT * FROM messages WHERE id = ?", (message[0],))
                                MResult = MSelect.fetchall()
                                print(f"Sending message {MResult[0][0]} from waiting to {addr[0]}")
                                conn.send_message(
                                    ip = addr[0],
                                    port = 6001,
                                    idMessage = MResult[0][0],
                                    idConv = MResult[0][1],
                                    idSender = MResult[0][2],
                                    idReceiver = MResult[0][3],
                                    content = MResult[0][4],
                                    MTime = MResult[0][5],
                                    key_file = f'{self.root}client_keys/{packetID}.key'
                                )
                        
                            con.execute("DELETE FROM waiting WHERE idReceiver = ?", (packetID,))
                        print(f"{now} {addr[0]}: Control conection correct")
                        
                    except Exception as e:
                        con.close()
                        conexion.close()
                        raise e

            elif packet["type"] == "checkID":
                with sqlite3.connect(f"{self.root}.db") as con:
                    try:
                        select = con.execute(f"SELECT id FROM {str(packet['table'])} WHERE id = ?", (packet["idToCheck"],))
                        result = select.fetchall()
                        if len(result) == 0:
                            RPacket = {
                                "id": "server",
                                "available": True
                            }
                        else:
                            RPacket = {
                                "id": "server",
                                "available": False
                            }

                    except Exception as e:
                        con.close()
                        conexion.close()
                        raise e
                    
            elif packet["type"] == "checkIP":
                select = other.execute_db_command(
                    f"{self.root}.db",
                    "SELECT id FROM users WHERE ip = ?",
                    (packet["ipToCheck"],)
                )
                result = select.fetchall()
                if result: RPacket = {"id": result[0][0]}
                else: RPacket = {"id": "0"}

            elif packet["type"] == "getIP":
                select = other.execute_db_command(
                    f"{self.root}.db",
                    "SELECT ip FROM users WHERE id = ?",
                    (packet["id"],)
                )
                result = select.fetchall()
                if result: RPacket = {"ip": result[0][0]}
                else: RPacket = {"ip": "0"}

            elif packet["type"] == "getConvID":
                print(packet)
                id = other.get_conv_id(packet["idSender"], packet["idReceiver"], f"{self.root}.db")
                RPacket = {"id": id}

            RPacket = json.dumps(RPacket)
            conexion.sendall(bytes(RPacket, "utf-8"))
            conexion.close()