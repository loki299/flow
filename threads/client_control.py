import threading, functions.conection as con, schedule, time

# Este es el servicio que se encarga de realizar las conexiones de control cada minuto
# con el servidor. 

class ControlCon(threading.Thread):
    def __init__(self, ip, root):
        threading.Thread.__init__(self)
        self.ip = ip
        self.root = root

    def run(self):
        schedule.every(1).minutes.do(con.client_control_con, ip = self.ip, root = self.root)
        con.client_control_con(self.ip, self.root)
        while True:
            schedule.run_pending()
            time.sleep(1)