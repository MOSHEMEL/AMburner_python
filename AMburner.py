import time
from serial_talk import read_serial, write_serial, read_all_mem, find_offset, enumerate_ports
from serial import *
import AM_properties
import logging

logging.basicConfig(filename='burn.log', filemode='a', format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

class Aptx():
    def __init__(self):
        self.data = {"snum MCU":"Unknown",
                "snum APTx":"Unknown",
                "snum AM":"Unknown",
                "maximum AM":-1,
                "curent AM":-1,
                "init done":False,
                "date": 0}
        self.data_len = len(self.data.keys())

    def __str__(self):
        textual_repr = []
        for key in self.data.keys():
            if key == "date":
                textual_repr.append("{}: {}".format(key, time.ctime(self.data[key])))
            else:
                textual_repr.append("{}: {}".format(key, self.data[key]))
        return str('\n'.join(textual_repr))

    def get_data(self):
        self.data = read_serial()
        self.data["curent AM"] = find_offset()

    def set_data(self, erase):
        write_serial(self.data, erase)

    def dump_mem():
        read_all_mem()

    def write_log(self):
        pass

apt = Aptx()
serial_ports = enumerate_ports()

from tkinter import *
from tkinter import messagebox
 
window = Tk()
 
window.title("Armenta Burn device app")
window.geometry('300x360')

port_COMPORT = StringVar(window)
# throw exception if there is no serial present
if len(serial_ports) == 0:
    messagebox.showinfo('Error','No COM Ports connected!')
    port_COMPORT.set("None")
    serial_ports = ["None"]
else:
    port_COMPORT.set(serial_ports[-1])

rcv_data = Text(window, width=40, height=apt.data_len)
rcv_data.insert(INSERT,str(apt))

ports_menu = OptionMenu(window, port_COMPORT, *serial_ports)

lbl_mcusnum = Label(window, text="MCU Serial Number:").grid(column=0, row=2, sticky=W)
txt_mcusnum = Entry(window,width=10)
lbl_aptxsnum = Label(window, text="APTx Serial Number:").grid(column=0, row=3, sticky=W)
txt_aptxsnum = Entry(window,width=10)
lbl_amsnum = Label(window, text="AM Serial Number:").grid(column=0, row=4, sticky=W)
txt_amsnum = Entry(window,width=10)
lbl_maxi = Label(window, text="Maximum pulses:").grid(column=0, row=5, sticky=W)
txt_maxi = Entry(window,width=5)
erase_var = BooleanVar()
init_var = BooleanVar()
check_init = Checkbutton(window, text="Write init", var=init_var)
check_erase = Checkbutton(window, text="Erase Chip", var=erase_var)


def parse_snum(sn_text):
    
    if len(sn_text.split('-')) == 2:
        return int(''.join(sn_text.split('-')))
    elif len(sn_text.split('-')) > 2:
        raise RuntimeError
    else:
        return int(sn_text)


def burn_AM():
    try:
        AM_properties.serialPort = port_COMPORT.get()
        logging.info('Write memory at : {}'.format(AM_properties.serialPort))
        apt.data["snum MCU"] = parse_snum(txt_mcusnum.get())
        apt.data["snum APTx"] = parse_snum(txt_aptxsnum.get())
        apt.data["snum AM"] = parse_snum(txt_amsnum.get())
        apt.data["maximum AM"] = int(txt_maxi.get())
        if erase_var.get():
            print("erased chip!!")
            apt.data["curent AM"] = 0
        if init_var.get():
            print("Init made!!")
            apt.data["init done"] = True
        else:
            apt.data["init done"] = False
        apt.data["date"] = int(time.time())
        rcv_data.delete('1.0', END)
        rcv_data.insert(INSERT, str(apt))
        apt.set_data(erase_var.get())
        logging.info(str(apt))
    except RuntimeError:
        messagebox.showinfo('Error','Serial Number is wrong format')
    except ValueError:
        messagebox.showinfo('Error','Values Are Wrong!')
    except SerialException:
        messagebox.showinfo('Error','No device at {}'.format(COMPORT))


def read_AM():
    try:
        AM_properties.serialPort = port_COMPORT.get()
        logging.info('Read memory at : {}'.format(AM_properties.serialPort))
        apt.get_data()
        rcv_data.delete('1.0', END)
        rcv_data.insert(INSERT, str(apt))
        logging.info(str(apt))
    except SerialException:
        messagebox.showinfo('Error','No device at {}'.format(COMPORT))


def dump_AM():
    try:
        AM_properties.serialPort = port_COMPORT.get()
        logging.info('Dump memory at : {}'.format(AM_properties.serialPort))
        apt.dump_mem()
    except SerialException:
        messagebox.showinfo('Error','No device at {}'.format(COMPORT))


burn_btn = Button(window, text="Burn baby Burn!", command=burn_AM)
read_btn = Button(window, text="Read em up", command=read_AM)
hex_dump = Button(window, text="dump memory", command=dump_AM)
rcv_data.grid(row=0, columnspan=2, sticky=N)
read_btn.grid(row=1,columnspan=2)
txt_mcusnum.grid(column=1, row=2)
txt_aptxsnum.grid(column=1, row=3)
txt_amsnum.grid(column=1, row=4)
txt_maxi.grid(column=1, row=5)
check_init.grid(row=6, columnspan=2)
check_erase.grid(row=7, columnspan=2)
burn_btn.grid(row=8, columnspan=2)
hex_dump.grid(row=9, columnspan=2)
ports_menu.grid(row=10, columnspan=2)
window.mainloop()

input()
# first we read the AM values:
# we read the MCU header, APTx header and AM header
# Then we ask for:
# 1. MAXIMUM PULSES
# 2. SNUM for AM
# 3. SNUM for APTx
# 4. SNUM for MCU
# 5. check button if init was done
# and we have burn button
# burn does the next:
# erase the whole chip of AM
# write snum, date (current milis since epoch), maximum and init to chip
# write snum to mcu
# write snum to aptx
# THEN:
# we write a log with the datetime as name into a folder
