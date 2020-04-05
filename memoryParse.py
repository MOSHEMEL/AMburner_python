def translate_tobin():
    f = open('memory.txt', 'r')
    f_o = open('memory.bin', 'wb')
    for line in f:
        if line.startswith('cs['):
            pass
        else:
            for byte in line.split(' '):
                if '\n' in byte:
                    byte = byte.strip()
                try:
                    byte_r = int(byte[2:],16)
                    byte_c = bytearray.fromhex(byte[2:])
                    f_o.write(byte_c)
                except Exception as inst:
                    print(type(inst))     # the exception instance
                    print(inst.args)      # arguments stored in .args
                    print(inst)           # __str__ allows args to be printed directly
if __name__ == "__main__":
    translate_tobin()