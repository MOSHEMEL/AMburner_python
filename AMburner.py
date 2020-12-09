import time
from serial_talk import read_serial, write_serial, read_all_mem, find_offset, enumerate_ports
from serial import *
import AM_properties
import logging
import json
from requests import get
import base64
import csv
import boto3
import os
import sys
import threading
from tkinter import *
from tkinter import messagebox
from PIL import ImageTk, Image
VERSION_MAJOR = 1
VERSION_MINOR = 0
VERSION_PATCH = 0
VERSION_AMBURNER = f'{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}'
bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
path_to_img = os.path.abspath(os.path.join(bundle_dir, 'ARmentaSmall.png'))

DEBUG_ENVIROMENT = False
User_name = "default"
Password = ""
Access_key_ID = ""
Secret_access_key = "password321"
Console_login_link = ""
BUCKET_NAME = "am-burner-logs"
FILES_LIST = {}

logging.basicConfig(filename='burn.log', filemode='a', format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)
print("------------Start INIT Settings------------")

if os.path.isfile('user_credentials.csv'):
    with open('user_credentials.csv', newline='') as csvfile:
        dictobj  = csv.DictReader(csvfile)
        for row in dictobj:
            User_name = row["User name"]
            Password = row["Password"]
            Access_key_ID = row["Access key ID"]
            Secret_access_key = row["Secret access key"]
            Console_login_link = row["Console login link"]

    print("------------INIT Settings succesfull------------")
else:
    print("No credentials File Found!")
    input()
    sys.exit()



class ProgressPercentage(object):

    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        # To simplify, assume this is hooked up to a single filename
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            sys.stdout.write(
                "\r%s  %s / %s  (%.2f%%)" % (
                    self._filename, self._seen_so_far, self._size,
                    percentage))
            sys.stdout.flush()

class json_ES_Format():
        def get_IP(self):
            try:
                return get('https://api.ipify.org').text
            except:
                return '127.0.0.1'


        def set_write(self, snum_f, maxi_f, date_f, is_nuked):
            self.Action = 'write'
            self.ip_origin = self.get_IP()

            self.AM_serial = snum_f
            self.AM_maximum = maxi_f
            self.AM_date_of_write = self.format_t(date_f)
            self.AM_is_nuked = is_nuked
            self.version_AM_Burner = VERSION_AMBURNER


        def set_read(self, snum_f, maxi_f, date_f, current_f):
            self.Action = 'read'
            self.ip_origin = self.get_IP()

            self.AM_serial = snum_f
            self.AM_maximum = maxi_f
            self.AM_current = current_f
            self.AM_date_of_write = self.format_t(date_f)
            self.version_AM_Burner = VERSION_AMBURNER

        def format_t(self, date_f):
            self.local_time = time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(int(time.time())))
            self.local_time_t = time.strftime('%H:%M:%S', time.localtime(int(time.time())))
            self.local_time_d = time.strftime('%d/%m/%Y', time.localtime(int(time.time())))
            return time.strftime('%Y%m%d_%H%M%S', time.localtime(int(date_f)))

        def set_dump(self, snum_f, maxi_f, date_f, current_f):
            self.read(snum_f, maxi_f, date_f, current_f)
            self.get_DATA()
            self.version_AM_Burner = VERSION_AMBURNER


        def authenticate(self, name, distributor):
            self.name = name
            self.distributor= distributor


        def get_json(self):
            return json.dumps(self.__dict__)

        def get_DATA(self):
            with open("memory.bin", "rb") as f:
                encodedMem = base64.b64encode(f.read())
                self.DATA = encodedMem.decode()

        def write_log(self):
            fname = f'{self.AM_serial}___{self.AM_date_of_write}.json'
            with open(fname, 'w') as fn:
                json.dump(self.__dict__, fn)
            return fname

        def s3_connect_and_download(self , name="reader_agent"):
            try:
                self.authenticate(name, User_name)
                fname = self.write_log()
                s3 = boto3.client('s3', 
                                    aws_access_key_id=Access_key_ID,
                                    aws_secret_access_key=Secret_access_key) 
                response = s3.upload_file(fname, BUCKET_NAME, fname, Callback=ProgressPercentage(fname),
                                                        ExtraArgs={'ACL': 'bucket-owner-full-control'})
                print("\n")
                os.remove(fname)
            except ClientError as e:
                print("ClientError")
                logging.error(e)
                return False
            except Exception as ex:
                print("Exception")
                logging.error(ex)
                return False
            return True


class Aptx():
    def __init__(self):
        self.data = {
                "snum AM":"Unknown",
                "maximum AM":-1,
                "current AM":-1,
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
        self.data["current AM"] = find_offset()

    def set_data(self, erase):
        write_serial(self.data, erase)

    def dump_mem(self):
        read_all_mem()

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
        apt.data["snum AM"] = parse_snum(txt_amsnum.get())
        apt.data["maximum AM"] = int(txt_maxi.get())
        if erase_var.get():
            print("erased chip!!")
            apt.data["current AM"] = 0

        apt.data["date"] = int(time.time())
        rcv_data.delete('1.0', END)
        rcv_data.insert(INSERT, str(apt))

                # create json
        json_sender = json_ES_Format()
        json_sender.COM_PORT = AM_properties.serialPort
        json_sender.set_write(
            snum_f = apt.data["snum AM"],
            maxi_f = apt.data["maximum AM"],
            date_f= apt.data["date"],
            is_nuked=erase_var.get())

        json_sender.s3_connect_and_download(name=txt_name.get())

        apt.set_data(erase_var.get())
        logging.info(str(apt))

    except RuntimeError:
        messagebox.showinfo('Error','Serial Number is wrong format')
    except ValueError:
        messagebox.showinfo('Error','Values Are Wrong!')
    except SerialException:
        try:
            messagebox.showinfo('Error','No device at {}'.format(COMPORT))
        except NameError:
            messagebox.showinfo('Error','No devices at COM')


def read_AM():
    try:
        AM_properties.serialPort = port_COMPORT.get()

        logging.info('Read memory at : {}'.format(AM_properties.serialPort))
        apt.get_data()
        rcv_data.delete('1.0', END)
        rcv_data.insert(INSERT, str(apt))
        logging.info(str(apt))

        # create json
        json_sender = json_ES_Format()
        json_sender.COM_PORT = AM_properties.serialPort
        json_sender.set_read(
            snum_f = apt.data["snum AM"],
            maxi_f = apt.data["maximum AM"],
            date_f=apt.data["date"],
            current_f=apt.data["current AM"])
        json_sender.s3_connect_and_download()

    except SerialException:
        try:
            messagebox.showinfo('Error','No device at {}'.format(COMPORT))
        except NameError:
            messagebox.showinfo('Error','No devices at COM')



def dump_AM():
    try:
        AM_properties.serialPort = port_COMPORT.get()
        logging.info('Dump memory at : {}'.format(AM_properties.serialPort))
        apt.get_data()
        apt.dump_mem()
        # create json
        json_sender = json_ES_Format()
        json_sender.COM_PORT = AM_properties.serialPort
        json_sender.set_dump(
            snum_f = apt.data["snum AM"],
            maxi_f = apt.data["maximum AM"],
            date_f=apt.data["date"],
            current_f=apt.data["current AM"])

        json_sender.s3_connect_and_download()

    except SerialException:
        try:
            messagebox.showinfo('Error','No device at {}'.format(COMPORT))
        except NameError:
            messagebox.showinfo('Error','No devices at COM')
        

apt = Aptx()
serial_ports = enumerate_ports()
print(serial_ports)
window = Tk()
 
window.title(f'Armenta Burner v{VERSION_AMBURNER}')
window.geometry('300x390')

img = Image.open(path_to_img)
img = ImageTk.PhotoImage(img)
Label(window, image=img).grid(row=0, columnspan=2, sticky=N)
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


erase_var = BooleanVar()


txt_maxi = Entry(window,width=5)
txt_name = Entry(window,width=20)
txt_amsnum = Entry(window,width=10)

check_erase = Checkbutton(window, text="Erase Chip", var=erase_var)

burn_btn = Button(window, text="Burn baby Burn!", command=burn_AM)
read_btn = Button(window, text="Read em up", command=read_AM)
hex_dump = Button(window, text="dump memory", command=dump_AM)
rcv_data.grid(row=1, columnspan=2, sticky=N)
read_btn.grid(row=2,columnspan=2)

lbl_amsnum = Label(window, text="AM Serial Number:").grid(row=3, column=0, sticky=W)
txt_amsnum.grid(row=3, column=1)

lbl_maxi = Label(window, text="Maximum pulses:").grid(row=4, column=0, sticky=W)
txt_maxi.grid(row=4, column=1)

lbl_name = Label(window, text="Name:").grid(row=5, column=0, sticky=W)
txt_name.grid(row=5, column=1)

check_erase.grid(row=6, columnspan=2)
burn_btn.grid(row=7, columnspan=2)
hex_dump.grid(row=8, columnspan=2)
ports_menu.grid(row=9, columnspan=2)
window.mainloop()