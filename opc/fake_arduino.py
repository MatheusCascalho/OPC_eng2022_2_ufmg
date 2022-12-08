def gen_analog():
    v = 10
    while True:
        v *= -1
        yield v

class FakeArduino:

    def __init__(self):
        self.analog = gen_analog()
        self.digital = [1, 0, 1, 0, 1, 1, 1]
        self.analogical = [1, 3, 45, next(self.analog), 100-next(self.analog)]
    def write_lines(self, data):
        print(f"FAKE ARDUINO: Dado escrito no arduino: {data}")
        if len(data) == 1:
            data = data[0].decode()
            position = int(data[2:4])
            value = int(data[4:-1])
            if 'SD' in data:
                self.digital[position] = value
            else:
                position -= 7
                self.analogical[position] = value

    def read_line(self):
        print("FAKE ARDUINO: Lendo dados do arduino")
        data = f"I;D1,{self.digital[0]};D2,{self.digital[1]};D3,{self.digital[2]};D4,{self.digital[3]};D5,{self.digital[4]};"
        data += f"D6,{self.digital[5]};D7,{self.digital[6]};"
        data += f"A1,{self.analogical[0]};A2,{self.analogical[1]};A3,{self.analogical[2]};"
        data += f"A4,{next(self.analog)};A5,{self.analogical[4]};F"
        data = data.encode()
        print(f"FAKE ARDUINO: dados enviados: {data}")
        return data