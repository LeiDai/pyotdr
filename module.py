#!/usr/bin/env python
# -*- coding: utf-8 -*-

import string
import re
#from fpconst import *
from pyvisa import visa, vpp43
from pyvisa.vpp43_constants import *
from pyvisa.visa_exceptions import *
#from crc16 import crc16xmodem
import time
#from onebench.mutex import mutex

def loge(p1,p2):
    pass
def sleep(s):
    time.sleep(s)

class SerialDevice(visa.ResourceTemplate):

    def __init__(self, resource_name, **keyw):
        visa._warn_for_invalid_keyword_arguments(keyw,
           ("timeout", "lock", "term_chars", "chunk_size", "baud_rate", "data_bits", "stop_bits", "parity", "end_input"))

        keyw.setdefault("timeout", 180)
        keyw.setdefault("term_chars", ">")
        keyw.setdefault("chunk_size", 1000*65536)
        keyw.setdefault("baud_rate",  115200)
        keyw.setdefault("data_bits",  8)
        keyw.setdefault("stop_bits",  1)
        keyw.setdefault("parity",     VI_ASRL_PAR_NONE)
        keyw.setdefault("end_input",  VI_ASRL_END_NONE)

        try:
            visa.ResourceTemplate.__init__(self, resource_name,
                                      **visa._filter_keyword_arguments(keyw, ("timeout", "lock")))
            
            self.term_chars = keyw.get("term_chars")
            self.chunk_size = keyw.get("chunk_size")
            self.baud_rate  = keyw.get("baud_rate")
            self.data_bits  = keyw.get("data_bits")
            self.stop_bits  = keyw.get("stop_bits")
            self.parity     = keyw.get("parity")
            self.end_input  = keyw.get("end_input")

        except VisaIOError, inst:
            if (inst.error_code == VI_ERROR_RSRC_BUSY):
                logc(u'UART_ERROR', 'Serial port is opened by another program!')
            raise inst

# self.mtx = mutex()

    def __set_term_chars(self, term_chars):
        """Set a new termination character sequence.  See below the property
        "term_char"."""
        # First, reset termination characters, in case something bad happens.
        self.__term_chars = ""
        vpp43.set_attribute(self.vi, VI_ATTR_TERMCHAR_EN, VI_FALSE)
        if term_chars == "" or term_chars == None:
            self.__term_chars = term_chars
            return
        # Only the last character in term_chars is the real low-level
        # termination character, the rest is just used for verification after
        # each read operation.
        last_char = term_chars[-1]
        # Consequently, it's illogical to have the real termination character
        # twice in the sequence (otherwise reading would stop prematurely).
        if term_chars[:-1].find(last_char) != -1:
            raise ValueError, "ambiguous ending in termination characters"
        vpp43.set_attribute(self.vi, VI_ATTR_TERMCHAR, ord(last_char))
        vpp43.set_attribute(self.vi, VI_ATTR_TERMCHAR_EN, VI_TRUE)
        self.__term_chars = term_chars
    def __get_term_chars(self):
        """Return the current termination characters for the device."""
        return self.__term_chars
    def __del_term_chars(self):
        self.term_chars = None
    term_chars = property(__get_term_chars, __set_term_chars, __del_term_chars,
        r"""Set or read a new termination character sequence (property).

        Normally, you just give the new termination sequence, which is appended
        to each write operation (unless it's already there), and expected as
        the ending mark during each read operation.  A typical example is CR+LF
        or just CR.  If you assign "" to this property, the termination
        sequence is deleted.

        The default is None, which means that CR is appended to each write
        operation but not expected after each read operation (but stripped if
        present).

        """)

    def __set_baud_rate(self, rate):
        vpp43.set_attribute(self.vi, VI_ATTR_ASRL_BAUD, rate)
    def __get_baud_rate(self):
        return vpp43.get_attribute(self.vi, VI_ATTR_ASRL_BAUD)
    baud_rate = property(__get_baud_rate, __set_baud_rate, None,
                         """Baud rate of the serial instrument""")

    def __get_data_bits(self):
        return vpp43.get_attribute(self.vi, VI_ATTR_ASRL_DATA_BITS)
    def __set_data_bits(self, bits):
        if not 5 <= bits <= 8:
            raise ValueError, "number of data bits must be from 5 to 8"
        vpp43.set_attribute(self.vi, VI_ATTR_ASRL_DATA_BITS, bits)
    data_bits = property(__get_data_bits, __set_data_bits, None,
                         """Number of data bits contained in each frame """
                         """(from 5 to 8)""")

    def __get_stop_bits(self):
        deci_bits = vpp43.get_attribute(self.vi, VI_ATTR_ASRL_STOP_BITS)
        if deci_bits == 10:
            return 1
        elif deci_bits == 15:
            return 1.5
        elif deci_bits == 20:
            return 2
    def __set_stop_bits(self, bits):
        deci_bits = 10 * bits
        if 9 < deci_bits < 11:
            deci_bits = 10
        elif 14 < deci_bits < 16:
            deci_bits = 15
        elif 19 < deci_bits < 21:
            deci_bits = 20
        else:
            raise ValueError, "invalid number of stop bits"
        vpp43.set_attribute(self.vi, VI_ATTR_ASRL_STOP_BITS, deci_bits)
    stop_bits = property(__get_stop_bits, __set_stop_bits, None,
                         """Number of stop bits contained in each frame """
                         """(1, 1.5, or 2)""")

    def __get_parity(self):
        return vpp43.get_attribute(self.vi, VI_ATTR_ASRL_PARITY)
    def __set_parity(self, parity):
        vpp43.set_attribute(self.vi, VI_ATTR_ASRL_PARITY, parity)
    parity = property(__get_parity, __set_parity, None,
                      """The parity used with every frame transmitted """
                      """and received""")

    def __get_end_input(self):
        return vpp43.get_attribute(self.vi, VI_ATTR_ASRL_END_IN)
    def __set_end_input(self, termination):
        vpp43.set_attribute(self.vi, VI_ATTR_ASRL_END_IN, termination)
    end_input = property(__get_end_input, __set_end_input, None,
        """indicates the method used to terminate read operations""")

    def open(self):
        """Re-open the VISA session
        """
        if self.vi:
            vpp43.open(self.vi, self.resource_name, VI_NO_LOCK)
            self.vi = None

    def clear(self):
        """Resets the device.  This operation is highly bus-dependent."""
        vpp43.clear(self.vi)

    def __write(self, message, delay, term_chars=None):
        if term_chars and not message.endswith(term_chars):
            message += term_chars
        elif term_chars is None and not message.endswith("\r\n"):
            message += "\r\n"
        vpp43.write(self.vi, message)
        if (delay > 0.0):
            sleep(delay)    
    
    def __write_mys(self, message, delay, term_chars=None):
        if term_chars and not message.endswith(term_chars):
            message += term_chars
        elif term_chars is None and not message.endswith("\n"):
            message += "\n"
        vpp43.write(self.vi, message)
        if (delay > 0.0):
            sleep(delay)    
    
    def write_2(self,message):
        vpp43.write(self.vi, message)
    def read_2(self):
        return vpp43.read(self.vi, self.chunk_size)
#        return self.__read(0)
    
    def read_3(self,num):
        buffer = ""
#        i=300
        chunk = vpp43.read(self.vi, num)
        buffer += chunk
        return chunk
    
    def __read(self, delay):
        try:
            buffer = ""
            chunk = vpp43.read(self.vi, self.chunk_size)
            buffer += chunk
            while vpp43.get_status() == VI_SUCCESS_MAX_CNT:
                chunk = vpp43.read(self.vi, self.chunk_size)
                buffer += chunk
            if (delay > 0.0):
                sleep(delay)
            return buffer
        except VisaIOError, inst:
            if (inst.error_code == VI_ERROR_TMO):
                loge(u'UART_ERROR', u'Timeout!')
                return buffer
            else:
                raise inst

    def write(self, cmd, wdelay=0.0, term_chars=None):
        """Write a string message to the device.

        Parameters:
        message -- the string message to be sent.

        """
#        self.mtx.lock()
        self.__write(cmd, wdelay)
#        logi(u'OACS_WRITE', cmd)
#        self.mtx.unlock()

    def read(self, delay=0.0):
        """Read the unmodified string sent from the instrument to the computer.
        """
#        self.mtx.lock()
        r = self.__read(delay)
#        read(rdelay)
#        self.mtx.unlock()
#        logi(u'OACS_READ', r)
        return r
    
    def ask(self, cmd, wdelay=0.0, rdelay=0.0, hook=None):
#        self.mtx.lock()
        self.__write(cmd, wdelay)
        if (hook):
            hook()
        r = self.__read(rdelay)
#        self.__read(rdelay)
#        if r == "None" or r == "":
#            self.__write("root", wdelay)
#            time.sleep(0.1)
#            self.__write("oacs", wdelay)
#            time.sleep(0.5)
#            r = self.__read(rdelay)
#            r = self.__read(rdelay)
#        self.mtx.unlock()
#        logi(u'OACS_QUERY', cmd, r)
        return r

    def askm(self, cmd, wdelay=0.0, rdelay=0.0, hook=None):
#        self.mtx.lock()
        self.__write_mys(cmd, wdelay)
        if (hook):
            hook()
        r = self.__read(rdelay)
#        print self.__read(rdelay)
#        if r == "None" or r == "":
#            self.__write("root", wdelay)
#            time.sleep(0.1)
#            self.__write("oacs", wdelay)
#            time.sleep(0.5)
#            r = self.__read(rdelay)
#            r = self.__read(rdelay)
#        self.mtx.unlock()
#        logi(u'OACS_QUERY', cmd, r)
#        print r
        return r

    def ask_for_xmodem(self, cmd, wdelay=0.0, rdelay=0.0, hook=None):
#        self.mtx.lock()
        tmp=self.term_chars
        self.term_chars = 'C'
        self.__write(cmd, wdelay)
        if (hook):
            hook()
        r = self.__read(rdelay)
        self.term_chars = tmp
#        self.mtx.unlock()
#        logi(u'OACS_QUERY', cmd, r)
        return r


class Version(object):
    def __init__(self, module):
        self.module = module
        self.ptable={'get_firmware':self.parse_ver_value,
                     'get_design':self.parse_ver_value,
                     'get_platform':self.parse_ver_value,
                     'get_verfull':self.parse_ver_value,
                     'get_verhw':self.parse_ver_value,
                     }
        self.etable={'get_firmware':self.module.parse_print_error,
                     'get_design':self.module.parse_print_error,
                     'get_platform':self.module.parse_print_error,
                     'get_verfull':self.module.parse_print_error,
                     'get_verhw':self.module.parse_print_error,
                     }

        
    def parse_ver_value(self, lines, matches):
        result_d = rd = {}
        for i in range(len(lines)):
            temp=lines[i].split(':')            
            rd[temp[0]]=temp[1].strip()
            
        if (matches==None):
            return result_d
        
        for rdkey in rd.keys():
            if (rdkey.upper()==matches.upper()):
                return rd[rdkey]
        
        return 'Cannot Match'
                                              
    def __get_firmware(self):
        command = "VER FULL"
        return self.module.parse_result(self.module.ask(command), self.ptable['get_firmware'],self.etable['get_firmware'], "Firmware Vers")
    firmware = property(__get_firmware, None, None, "firmware version")

    def __get_design(self):
        command = "VER FULL"
        return self.module.parse_result(self.module.ask(command), self.ptable['get_design'],self.etable['get_design'], "Design version")
    design = property(__get_design, None, None, "design version")
    
    def __get_platform(self):
        command = "VER FULL"
        return self.module.parse_result(self.module.ask(command), self.ptable['get_platform'],self.etable['get_platform'], "Platform")
    platform = property(__get_platform, None, None, "Platform")  
    
    def __get_verfull(self):
        command = "VER FULL"
        return self.module.parse_result(self.module.ask(command), self.ptable['get_verfull'],self.etable['get_verfull'], None)
    verfull = property(__get_verfull, None, None, "VER FULL")
    
    def __get_verhw(self):
        command = "VER HW"
        return self.module.parse_result(self.module.ask(command), self.ptable['get_verhw'],self.etable['get_verhw'], None)
    verhw = property(__get_verhw, None, None, "VER HW")

class Recv(object):
    SOH = '\x01'
    STX = '\x02'
    EOT = '\x04'
    ACK = '\x06'
    NAK = '\x15'
    CAN = '\x18'
    def __init__(self,filename,module):
        self.file=open(filename, 'rb')
        self.module=module
        self.module.timeout=10

    def return_value(self, lines, *matches):
        return lines

    def __get_fw128(self):
        self.module.ask_for_xmodem('recv fw')
        p = 1 
        s = self.file.read(128)############
        while s: 
            s = s + '\xFF'*(128 - len(s))
            while 1:
                strs=Recv.SOH+chr(p)+chr(255 - p)+s+chr(crc16xmodem(s)>>8)+chr(crc16xmodem(s)&0xff)
                self.module.write_2(strs)
                while 1:
                    answer = self.module.read_3(1)
                    if answer <> 'C':
                        break
                    
                if  answer == Recv.NAK:
                    continue 
                if  answer == Recv.ACK:
                    break
                return False 
            s = self.file.read(128) 
            p = (p + 1)%256 
            print '.', 
        self.module.write_2(Recv.EOT)
        while 1:
            answer = self.module.read_3(1)
            if  answer == Recv.NAK:
                self.module.write_2(Recv.EOT)
                while 1:
                    answer = self.module.read_3(1)
                    if  answer == Recv.ACK:
                        break
                break
        self.module.write_2(Recv.CAN+Recv.CAN)
        time.sleep(0.5)
        self.module.timeout=3
        return self.module.parse_result(self.module.read(), self.return_value,self.module.parse_print_error, None)
    fw128 = property(__get_fw128, None, None, "Recv fw")

    def __get_fw1k(self):
        self.module.ask_for_xmodem('recv fw')
        p = 1 
        s = self.file.read(1024)############
        while s: 
            s = s + '\xFF'*(1024 - len(s))
            while 1:
                strs=Recv.STX+chr(p)+chr(255 - p)+s+chr(crc16xmodem(s)>>8)+chr(crc16xmodem(s)&0xff)
                self.module.write_2(strs)
                while 1:
                    answer = self.module.read_3(1)
                    if answer <> 'C':
                        break
                    
                if  answer == Recv.NAK:
                    continue 
                if  answer == Recv.ACK:
                    break
                return False 
            s = self.file.read(1024) 
            p = (p + 1)%256 
            print '.\n', 
        self.module.write_2(Recv.EOT)
        while 1:
            answer = self.module.read_3(1)
            if  answer == Recv.NAK:
                self.module.write_2(Recv.EOT)
                while 1:
                    answer = self.module.read_3(1)
                    if  answer == Recv.ACK:
                        break
                break
            else:
                print "+++++"+char(answer)
        self.module.write_2(Recv.CAN+Recv.CAN)
        time.sleep(1)
        self.module.timeout=3
        return self.module.parse_result(self.module.read(), self.return_value,self.module.parse_print_error, None)
    
    fw = property(__get_fw1k, None, None, "Recv fw")
    
    def __get_cfg128(self):
        self.module.ask_for_xmodem('recv cfg')
        p = 1 
        s = self.file.read(128)############
        while s: 
            s = s + '\xFF'*(128 - len(s))
            while 1:
                strs=Recv.SOH+chr(p)+chr(255 - p)+s+chr(crc16xmodem(s)>>8)+chr(crc16xmodem(s)&0xff)
                self.module.write_2(strs)
                while 1:
                    answer = self.module.read_3(1)
                    if answer <> 'C':
                        break
                    
                if  answer == Recv.NAK:
                    continue 
                if  answer == Recv.ACK:
                    break
                return False 
            s = self.file.read(128) 
            p = (p + 1)%256 
            print '.', 
        self.module.write_2(Recv.EOT)
        while 1:
            answer = self.module.read_3(1)
            if  answer == Recv.NAK:
                self.module.write_2(Recv.EOT)
                while 1:
                    answer = self.module.read_3(1)
                    if  answer == Recv.ACK:
                        break
                break
        self.module.write_2(Recv.CAN+Recv.CAN)
        time.sleep(0.5)
        self.module.timeout=3
        return self.module.parse_result(self.module.read(), self.return_value,self.module.parse_print_error, None)
    cfg128 = property(__get_cfg128, None, None, "Recv cfg")

    def __get_cfg1k(self):
        self.module.ask_for_xmodem('recv cfg')
        p = 1 
        s = self.file.read(1024)############
        while s: 
            s = s + '\xFF'*(1024 - len(s))
            while 1:
                strs=Recv.STX+chr(p)+chr(255 - p)+s+chr(crc16xmodem(s)>>8)+chr(crc16xmodem(s)&0xff)
                self.module.write_2(strs)
                while 1:
                    answer = self.module.read_3(1)
                    if answer <> 'C':
                        break
                    
                if  answer == Recv.NAK:
                    continue 
                if  answer == Recv.ACK:
                    break
                return False 
            s = self.file.read(1024) 
            p = (p + 1)%256 
            print '.', 
        self.module.write_2(Recv.EOT)
        while 1:
            answer = self.module.read_3(1)
            if  answer == Recv.NAK:
                self.module.write_2(Recv.EOT)
                while 1:
                    answer = self.module.read_3(1)
                    if  answer == Recv.ACK:
                        break
                break
        self.module.write_2(Recv.CAN+Recv.CAN)
        time.sleep(1)
        self.module.timeout=3
        return self.module.parse_result(self.module.read(), self.return_value,self.module.parse_print_error, None)
    
    cfg = property(__get_cfg1k, None, None, "Recv cfg")
    
    def __get_cal128(self):
        self.module.ask_for_xmodem('recv cal')
        p = 1 
        s = self.file.read(128)############
        while s: 
            s = s + '\xFF'*(128 - len(s))
            while 1:
                strs=Recv.SOH+chr(p)+chr(255 - p)+s+chr(crc16xmodem(s)>>8)+chr(crc16xmodem(s)&0xff)
                self.module.write_2(strs)
                while 1:
                    answer = self.module.read_3(1)
                    if answer <> 'C':
                        break
                    
                if  answer == Recv.NAK:
                    continue 
                if  answer == Recv.ACK:
                    break
                return False 
            s = self.file.read(128) 
            p = (p + 1)%256 
            print '.', 
        self.module.write_2(Recv.EOT)
        while 1:
            answer = self.module.read_3(1)
            if  answer == Recv.NAK:
                self.module.write_2(Recv.EOT)
                while 1:
                    answer = self.module.read_3(1)
                    if  answer == Recv.ACK:
                        break
                break
        self.module.write_2(Recv.CAN+Recv.CAN)
        time.sleep(0.5)
        self.module.timeout=3
        return self.module.parse_result(self.module.read(), self.return_value,self.module.parse_print_error, None)
    cal128 = property(__get_cal128, None, None, "Recv cal")

    def __get_cal1k(self):
        
        self.module.ask_for_xmodem('recv cal')
        p = 1 
        s = self.file.read(1024)############
        while s: 
            s = s + '\xFF'*(1024 - len(s))
            while 1:
                strs=Recv.STX+chr(p)+chr(255 - p)+s+chr(crc16xmodem(s)>>8)+chr(crc16xmodem(s)&0xff)
                self.module.write_2(strs)
                while 1:
                    answer = self.module.read_3(1)
                    if answer <> 'C':
                        break
                    
                if  answer == Recv.NAK:
                    continue 
                if  answer == Recv.ACK:
                    break
                return False 
            s = self.file.read(1024) 
            p = (p + 1)%256 
            print '.', 
        self.module.write_2(Recv.EOT)
        while 1:
            answer = self.module.read_3(1)
            if  answer == Recv.NAK:
                self.module.write_2(Recv.EOT)
                while 1:
                    answer = self.module.read_3(1)
                    if  answer == Recv.ACK:
                        break
                break
        self.module.write_2(Recv.CAN+Recv.CAN)
        time.sleep(1)
        self.module.timeout=3
        return self.module.parse_result(self.module.read(), self.return_value,self.module.parse_print_error, None)
    
    cal = property(__get_cal1k, None, None, "Recv cal")

    def __get_hw128(self):
        self.module.ask_for_xmodem('recv hw')
        p = 1 
        s = self.file.read(128)############
        while s: 
            s = s + '\xFF'*(128 - len(s))
            while 1:
                strs=Recv.SOH+chr(p)+chr(255 - p)+s+chr(crc16xmodem(s)>>8)+chr(crc16xmodem(s)&0xff)
                self.module.write_2(strs)
                while 1:
                    answer = self.module.read_3(1)
                    if answer <> 'C':
                        break
                    
                if  answer == Recv.NAK:
                    continue 
                if  answer == Recv.ACK:
                    break
                return False 
            s = self.file.read(128) 
            p = (p + 1)%256 
            print '.', 
        self.module.write_2(Recv.EOT)
        while 1:
            answer = self.module.read_3(1)
            if  answer == Recv.NAK:
                self.module.write_2(Recv.EOT)
                while 1:
                    answer = self.module.read_3(1)
                    if  answer == Recv.ACK:
                        break
                break
        self.module.write_2(Recv.CAN+Recv.CAN)
        time.sleep(0.5)
        self.module.timeout=3
        return self.module.parse_result(self.module.read(), self.return_value,self.module.parse_print_error, None)
    hw128 = property(__get_hw128, None, None, "Recv hw")

    def __get_hw1k(self):
        self.module.ask_for_xmodem('recv hw')
        p = 1 
        s = self.file.read(1024)############
        while s: 
            s = s + '\xFF'*(1024 - len(s))
            while 1:
                strs=Recv.STX+chr(p)+chr(255 - p)+s+chr(crc16xmodem(s)>>8)+chr(crc16xmodem(s)&0xff)
                self.module.write_2(strs)
                while 1:
                    answer = self.module.read_3(1)
                    if answer <> 'C':
                        break
                    
                if  answer == Recv.NAK:
                    continue 
                if  answer == Recv.ACK:
                    break
                return False 
            s = self.file.read(1024) 
            p = (p + 1)%256 
            print '.', 
        self.module.write_2(Recv.EOT)
        while 1:
            answer = self.module.read_3(1)
            if  answer == Recv.NAK:
                self.module.write_2(Recv.EOT)
                while 1:
                    answer = self.module.read_3(1)
                    if  answer == Recv.ACK:
                        break
                break
        self.module.write_2(Recv.CAN+Recv.CAN)
        time.sleep(1)
        self.module.timeout=3
        return self.module.parse_result(self.module.read(), self.return_value,self.module.parse_print_error, None)
    hw = property(__get_hw1k, None, None, "Recv hw")

#    time.sleep(1)

#    def __get_hw(self):
#        
#    def __get_cal(self):
#    
#    def __get_cfg(self):
        
class Alarm(object):
    def __init__(self, name, module):
        self.name = name
        self.module = module
        self.ptable={'get_sta':self.module.parse_line_value,
                     'get_sst':self.module.parse_line_value,
                     'get_chg':self.module.parse_line_value,
                     'get_thr':self.module.parse_line_value,
                     'set_thr':self.module.parse_line_value,
                     'get_hys':self.module.parse_line_value,
                     'set_hys':self.module.parse_line_value,
                     'get_thrmin':self.module.parse_line_value,
                     'get_thrmax':self.module.parse_line_value,
                     'get_hysmin':self.module.parse_line_value,
                     'get_hysmax':self.module.parse_line_value,
                     'get_pin':self.module.parse_line_value,
                     'get_mode':self.module.parse_line_value,
                     'get_tf':self.module.parse_line_value,
                     'set_tf':self.module.parse_line_value,
                     'get_tr':self.module.parse_line_value,
                     'set_tr':self.module.parse_line_value,
                     'get_all':self.module.parse_line_value
                     }
        self.etable={'get_sta':self.module.parse_print_error,
                     'get_sst':self.module.parse_print_error,
                     'get_chg':self.module.parse_print_error,
                     'get_thr':self.module.parse_print_error,
                     'set_thr':self.module.parse_print_error,
                     'get_hys':self.module.parse_print_error,
                     'set_hys':self.module.parse_print_error,
                     'get_thrmin':self.module.parse_print_error,
                     'get_thrmax':self.module.parse_print_error,
                     'get_hysmin':self.module.parse_print_error,
                     'get_hysmax':self.module.parse_print_error,
                     'get_pin':self.module.parse_print_error,
                     'get_mode':self.module.parse_print_error,
                     'get_tf':self.module.parse_print_error,
                     'set_tf':self.module.parse_print_error,
                     'get_tr':self.module.parse_print_error,
                     'set_tr':self.module.parse_print_error,
                     'get_all':self.module.parse_print_error
                     }   
        
    def __get_sta(self):
        command = self.module.buildCommand("ALRM", self.name, "STA")
        return self.module.parse_result(self.module.ask(command), self.ptable['get_sta'], self.etable['get_sta'],"ALRM", self.name, "STA")
    sta = property(__get_sta, None, None, "alarm status")

    def __get_sst(self):
        command = self.module.buildCommand("ALRM", self.name, "SST")
        return self.module.parse_result(self.module.ask(command), self.ptable['get_sst'], self.etable['get_sst'], "ALRM", self.name, "SST")
    sst = property(__get_sst, None, None, "alarm sticky status")

    def __get_chg(self):
        command = self.module.buildCommand("ALRM", self.name, "CHG")
        return self.module.parse_result(self.module.ask(command), self.ptable['get_chg'], self.etable['get_chg'], "ALRM", self.name, "CHG")
    chg = property(__get_chg, None, None, "alarm changed")

    def __get_thr(self):
        command = self.module.buildCommand("ALRM", self.name, "THR")
        return self.module.parse_result(self.module.ask(command), self.ptable['get_thr'], self.etable['get_thr'], "ALRM", self.name, "THR")
    def __set_thr(self, setpoint):
        command = self.module.buildCommand("ALRM", self.name, "THR", setpoint)
        return self.module.parse_result(self.module.ask(command), self.ptable['set_thr'], self.etable['set_thr'])
    thr = property(__get_thr, __set_thr, None, "alarm threshold")

    def __get_hys(self):
        command = self.module.buildCommand("ALRM", self.name, "HYS")
        return self.module.parse_result(self.module.ask(command), self.ptable['get_hys'], self.etable['get_hys'],"ALRM", self.name, "HYS")
    def __set_hys(self, setpoint):
        command = self.module.buildCommand("ALRM", self.name, "HYS", setpoint)
        return self.module.parse_result(self.module.ask(command), self.ptable['set_hys'], self.etable['set_hys'])
    hys = property(__get_hys, __set_hys, None, "alarm hysteresis")

    def __get_thrmin(self):
        command = self.module.buildCommand("ALRM", self.name, "THRMIN")
        return self.module.parse_result(self.module.ask(command), self.ptable['get_thrmin'], self.etable['get_thrmin'], "ALRM", self.name, "THRMIN")
    thrmin = property(__get_thrmin, None, None, "alarm minimum threshold")

    def __get_thrmax(self):
        command = self.module.buildCommand("ALRM", self.name, "THRMAX")
        return self.module.parse_result(self.module.ask(command), self.ptable['get_thrmax'], self.etable['get_thrmax'], "ALRM", self.name, "THRMAX")
    thrmax = property(__get_thrmax, None, None, "alarm maximum threshold")

    def __get_hysmin(self):
        command = self.module.buildCommand("ALRM", self.name, "HYSMIN")
        return self.module.parse_result(self.module.ask(command), self.ptable['get_hysmin'], self.etable['get_hysmin'], "ALRM", self.name, "HYSMIN")
    hysmin = property(__get_hysmin, None, None, "alarm minimum hysteresis")

    def __get_hysmax(self):
        command = self.module.buildCommand("ALRM", self.name, "HYSMAX")
        return self.module.parse_result(self.module.ask(command), self.ptable['get_hysmax'], self.etable['get_hysmax'], "ALRM", self.name, "HYSMAX")
    hysmax = property(__get_hysmax, None, None, "alarm maximum hysteresis")

    def __get_pin(self):
        command = self.module.buildCommand("ALRM", self.name, "PIN")
        return self.module.parse_result(self.module.ask(command), self.ptable['get_pin'], self.etable['get_pin'], "ALRM", self.name, "PIN")
    pin = property(__get_pin, None, None, "alarm pin")

    def __get_mode(self):
        command = self.module.buildCommand("ALRM", self.name, "MODE")
        return self.module.parse_result(self.module.ask(command), self.ptable['get_mode'], self.etable['get_mode'], "ALRM", self.name, "MODE")
    mode = property(__get_mode, None, None, "alarm mode")

    def __get_tr(self):
        command = self.module.buildCommand("ALRM", self.name, "TR")
        return self.module.parse_result(self.module.ask(command), self.ptable['get_tr'], self.etable['get_tr'], "ALRM", self.name, "TR")
    def __set_tr(self, setpoint):
        command = self.module.buildCommand("ALRM", self.name, "TR", setpoint)
        return self.module.parse_result(self.module.ask(command), self.ptable['set_tr'], self.etable['set_tr'])
    tr = property(__get_tr, __set_tr, None, "alarm trip debounce time")

    def __get_tf(self):
        command = self.module.buildCommand("ALRM", self.name, "TF")
        return self.module.parse_result(self.module.ask(command), self.ptable['get_tf'], self.etable['get_tf'], "ALRM", self.name, "TF")
    def __set_tf(self, setpoint):
        command = self.module.buildCommand("ALRM", self.name, "TF", setpoint)
        return self.module.parse_result(self.module.ask(command), self.ptable['set_tf'], self.etable['set_tf'])
    tf = property(__get_tf, __set_tf, None, "alarm reset debounce time")

    def __get_all(self):
        command = self.module.buildCommand("ALRM", self.name, "ALL")
        return self.module.parse_result(self.module.ask(command), self.ptable['get_all'], self.etable['get_all'], "ALRM", self.name)
    all = property(__get_all, None, None, None)

class POKE(object):
    def __init__(self,address,module):
        self.address=address
        self.module=module
        self.ptable={'set_set':self.module.parse_line_value }
        self.etable={'set_set':self.module.parse_print_error}
    def __set_set(self,setpoint):
        command = self.module.buildCommand("POKE", self.address, setpoint)
        return self.module.parse_result(self.module.ask(command), self.ptable['set_set'], self.etable['set_set'])
    set = property(None, __set_set, None, "POKE SET")

class DUMP(object):
    def __init__(self,address,module):
        self.address=address
        self.module=module
#        self.ptable={'get_get_str':self.parse_dump_value }
#        self.etable={'get_get_str':self.module.parse_print_error}
        self.ptable={'get_get_num':self.parse_line_value }
        self.etable={'get_get_num':self.module.parse_print_error}

    def parse_dump_result(self,result):
        if (not result):
            return None
        if (self.module.echo_mode=="ON"):
            result = result[result.find('\n') + 1:]
        result = result[:result.find('>')]
        return result
    
    def parse_line_value(self, lines, *matches):
        """ Merge single line result into one dictionary
            [{1:{"ILD":98.2}}, {1:{"ISP":98.1}}, {2:{"ILD":149.5}}, {2:{"ISP":148.9}}
            becomes:
            {1:{"ILD":98.2, "ISP":98.1}, 2:{"ILD":149.5, "ISP":148.9}}}
        """
        result_m = {}
        for line in lines:
            result = self.parse_singleline_value(line, *matches)
            r = result_m
            if (result == None):
                continue
            elif (type(result) == dict):
                while (type(result) == dict):
                    keys = result.keys()
                    if (len(keys) == 1):
                        key, val = keys[0], result[keys[0]]
                        if (r.has_key(key)):
                            pass
                        elif (type(val) == dict):
                            r[key] = {}
                        else:
                            r[key] = val
                            break
                        result = result[key]
                        r = r[key]
            else:
                result_m = result
                break

        if (type(result_m) == dict and len(result_m) == 0):
            result_m = None

        return result_m

    def parse_singleline_value(self, line, *matches):
        """ Parse a single line using given match pattern
            line    = "PUMP 1 ILD: 98.2 mA"
            matches = ["PUMP", None, None]  -->  result  = {1:{"ILD":98.2}}
            matches = ["PUMP", 1,    None]  -->  result  = {"ILD":98.2}
            matches = ["PUMP", 1,    ILD]   -->  result  = 98.2
        """
        valid = True
        result = []

        tokens = line.split(':')
        if (len(tokens) == 2):
            # command tokens (left side of ":")
            tokens_c = tokens[0].split()
            for i in range(len(tokens_c)):
                if (i > len(matches)-1 or matches[i] == None):
                    result.append(self.castValue(tokens_c[i].strip()))
                elif (str(matches[i]).upper() != tokens_c[i].upper()):
                    valid = False
                    result = []
                    break
            if (valid):
                # result tokens (right side of ":")
                tokens_r = tokens[1].split()
                if (len(tokens_r) > 0):
                    result.append(self.castValue(tokens_r[0].strip()))

        # Convert to dictionary
        if (len(result) > 1):
            result_d = rd = {}
            for i in range(len(result)):
                if (i == len(result)-2):
                    rd[result[i]] = result[i+1]
                    break
                else:
                    rd[result[i]] = {}
                rd = rd[result[i]]
            result = result_d
        # Return single value
        elif (len(result) == 1):
            result = result[0]
        # Invalid
        else:
            loge(u'OACS_ERROR', line)
            result = None

        return result
    
    def castValue(self, value):
        v = value
        try:
            v = int(value,16)
        except ValueError:
            try:
                v = float(value)
            except ValueError:
                pass
        return v


    def __get_get(self):
        if (type(self.address)== long or type(self.address)== int):
#            self.address=int(self.address,16)
            command = self.module.buildCommand("DUMP", self.address,1)
            return self.module.parse_result(self.module.ask(command), self.ptable['get_get_num'], self.etable['get_get_num'],'%x'%self.address)
        elif(type(self.address)==str):
            command = self.module.buildCommand("DUMP", self.address)
            return self.parse_dump_result(self.module.ask(command))



#        if type(self.address)==str:
#            command = self.module.buildCommand("DUMP", self.address)
#            return self.parse_dump_result(self.module.ask(command))
#        else:
#            command = self.module.buildCommand("DUMP", self.address,1)
#            return int(self.module.parse_result(self.module.ask(command), self.ptable['get_get_num'], self.etable['get_get_num'],'%x'%self.address),16)
    get = property(__get_get,None,None,'DUMP GET')
            
class TC(object):
    def __init__(self, num, module):
        self.num = num
        self.module = module
        self.ptable={'get_act':self.module.parse_line_value,
                     'set_set':self.module.parse_line_value,
                     'get_set':self.module.parse_line_value,
                     'get_all':self.module.parse_line_value
                    }
        
        self.etable={'get_act':self.module.parse_print_error,
                     'set_set':self.module.parse_print_error,
                     'get_set':self.module.parse_print_error,
                     'get_all':self.module.parse_print_error
                    }
        
    def __get_act(self):
        command = self.module.buildCommand("TC", self.num, "ACT")
        return self.module.parse_result(self.module.ask(command), self.ptable['get_act'], self.etable['get_act'],"TC", self.num, "ACT")
    act = property(__get_act, None, None, "TC ACT")

    def __get_set(self):
        command = self.module.buildCommand("TC", self.num, "SET")
        return self.module.parse_result(self.module.ask(command), self.ptable['get_set'], self.etable['get_set'],"TC", self.num, "SET")
    def __set_set(self,setpoint):
        command = self.module.buildCommand("TC", self.num, "SET", setpoint)
        return self.module.parse_result(self.module.ask(command), self.ptable['set_set'], self.etable['set_set'],"TC", self.num, "SET")
    set = property(__get_set, __set_set, None, "TC SET")

    def __get_all(self):
        command = self.module.buildCommand("TC", self.num)
        print command
        return self.module.parse_result(self.module.ask(command), self.ptable['get_all'], self.etable['get_all'], "TC",self.num)
    all = property(__get_all, None, None, None)                   

class ModuleError():
    def __init__(self,meg_error):
        self.error_message=meg_error
    def printerror(self):
        print 'Fail\n %s'%self.error_message

class Module(SerialDevice):

    def __init__(self, resource_name,**keyw):
        SerialDevice.__init__(self, resource_name,**keyw)
        self.sendmode=None
        old_timeout = self.timeout
        self.timeout = 0.1

        # Detect baud rate
        self.echo_mode = None
        rates = (9600,115200, 57600,  1200, 2400, 4800, 19200, 38400)
        self.ptable={
                     "get_boot":self.parse_line_value,
                     "get_baud":self.parse_line_value,
                     "set_baud":self.parse_line_value,
                     'get_ast':self.parse_line_value,
                     'get_ast' :self.parse_multiline_ast,
                     'get_mst' :self.parse_singleline_alarms,
                     "get_mt": self.parse_line_value,
                     'get_key':self.parse_line_value,
                     'set_key':self.parse_line_value,
                     'get_astm' :self.parse_singleline_alarms,
                     'set_astm' :self.parse_singleline_alarms,
                     'get_cfg' :self.parse_cfg,
                     'get_cal' :self.parse_cal
                     }
        self.etable={"get_boot":self.parse_print_error,
                     "get_baud":self.parse_print_error,
                     "set_baud":self.parse_print_error,
                     'get_ast':self.parse_print_error,
                     'get_mst':self.parse_print_error,
                     "get_mt" :self.parse_print_error,
                     'get_key':self.parse_print_error,
                     'set_key':self.parse_print_error,
                     'get_astm':self.parse_print_error,
                     'set_astm':self.parse_print_error,
                     'get_cfg':self.parse_print_error,
                     'get_cal':self.parse_print_error
                     }
        
        self.alrm_obj={}
        self.ver_obj={}
        self.tc_obj={}
        self.poke_obj={}
        self.dump_obj={}
        self.recv_obj={}
        for rate in rates:
            self.baud_rate = rate
            echo = self.echo
            if (echo):
                self.echo_mode = echo
                break
        if (not self.echo_mode):
            raise ValueError, "Echo return None"
        self.timeout = old_timeout
    
    def parse_result(self, result, parse_line, parse_error, *matches):
        if (not result):
            return None
        lines = result.splitlines()
        parse = False
        lines_r = []
        r = None
        if (self.echo_mode == "OFF"):
            parse = True
        for i in range(len(lines)):
            if (parse == False and i == 0 and self.echo_mode == "ON"):
                parse = True
            elif (parse == True and lines[i].strip() == ""):
                pass
            elif (parse == True and lines[i] == ">"):
                parse = False
            elif (parse == True):
                lines_r.append(lines[i])
            else:
                pass
        e=None
#        print lines_r
        if (callable(parse_error)):
            e=parse_error(lines_r)
        lines_tmp=lines_r
        lines_r=[]
        for line in lines_tmp:
            if self.sendmode == "TX":
                line=string.replace(line, "TX ", "")
                lines_r.append(line)
            elif self.sendmode == "RX":                
                line=string.replace(line, "RX ", "")
                lines_r.append(line)
            else:
                lines_r.append(line)
        self.sendmode=None
        matches = list(matches)
        while matches.count('') >0:
            matches.remove('')
        if (not e):   
            if (callable(parse_line)):
                return parse_line(lines_r, *matches)
        else:
            return lines_r
        
#        return result

    def ask(self, cmd, **args):
        if self.sendmode == None:
            return SerialDevice.ask(self,cmd, **args)
        elif self.sendmode == "TX":
            return SerialDevice.ask(self,"TX "+cmd, *args)
        elif self.sendmode == "RX":
            return SerialDevice.ask(self,"RX "+cmd, *args)
        
    def parse_print_error(self,lines):
        e=None
        if(len(lines)==1 and lines[0][0]=='?'):
            e=ModuleError(lines[0])
            e.printerror()
        return e
    

    def parse_line_value(self, lines, *matches):
        """ Merge single line result into one dictionary
            [{1:{"ILD":98.2}}, {1:{"ISP":98.1}}, {2:{"ILD":149.5}}, {2:{"ISP":148.9}]
            becomes:
            {1:{"ILD":98.2, "ISP":98.1}, 2:{"ILD":149.5, "ISP":148.9}}}
        """
        result_m = {}
        for line in lines:
            result = self.parse_singleline_value(line, *matches)
            r = result_m
            if (result == None):
                continue
            elif (type(result) == dict):
                while (type(result) == dict):
                    keys = result.keys()
                    if (len(keys) == 1):
                        key, val = keys[0], result[keys[0]]
                        if (r.has_key(key)):
                            pass
                        elif (type(val) == dict):
                            r[key] = {}
                        else:
                            r[key] = val
                            break
                        result = result[key]
                        r = r[key]
            else:
                result_m = result
                break

        if (type(result_m) == dict and len(result_m) == 0):
            result_m = None

        return result_m

    def parse_singleline_alarms(self, lines, *matches):
        alarms = []
        if (len(lines) == 1):
            tokens = lines[0].split(':')
            if (len(tokens) == 2):
                tokens_r = tokens[1].split()
                for t in tokens_r:
                    alarms.append(t.strip())
        return alarms
    
    def parse_multiline_ast(self, lines, *matches):
        alarms = []
        if (len(lines) <= 3):
            for num in range(len(lines)):
                tokens = lines[num].split(':')
                if (len(tokens) == 2):
                    tokens_r = tokens[1].split()
                    for t in tokens_r:
                        alarms.append(t.strip())
        return alarms

    def parse_singleline_value(self, line, *matches):
        """ Parse a single line using given match pattern
            line    = "PUMP 1 ILD: 98.2 mA"
            matches = ["PUMP", None, None]  -->  result  = {1:{"ILD":98.2}}
            matches = ["PUMP", 1,    None]  -->  result  = {"ILD":98.2}
            matches = ["PUMP", 1,    ILD]   -->  result  = 98.2
        """
        matches
        valid = True
        result = []

        tokens = line.split(':')
        if (len(tokens) == 2):
            # command tokens (left side of ":")
            tokens_c = tokens[0].split()
            for i in range(len(tokens_c)):
                if (i > len(matches)-1 or matches[i] == None):
                    result.append(self.castValue(tokens_c[i].strip()))
                elif (str(matches[i]).upper() != tokens_c[i] and str(matches[i]) != tokens_c[i]):
                    valid = False
                    result = []
                    break
            if (valid):
                # result tokens (right side of ":")
                tokens_r = tokens[1].split()
                if (len(tokens_r) > 0):
                    if len(tokens_r)>2:
                        for li in range(len(tokens_r)-1):
                            b=self.castValue(tokens_r[li].strip())
                            result.append(b)
                    else:
                        b=self.castValue(tokens_r[0].strip())
                        result.append(b)


        # Convert to dictionary
        if (len(result) > 1):
            result_d = rd = {}
            for i in range(len(result)):
                if (i == len(result)-2):
                    rd[result[i]] = result[i+1]
                    break
                else:
                    rd[result[i]] = {}
                rd = rd[result[i]]
            result = result_d
        # Return single value
        elif (len(result) == 1):
            result = result[0]
        # Invalid
        else:
            loge(u'OACS_ERROR', line)
            result = None

        return result

    def buildCommand(self, *params):
        command =""
        for param in params:
            if (type(param) == int or type(param)==long):
                command += " %d" % param
            elif (type(param) == float):
                command += " %.2f" % param
            elif(type(param) == str and param !=""):
                command += " %s" % param.upper()
            else:
                continue
        return command.strip()

    def castValue(self, value):
        v = value
        try:
            v = int(value)
        except ValueError:
            try:
                v = float(value)
            except ValueError:
                pass
        return v

    def __boot(self):
        
        command = "boot"
        return self.ask(command)
#        try:
#            return self.read_2()
#        except:
#            return
#        self.write_2(command)
#        self.close()
#        time.sleep(1)
#        return self.read_2()
        #return self.parse_result(self.ask(command), None, "BOOT")
    boot= property(__boot, None, None, "BOOT")

#    def boot(self):
#        command = "BOOT"
#        self.write_2(command)
#        return self.read_2()
#        return self.parse_result(self.ask(command), None, "BOOT")

    def __bootfpga(self):
        for i in range(20):
            self.write_2('^')
            time.sleep(0.01)
        self.write_2('K')
        self.write_2('B')
        print self.read_2()
    bootfpga=property(__bootfpga,None,None,'BOOT GPGA')
    
    def __rst(self):
        command = "RST"
        return self.parse_result(self.ask(command), None, "RST")
    rst= property(__rst, None, None, "RST")
    def __get_baud(self):
        command = "BAUD"
        return self.parse_result(self.ask(command), self.ptable['get_baud'],self.etable['get_baud'], "BAUD")
    def __set_baud(self, rate):
        if (rate):
            command = self.buildCommand("BAUD", rate)
            self.parse_result(self.ask(command), self.ptable['set_baud'],self.etable['set_baud'], "BAUD", rate)
            self.baud_rate = rate
    baud = property(__get_baud, __set_baud, None, "baud rate")
    
    def __get_mt(self):
        command = "MT"
        return self.parse_result(self.ask(command), self.ptable['get_mt'],self.etable['get_mt'], "MT")    
    mt = property(__get_mt, None, None, "case temperature")
    
    def __get_tx(self):
        self.sendmode="TX"
        return self
    tx = property(__get_tx, None, None, "PG1600D TX")

    def __get_rx(self):
        self.sendmode="RX"
        return self
    rx = property(__get_rx, None, None, "PG1600D TX")

    def __get_key(self):
        command='KEY'
        return self.parse_result(self.ask(command), self.ptable['get_key'],self.etable['get_key'], "KEY")
    def __set_key(self,number):
        command = self.buildCommand("key", number)
        return self.parse_result(self.ask(command), self.ptable['set_key'], self.etable['set_key'])       
    key = property(__get_key, __set_key, None, "module key")
    
    def __get_astm(self):
        command='ASTM'
        return self.parse_result(self.ask(command), self.ptable['get_astm'],self.etable['get_astm'], "astm")
    def __set_astm(self,mode):
        command = self.buildCommand("ASTM", mode)
        return self.parse_result(self.ask(command), self.ptable['set_astm'], self.etable['set_astm'])       
    astm = property(__get_astm, __set_astm, None, "astm")
    
    def __get_echo(self):
        command = "ECHO"
        self.ask(command)
        result = self.ask(command)
        print result
        if (result):
            for line in result.splitlines():
                tokens = line.split(':')
                if (len(tokens) == 2):
                    return tokens[1].strip()
        return None
        
    def __set_echo(self, mode):
        if (mode):
            command = self.buildCommand("ECHO", mode)
            self.ask(command)
            self.echo_mode = mode.upper()
    echo = property(__get_echo, __set_echo, None, "echo on/off")
 

    def __get_ast(self):
        command = "AST"
        return self.parse_result(self.ask(command), self.ptable['get_ast'],self.etable['get_ast'], "AST")
    ast = property(__get_ast, None, None, "alarm status list")

    def __get_mst(self):
        command = "MST"
        return self.parse_result(self.ask(command), self.ptable['get_mst'],self.etable['get_mst'], "MST")
    mst = property(__get_mst, None, None, "module status list")

    def parse_cfg(self,line,matches):
        if (line==[]):
            return None
        else:
            temp=line[0].split()
            print line
            return int(temp[1].strip("'"))

    def parse_cal(self,line,matches):
        if (line==[]):
            return None
        else:
            temp=line[0].split()
            temp[1]=temp[1].strip('"')
            temp[1]=temp[1].strip("'")
            return float(temp[1])

    def recv(self,name):
#        if (self.recv_obj.has_key(name)):
#            pass
#        else:
#            recv_ob=Recv(name, self)
#            self.recv_obj[name]=recv_ob
#        return self.recv_obj[name]
        return Recv(name, self)

    def cfg(self,*value):
        command="cfg"
        for i in value:
            command+=' %s'%str(i)
        return self.parse_result(self.ask(command), self.ptable['get_cfg'],self.etable['get_cfg'],None)
    
    def read_ase_para(self,edfa_num = 1,stage_num = 1):
        cmd = "edfa%sstage"%edfa_num+str(stage_num)+"ase"
        retval = self.ask("cal " + cmd)
        search_result = re.findall(cmd+r'\s+([\-\.\de]+)\s+([\-\.\de]+)\s+([\-\.\de]+)\s+([\-\.\de]+)',retval,re.I)
        par = []
        for item in search_result:
            for p in item:
                par.append(float(p))
        return par
    def get_pump_limit(self):
        limit = []
        retval= self.ask("pump")
        search_result = re.findall(r'pump (\d+) EOL: ([\d\-\.]+|(\-Inf)) mA',retval,re.I)
        for item in search_result:
            if(item[2] != "-Inf"):
                limit.append(float(item[1]))
            else:
                limit.append(None)
        return limit
    def cal(self,*value):
        command="cal"
        for i in value:
            command+=' %s'%str(i)
        return self.parse_result(self.ask(command), self.ptable['get_cal'],self.etable['get_cal'],None)

    def ver(self):
        if (self.ver_obj.has_key(1)):
            pass        
        else:
            ver_ob=Version(self)
            self.ver_obj[1]=ver_ob
        return self.ver_obj[1]   

    def alrm(self, name=None):
        if (self.alrm_obj.has_key(name)):
            pass
        else:
            alrm_ob=Alarm(name, self)
            self.alrm_obj[name]=alrm_ob
        return self.alrm_obj[name]

    def tc(self, num=None):
        if (self.tc_obj.has_key(num)):
            pass        
        else:
            tc_ob=TC(num, self)
            self.tc_obj[num]=tc_ob
        return self.tc_obj[num]

    def poke(self,address):
        if (self.poke_obj.has_key(address)):
            pass
        else:
            self.poke_obj[address]=POKE(address,self)
        return self.poke_obj[address]

    def dump(self,address):
        if (self.dump_obj.has_key(address)):
            pass
        else:
            self.dump_obj[address]=DUMP(address,self)
        return self.dump_obj[address]
#if __name__=='__main__':
    #dut=Module('COM7')
#    instrument("")
    #print dut.ask("ver full")
#    print "next..."
#    print dut.mst
#    print "next..."
#    print dut.ask("alrm ild1dl thr")
#    print "next..."
#    dut.key=1
#    print dut.recv("C:\\Users\\vincent.weng\\Desktop\\testcfg.txt").cfg
#    print dut.mst
#    print dut.recv("C:\\Users\\vincent.weng\\Desktop\\testcfg.txt").cfg128
#    print dut.recv("Y:\\EricGuo\\xmodem\\PG1600_0908dbg1.bin").fw128
#    print dut.mst
#    print dut.ast
#    print dut.recv("Q:\\EricGuo\\xmodem\\PG1600_0908dbg1.bin").fw
#    print dut.mst
#    print dut.ast
#    print dut.recv("Y:\\EricGuo\\xmodem\\PG1600_0908dbg1.bin").fw
#    print dut.recv("C:\\Users\\vincent.weng\\Desktop\\testcfg.txt").cfg128
#    print dut.recv("C:\\Users\\vincent.weng\\Desktop\\testcfg.txt").cfg
#    
#    
#    print dut.mst
#    print dut.ast
#    print dut.recv("Y:\\EricGuo\\xmodem\\PG1600_0908dbg1.bin").fw
#    print dut.recv("C:\\Users\\vincent.weng\\Desktop\\testcfg.txt").cfg128
#    print dut.recv("C:\\Users\\vincent.weng\\Desktop\\testcfg.txt").cfg
#    
#    
#    time.sleep(4)
#    print dut.recv("Q:\\EricGuo\\xmodem\\PG1600_0908dbg1.bin").fw128
#    print dut.mst
#    print dut.ast
#    print dut.ask('^^^^^^^^^^^^^^^^^^^^^^^^^^^^')
#    time.sleep(2)
#    print dut.ask('K')
#    print dut.ask('B')
#    print dut.rx.pump(0).ild
#    print dut.tx.pump(0).ild
    
