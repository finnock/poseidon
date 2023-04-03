import serial
import time


class CannotConnectException(Exception):
    pass


class Arduino:
    def __init__(self):
        self.port = None
        self.serial = None
        self.connected = False

    # Connect to the Arduino Board
    def connect(self):
        try:
            port_declared = self.port in vars()
            try:
                self.serial = serial.Serial()
                self.serial.port = self.port
                self.serial.baudrate = 230400
                self.serial.parity = serial.PARITY_NONE
                self.serial.stopbits = serial.STOPBITS_ONE
                self.serial.bytesize = serial.EIGHTBITS
                self.serial.timeout = 1
                self.serial.open()

                # This is a thread that always runs and listens to commands from the Arduino
                # TODO: figure out how this is usable! Sounds good!
                #self.global_listener_thread = Thread(self.listening)
                #self.global_listener_thread.finished.connect(lambda:self.self.thread_finished(self.global_listener_thread))
                #self.global_listener_thread.start()


                # TODO: figure out if 3s is necessary
                # TODO: possible thread?
                time.sleep(3)

                self.connected = True
            except:
                self.connected = False
                raise CannotConnectException
        except AttributeError:
            self.connected = False

    # Disconnect from the Arduino board
    # TODO: figure out how to handle error.. (which error?)
    def disconnect(self):
        print("Disconnecting from board..")
        #self.global_listener_thread.stop()
        time.sleep(3)
        self.serial.close()
        self.connected = False
        print("Board has been disconnected")

    def send_commands(self, commands):
        waiting_for_reply = False

        for command in commands:
            if not waiting_for_reply:
                self.send_to_arduino(command)
                print("Sent from PC -- " + command)
                waiting_for_reply = True

            if waiting_for_reply:
                while self.serial.inWaiting() == 0:
                    pass

                data_received = self.main.recvPositionArduino()
                print("Reply Received -- " + data_received)
                waiting_for_reply = False

            time.sleep(0.1)
        print("Send and receive complete\n\n")

    def send_to_arduino(self, command):
        self.serial.write(command.encode())
        self.serial.flushInput()
