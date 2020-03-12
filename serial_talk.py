import serial
import queue
import time
import memoryParse

COMPORT = "COM7"
serialPort = COMPORT
baudRate = 115200
snum_adress = "000ffff6"
date_adress = "000fffee"
maxi_adress = "000fffe6"

def read_serial():


    ser = serial.Serial(serialPort , baudRate, timeout=1, writeTimeout=0) #ensure non-blocking
    q = queue.LifoQueue(maxsize=25)
    q.put("getid,1#")
    q.put("getid,2#")
    q.put("getid,3#")
    q.put("rd,1,0x000FFFF6#")
    q.put("rd,2,0x000FFFF6#")
    q.put("rd,3,0x000FFFF6#")
    q.put("rd,3,0x000FFFEE#")
    q.put("rd,3,0x000FFFE6#")
    q.put("status2,3#")
    q.put("status1,3#")
    q.put("testread,3#") 
    q.put("debug#")

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
                    try:
                        if int(parsed[5],16) == int(snum_adress,16):
                            apt['snum AM'] = int(parsed[2],16)
                    except IndexError:
                        pass
                if not "VMDPE" in data_r:
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

    ser = serial.Serial(serialPort , baudRate, timeout=1, writeTimeout=0) #ensure non-blocking
    q = queue.LifoQueue(maxsize=45)
    """
        apt = {"snum MCU":"",
            "snum APTx":"",
            "snum AM":"",
            "maximum AM":0,
            "curent AM":0,
            "init done":True,
            "date": int(time.time())}
    """
    q.put("!!!WRITE COMPLETE!!!#")
    q.put("snum,1,{}#".format(apt_struct["snum MCU"]))
    q.put("snum,2,{}#".format(apt_struct["snum APTx"]))
    q.put("snum,3,{}#".format(apt_struct["snum AM"]))
    q.put("maxi,3,{}#".format(apt_struct["maximum AM"]))
    q.put("date,3,{}#".format(apt_struct["date"]))
    if apt_struct["init done"]:
        q.put("initdone?#")
        q.put("initdone!#")
        q.put("initdone!#")
    if erase:
        for j in range(10):
            q.put("NOP#")
        q.put("nuke,3#")

    q.put("set registers readonly#")
    q.put("status2,3#")
    q.put("status1,3#")
    q.put("statusw,3,8001#")
    q.put("clear registers#")
    q.put("status2,3#")
    q.put("status1,3#")
    q.put("statusw,3,0000#")
    q.put("status2,3#")
    q.put("status1,3#")
    q.put("debug#")

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
                if not "VMDPE" in data_r:
                    print(data_r)
            except UnicodeDecodeError:
                print(data)
        if q.empty() and  (time.time() - recent_milis > timeout):
            break
        # print(time.time() - int(recent_milis))
    ser.close()

def read_all_mem():
    ser = serial.Serial(serialPort , baudRate, timeout=1, writeTimeout=0) #ensure non-blocking
    q = queue.LifoQueue(maxsize=2) 
    q.put("dump#")
    q.put("debug#")

    recent_milis = int(time.time())
    timeout = 1
    f = open("memory.txt", "w")
    try:
        while True:
            data = ser.readline()[:-2] #the last bit gets rid of the new-line chars

            if data:
                try:
                    data_r = data.decode('ascii')
                    if data_r.startswith('0x'):
                        f.write(data_r)
                        f.write('\n')
                    if not "VMDPE" in data_r:
                        print(data_r)
                except UnicodeDecodeError:
                    print(data)
            elif not q.empty() and (time.time() - recent_milis > timeout):
                send_data = q.get()
                print(send_data)
                ser.write(send_data.encode('ascii'))
                recent_milis = int(time.time())
            elif q.empty() and  (time.time() - recent_milis > 1200000):
                break
            # print(time.time() - int(recent_milis))
        ser.close()
        f.close()
        memoryParse.translate_tobin()
    except KeyboardInterrupt:
        f.close()
        memoryParse.translate_tobin()

def find_offset():
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
    q.put("!!!READ COMPLETE!!!#")
    q.put("find,3,2#")
    q.put("debug#")


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
                    # "FIND %d %lu time offset %d"
                    print("{} is {}".format(parsed[1],parsed[5]))
                    offset[parsed[1]] = parsed[5]
                if not "VMDPE" in data_r:
                    print(data_r)
            except UnicodeDecodeError:
                print(data)
        if q.empty() and  (time.time() - recent_milis > timeout):
            print(offset)
            ser.close()
            return int(int(offset["2"])/8)

if __name__ == "__main__":
    print(read_serial())