import serial
import queue
import time
from memoryParse import translate_tobin

def read_serial():
    serialPort = "COM7"
    baudRate = 115200
    snum_adress = "000ffff6"
    date_adress = "000fffee"
    maxi_adress = "000fffe6"

    ser = serial.Serial(serialPort , baudRate, timeout=1, writeTimeout=0) #ensure non-blocking
    q = queue.LifoQueue(maxsize=20)
    q.put("rd,1,0x000FFFF6#\r\n")
    q.put("rd,2,0x000FFFF6#\r\n")
    q.put("rd,3,0x000FFFF6#\r\n")
    q.put("rd,3,0x000FFFEE#\r\n")
    q.put("rd,3,0x000FFFE6#\r\n")
    q.put("readap#\r\n") # TODO: replace by readap
    q.put("debug#\r\n")

    recent_milis = int(time.time())
    timeout = 3
    apt = {"snum MCU":"",
            "snum APTx":"",
            "snum AM":"",
            "maximum AM":0,
            "curent AM":0,
            "init done":True,
            "date": int(time.time())}

    init_flag = False
    while True:
        data = ser.readline()[:-2] #the last bit gets rid of the new-line chars
        if not q.empty() and (time.time() - recent_milis > timeout):
            send_data = q.get()
            print(send_data)
            ser.write(send_data.encode('ascii'))
            recent_milis = int(time.time())
        if data:
            try:
                data_r = data.decode('ascii')
                if data_r.startswith('SNUM'):
                    apt['snum AM'] = int(data_r.split(' ')[1],16)
                elif data_r.startswith('DATE'):
                    apt['date'] = int(data_r.split(' ')[1])
                elif data_r.startswith('MAXI'):
                    apt['maximum AM'] = int(data_r.split(' ')[1])
                elif data_r.startswith('INIT'):
                    init_flag = (data_r.split(' ')[1] == "DONE")
                elif data_r.startswith('cs[1] read'):
                    parsed = data_r.split(' ')
                    if int(parsed[5],16) == int(snum_adress,16):
                        apt['snum MCU'] = int(parsed[2],16)
                elif data_r.startswith('cs[2] read'):
                    parsed = data_r.split(' ')
                    if int(parsed[5],16) == int(snum_adress,16):
                        apt['snum APTx'] = int(parsed[2],16)
                elif data_r.startswith('cs[3] read'):
                    parsed = data_r.split(' ')
                    if int(parsed[5],16) == int(snum_adress,16):
                        apt['snum AM'] = int(parsed[2],16)
                print(data_r)
            except UnicodeDecodeError:
                print(data)
        if q.empty() and  (time.time() - recent_milis > timeout):
            apt['init done'] = init_flag
            break
        # print(time.time() - int(recent_milis))
    ser.close()
    return apt

def write_serial(apt_struct, erase):
    serialPort = "COM7"
    baudRate = 115200
    snum_adress = "000ffff6"
    date_adress = "000fffee"
    maxi_adress = "000fffe6"
    init_adress = "000fffde"

    ser = serial.Serial(serialPort , baudRate, timeout=1, writeTimeout=0) #ensure non-blocking
    q = queue.LifoQueue(maxsize=20)
    """
        apt = {"snum MCU":"",
            "snum APTx":"",
            "snum AM":"",
            "maximum AM":0,
            "curent AM":0,
            "init done":True,
            "date": int(time.time())}
    """
    q.put("snum,1,{}#\r\n".format(apt_struct["snum MCU"]))
    q.put("snum,2,{}#\r\n".format(apt_struct["snum APTx"]))
    q.put("snum,3,{}#\r\n".format(apt_struct["snum AM"]))
    q.put("maxi,3,{}#\r\n".format(apt_struct["maximum AM"]))
    q.put("date,3,{}#\r\n".format(apt_struct["date"]))
    if apt_struct["init done"]:
        q.put("initdone,3#\r\n")
    if erase:
        q.put("nuke,3#\r\n")
    q.put("debug#\r\n")

    recent_milis = int(time.time())
    timeout = 3

    while True:
        data = ser.readline()[:-2] #the last bit gets rid of the new-line chars
        if not q.empty() and (time.time() - recent_milis > timeout):
            send_data = q.get()
            print(send_data)
            ser.write(send_data.encode('ascii'))
            recent_milis = int(time.time())
        if data:
            try:
                data_r = data.decode('ascii')
                print(data_r)
            except UnicodeDecodeError:
                print(data)
        if q.empty() and  (time.time() - recent_milis > timeout):
            break
        # print(time.time() - int(recent_milis))
    ser.close()

def read_all_mem():
    serialPort = "COM7"
    baudRate = 115200

    ser = serial.Serial(serialPort , baudRate, timeout=1, writeTimeout=0) #ensure non-blocking
    size_of_mem = int(1048576/(4*256)); # 8Mbits = 1,048,576 Bytes = 262144 sectors
    q = queue.LifoQueue(maxsize=size_of_mem+2) 
    for i in range(size_of_mem):
        q.put("scan,1,{}#\r\n".format((size_of_mem-i-1)*256)) #Last in first out last is size-1
    q.put("debug#\r\n")

    recent_milis = int(time.time())
    timeout = 3
    f = open("memory.txt", "w")
    try:
        while True:
            data = ser.readline()[:-2] #the last bit gets rid of the new-line chars
            if not q.empty() and (time.time() - recent_milis > timeout):
                send_data = q.get()
                print(send_data)
                ser.write(send_data.encode('ascii'))
                recent_milis = int(time.time())
            if data:
                try:
                    data_r = data.decode('ascii')
                    if data_r.startswith('0x'):
                        f.write(data_r)
                        f.write('\n')
                    print(data_r)
                except UnicodeDecodeError:
                    print(data)
            if q.empty() and  (time.time() - recent_milis > timeout):
                break
            # print(time.time() - int(recent_milis))
        ser.close()
        f.close()
        transtranslate_tobin()
    except KeyboardInterrupt:
        f.close()

def find_offset():
    serialPort = "COM7"
    baudRate = 115200

    ser = serial.Serial(serialPort , baudRate, timeout=1, writeTimeout=0) #ensure non-blocking
    q = queue.LifoQueue(maxsize=20)
    """
        apt = {"snum MCU":"",
            "snum APTx":"",
            "snum AM":"",
            "maximum AM":0,
            "curent AM":0,
            "init done":True,
            "date": int(time.time())}
    """
    q.put("find,3,2#\r\n")
    q.put("debug#\r\n")


    recent_milis = int(time.time())
    timeout = 3
    offset = {"1":-1, "2":-1, "3":-1}
    while True:
        data = ser.readline()[:-2] #the last bit gets rid of the new-line chars
        if not q.empty() and (time.time() - recent_milis > timeout):
            send_data = q.get()
            print(send_data)
            ser.write(send_data.encode('ascii'))
            recent_milis = int(time.time())
        if data:
            try:
                data_r = data.decode('ascii')
                if data_r.startswith("FIND "):
                    parsed = data_r.split(' ')
                    # "FIND %d %lu time offset %d\r\n"
                    print("{} is {}".format(parsed[1],parsed[5]))
                    offset[parsed[1]] = parsed[5]
                print(data_r)
            except UnicodeDecodeError:
                print(data)
        if q.empty() and  (time.time() - recent_milis > timeout):
            print(offset)
            ser.close()
            return int(int(offset["2"])/8)

if __name__ == "__main__":
    print(read_serial())