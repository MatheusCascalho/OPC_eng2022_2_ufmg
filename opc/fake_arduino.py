def gen_analog():
    v = 10
    while True:
        v *= -2
        yield v

class FakeArduino:

    def __init__(self):
        self.analog = gen_analog()
    def write_lines(self, data):
        print(f"FAKE ARDUINO: Dado escrito no arduino: {data}")
    def read_line(self):
        print("FAKE ARDUINO: Lendo dados do arduino")
        data = b"I;D1,1;D2,0;D3,1;D4,0;D5,1;"
        data += b"D6,1;D7,1;"
        data += b"A1,1;A2,3;A3,45;"
        data += f"A4,{next(self.analog)};A5,4;F".encode()
        print(f"FAKE ARDUINO: dados enviados: {data}")
        return data