from thread import Thread
import time
import serial

FORWARD = 1
BACKWARD = 0

class SyringeChannel:

    def __init__(self, main, channel_number):
        self.main = main
        self.channel_number = channel_number

    def jog(self, direction):

        command = "<RUN,DIST,1,0,F,8000.0,8000.0,8000.0>"
        print("Would run: " + command)

        thread = Thread(self.runTest, [command])
        thread.finished.connect(lambda: self.thread_finished(thread))
        thread.start()

    def thread_finished(self, th):
        th.stop()