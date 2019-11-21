def translate_tobin():
    f = open('memory.txt', 'r')
    f_o = open('memory.bin', 'wb')
    for line in f:
        for byte in line.split(' '):
            if '\n' in byte:
                byte = byte.strip()
            byte_r = int(byte[2:],16)
            byte_c = bytearray.fromhex(byte[2:])
            f_o.write(byte_c)

if __name__ == "__main__":
    translate_tobin()