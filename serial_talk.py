import serial
import queue
import time
import memoryParse
import sys
import AM_properties


def read_serial():


    ser = serial.Serial(AM_properties.serialPort , AM_properties.baudRate, timeout=1, writeTimeout=0) #ensure non-blocking
    q = queue.LifoQueue(maxsize=45)
    q.put("getid,3#")
    q.put("rd,3,0x000FFFF6#")
    q.put("Read SNUM 3#")
    q.put("rd,3,0x000FFFEE#")
    q.put("Read DATE 3#")
    q.put("rd,3,0x000FFFE6#")
    q.put("Read MAX 3#")
    q.put("status2,3#")
    q.put("status1,3#")
    q.put("testread,3#") 
    q.put("debug#")

    recent_milis = int(time.time())
    timeout = 3
    apt = {
            "snum AM":"",
            "maximum AM":0,
            "current AM":0,
            "date": int(time.time())}

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
                elif data_r.startswith('cs[3] read'):
                    parsed = data_r.split(' ')
                    try:
                        if int(parsed[4],16) == int(AM_properties.snum_adress,16):
                            apt['snum AM'] = int(parsed[2].rstrip(':'),16)
                    except IndexError:
                        pass
                    except ValueError:
                        if int(parsed[5],16) == int(AM_properties.snum_adress,16):
                            apt['snum AM'] = int(parsed[2].rstrip(':'),16)
                if not "VMDP" in data_r:
                    print(data_r)
            except UnicodeDecodeError:
                print(data)
        if q.empty() and  (time.time() - recent_milis > timeout):
            break
    ser.close()
    return apt

def write_serial(apt_struct, erase):

    ser = serial.Serial(AM_properties.serialPort , AM_properties.baudRate, timeout=1, writeTimeout=0) #ensure non-blocking
    q = queue.LifoQueue(maxsize=50)

    q.put("!!!WRITE COMPLETE!!!#")
    q.put("snum,3,{}#".format(apt_struct["snum AM"]))
    q.put("maxi,3,{}#".format(apt_struct["maximum AM"]))
    q.put("date,3,{}#".format(apt_struct["date"]))
    if erase:
        q.put("scan,3,0#")
        q.put("scan,3,0#")
        q.put("scan,3,0#")
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
    q.put("testread,3#") 
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
                if not "VMDP" in data_r:
                    print(data_r)
            except UnicodeDecodeError:
                print(data)
        if q.empty() and  (time.time() - recent_milis > timeout):
            break
        # print(time.time() - int(recent_milis))
    ser.close()

def read_all_mem():
    ser = serial.Serial(AM_properties.serialPort , AM_properties.baudRate, timeout=1, writeTimeout=0) #ensure non-blocking
    q = queue.LifoQueue(maxsize=5) 
    q.put("dump#")

    recent_milis = int(time.time())
    timeout = 1
    q.put("debug#")
    send_data = q.get()
    print(send_data)
    ser.write(send_data.encode('ascii'))
    data = ser.readline()
    time.sleep(3)
    f = open("memory.txt", "w")
    log_ = open("mem_log.txt", "w")
    try:
        while True:
            data = ser.readline()[:-2] #the last bit gets rid of the new-line chars

            if data:
                try:
                    data_r = data.decode('ascii')
                    if data_r.startswith('0x'):
                        f.write(data_r)
                        f.write('\n')
                    if data_r == "cs[dump] Done!":
                        break
                    if not "VMDP" in data_r:
                        print(data_r)
                        log_.write(data_r)
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
        log_.close()
        memoryParse.translate_tobin()
    except KeyboardInterrupt:
        f.close()
        log_.close()
        memoryParse.translate_tobin()

def find_offset():
    ser = serial.Serial(AM_properties.serialPort , AM_properties.baudRate, timeout=1, writeTimeout=0) #ensure non-blocking
    q = queue.LifoQueue(maxsize=20)
    """
        apt = {"snum MCU":"",
            "snum APTx":"",
            "snum AM":"",
            "maximum AM":0,
            "current AM":0,
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
                if data_r.startswith("pulses "):
                    parsed = data_r.split(' ')
                    # "FIND %d %lu time offset %d"
                    print("pulses is {}".format(parsed[2]))
                    offset["2"] = parsed[2]
                if not "VMDP" in data_r:
                    print(data_r)
            except UnicodeDecodeError:
                print(data)
        if q.empty() and  (time.time() - recent_milis > timeout):
            print(offset)
            ser.close()
            try:
                temp = int(offset["2"])
                return temp
            except TypeError:
                return -1

def enumerate_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

if __name__ == "__main__":
    COMPORT = enumerate_ports()[-1]
    print(read_serial())