
import socket,threading
import sys, os
import time
import netifaces
import random
import struct
import hashlib
import configparser 
import re

if os.name == "nt":
    import winreg as wr

class SocketError(Exception):
    pass
class parseError(Exception):
    pass
class client:
    def __init__(self):
        
        PORT = 53025   
        
        # main socket   
        self.sock  =  socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # keep information about Available hosts and port
        self.usersDescriptor = {
            "HOST" :[],    
            "PORT" : PORT
        }
        self.filePath = ""
        # keep user config to download files
        self.userConfig ={}
        # keep user files
        self.userFiles = {}

        self._handleCommand("SETTINGS init")
     
        self.filePath = self.userConfig["folder_path"]

    def _run(self, command):
        
        self._handleCommand(command)
        return True
    
     
    def _handleCommand(self, command):
        command = command.replace(","," ")
        command = command.split(" ")
        command[0] = command[0].upper()

        cmd = {
            "SCAN" : self._scanNet, 
            "GET" : self._getFile,
            "SHOWFILES" : self._listFiles,
            "HELP" : self._printHelp,
            "SETTINGS" : self._manageSettings,
            "HOSTS" : self._loadLastActiveHosts,
            "GETALL" : self._getAllFiles
        }

        if command[0] not in cmd:
            self._printHelp("init")
            return False 
        
        return cmd[command[0]](command)

    def _scanNet(self, command):
        configFile = ""
        # erase user before new searching
        self.usersDescriptor["HOST"] = []

        with open("preferences.conf") as f:
            configFile = f.read()
            configFile = configFile.split("\n")
            for i,line in enumerate(configFile):
                line = line.replace(' ','')
                idx = line.find('#')
                if idx == -1:
                    idx = len(line)                
                configFile[i] = line[:idx]
            availabledevices = netifaces.interfaces()

            #  append device prefered by user saved in file
            preferredDevices = list( filter(None,configFile) )
            netmask = ''
            ip_addr = ''

            # stupid translation on windows when user specify preferredDevices
            if os.name == "nt":
                if len(preferredDevices) != 0:
                    iface_names = self.get_connection_names_from_reg(availabledevices)
                    for i, name in enumerate(preferredDevices):
                        for j,iface in enumerate(iface_names):
                            if iface == name:
                                preferredDevices[i] = availabledevices[j]
            # if user don't have config file, let him choose devices  
            if len(preferredDevices) == 0:
                
                print("List of avaliable devices: ")
                for key, value in enumerate(availabledevices):
                    if os.name == "nt":
                        print("{} {}".format(key,self._get_connection_name_from_reg(value)))
                    else: 
                        print("{} {}".format(key,value))
                
                devId = int(input("Choose device: "))
                preferredDevices.append(availabledevices[devId])

            #  get netmask and addres of choosen eth device 
            for device in preferredDevices:
                    try:
                        netmask = netifaces.ifaddresses(device)[netifaces.AF_INET][0]['netmask']
                        ip_addr = netifaces.ifaddresses(device)[netifaces.AF_INET][0]['addr']
                    except:
                        print("Device not connected")
                        return False

            # convert mask to number
            if netmask != '' and ip_addr != '':
                netmask = self._netDecode(netmask)
                ip_addr = self._netDecode(ip_addr)
                
                ip_start_scan_address = netmask & ip_addr
                #  0xffffffff <- is biggest mask in 32 bits  
                amount_addresses_to_scan = 0xffffffff - netmask
                
                self._scan(ip_start_scan_address, amount_addresses_to_scan )

        return True
# Unpack net items to 32 bit value
    def _netDecode(self, NetItem):
        NetItem = NetItem.split('.')
        NetItem = ( int(NetItem[0]) << 24 ) | ( int(NetItem[1]) << 16 ) | ( int(NetItem[2]) << 8 ) | ( int(NetItem[3]) )
        
        return NetItem

# pack net items to string net value
    def _netEncode(self, NetItem):
        data = []        
        for i in range(3,-1,-1):
            data.append( (NetItem >>(8* i)) & 0xff  )

        return "".join([str(chunk)+'.' for chunk in data] )[:-1]


    def TCP_connect(self, ip, delay):
        TCPsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        TCPsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        TCPsock.settimeout(delay)
        try:
            TCPsock.connect((ip, self.usersDescriptor["PORT"] ))
            nick = self._authenticateUser(TCPsock)
            if nick != None:
                self.usersDescriptor["HOST"].append({"IP" : ip, "NICK" : nick })
                print("Connected")
        except OSError:
            pass
            

#  scan local network and append new active users
    def _scan(self, ip_begin, address_amount ):
        ip_begin_str = ""
        threads = []
        for i in range(address_amount):
            ip_begin_str = self._netEncode(ip_begin)
            # // create thread to connect with speciffied ip
            t = threading.Thread(target=self.TCP_connect, args=(ip_begin_str, 1) )
            threads.append(t)
            t.start();
            # get new ip addres
            ip_begin+=1
        # 
        for i in range(len(threads)):
            threads[i].join()
        
        self._showActiveUsers()
        self._saveActiveHosts()
        

    def _authenticateUser(self, sock):
       
        sock.sendall(b"PING\n")
        # read signature 
        expectedString = "PONG_USP"      
        ret_value = sock.recv( len(expectedString) )
        # and user credits
        user_account_name = ""
        readCharacter = sock.recv(1) # read space between signature and nickname
        
        while True:
            readCharacter = sock.recv(1)
            if readCharacter == b'\n':
                break;
            user_account_name += chr(readCharacter[0]) 
            
        if expectedString == ret_value.decode("utf-8")  and len(user_account_name) > 0 :
            return user_account_name 
        else:
            return  None

        #  Posible options:
        #  GET * from *                                      -- get all files from all users
        #  GET * from user1, user2                     -- get * from specified some users
        #  GET file1, file2.. from *                        -- get some files from all users
        #  GET file1, file2.. from user1 user1 user2.. -- get some files from some users
    def _getAllFiles(self,command):
        self._getFile(["GET", "*", command[1], command[2] ] )

    def _getFile(self, command):
        self._loadLastActiveHosts(command)
        FILES = []
        USERS = []
        FILES = command[1:]
        
        for idx, item in enumerate(command):
            if item.upper() == "FROM":
               FILES = command[1 : idx]
               FILES = list( filter(None,FILES))
               USERS = command[(idx+1):]
               USERS = list( filter(None,USERS))
               break;

        #  it has to be at least one file in command and if '*' occured it can't be more files as args
        if len(FILES) == 0  or  len(FILES) > 1 and '*' in FILES:
            print("Incorrect syntax ")
            self._handleCommand("HELP")
            return False
        
        if len(USERS) != 1:
            print("You have to pass exacly one user");
            exit(1)
        
        USERS = self._translateAddress(USERS)
        if len(USERS) != 1:
            print("None of last active users has such nickname")
            exit(1)

        for file in FILES:
            self._downloadFile(file,USERS[0])
        
    def _searchUsr(self, usr):
        for i in range(len(self.usersDescriptor["HOST"])):
            if usr == self.usersDescriptor["HOST"][i]["NICK"]:
                return i
        return -1
    

    def _downloadFile(self, fileName, ip):
        if fileName.rfind('/') != -1:
            fileName_2 = fileName[fileName.rfind('/')+1:]
        else:
            fileName_2 =  fileName
        fileDownloadPath = self.filePath + "/" + fileName_2
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        self.sock.connect((ip, self.usersDescriptor["PORT"] ))

        self.sock.sendall(b"GET ")
        self.sock.sendall(bytes(fileName, "utf-8") )
        self.sock.sendall(b'\n')
        fileSize = self.sock.recv(8)
        if fileSize == b'':
            print("FILE NOT FOUND")
            return False
        fileSize = struct.unpack("<Q",fileSize )[0]

        sha256Sign = self.sock.recv(1 * 32)
        file = []
        dataLeft = fileSize
        dataRead = 0;
        print("Downloadin file: {}, from :{} \n".format(fileDownloadPath,ip) )
        with open(fileDownloadPath, "wb+" )  as f:
            while dataLeft > 0:
                data =  self.sock.recv(dataLeft)
                if len(data) == 0:
                    break
                f.write( bytearray(data) )
                dataLeft -= len(data)
                dataRead  += len(data) 
                hashAmount = int((dataRead/fileSize)*70)
                hashStr = "#"*hashAmount
                spaceStr = " "*(70-hashAmount)
                print( "Progress: (" + str( dataRead ) + "/" + str(fileSize) +") |" + hashStr + spaceStr + "| "+ str(int(dataRead/fileSize)*100) + "%" , end='\r', flush = True)
                time.sleep(0.8)

            
            print("\nValidating downloaded file...")
            f.seek(0,0)
            file.extend(f.read() )              
            if hashlib.sha256(bytes(file) ).digest() != sha256Sign :
                print ("\nSHA256 Incorrect\nRemoving file : ", fileDownloadPath)
                os.remove( fileDownloadPath )
                return False      
            else:
                print("\nFile Dowloaded")

            

        self.sock.close()
        return True

    def _translateAddress(self, users):
        ipTable = []
        for ip in users:

            if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip) != None:
                ipTable.append(ip)
            else:
                usrIdx = self._searchUsr(ip)
                if usrIdx != -1:
                    ipTable.append( self.usersDescriptor["HOST"][usrIdx]["IP"] )

        return ipTable;

    def _getFileList(self,command):
        
        reqestedUsers = command[1:]
        ipTable = []
        if "*" in reqestedUsers:
            for usr in self.usersDescriptor["HOST"]:
                ipTable.append(usr["IP"])
        else:
            ipTable = self._translateAddress(reqestedUsers)
            
        for i, host in enumerate(ipTable):
            try:
                print(host)
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.sock.connect( (host, self.usersDescriptor["PORT"] ) )
                self.sock.send(bytes("GETLIST\n", "UTF-8") )
                byteRead = ""
                fileName = ""
            
                while byteRead != b'\n':
                    byteRead = self.sock.recv(1)

                    if byteRead == b'\0':
                        if host not in self.userFiles:
                            self.userFiles.update({ host : [ ] })
                        else:
                            self.userFiles[host].append(fileName)  
                        fileName = ""
                    else:
                        fileName += byteRead.decode("utf-8")
                    
                self.sock.close()
            except(OSError):
                errMessage = "Host: " + host + " unreachable";
                raise SocketError(errMessage)
        return ipTable
    
    def _listFiles(self, command):
        
        if len(command) == 1:
            command.append("*")

        self._loadLastActiveHosts(command)
        ipTable = self._getFileList(command)

        print("Available files: ")
        for ip in ipTable:
            print("IP :  {} ".format( ip ) )    
            for f in self.userFiles[ip]:
                print("   -- ", f)

    def _printHelp(self, command):
        print("Available commands : ")
        print(" --SCAN               -- rescan network for active servers")
        print(" --HOSTS              -- show last active servers")
        print(" --SHOWFILES          -- request last active servers for available files")
        print("     --*--               you can also specify host ")
        print("     --*--               Ex.SHOWFILES [user1/ip_1,user2/ip_2...]") 
        print(" --GETALL from user   -- get all files from user (inactive)")
        print(" --GET file from user -- download files from users.")
        print("     --*--               You can specify files and user") 
        print("     --*--               It can be only one user")
        print("     --*--               Ex.get file1 file2 from user1")
        print(" --SETTINGS              -- manage your settings ")
        print("     --*--               /s - show settings")
        print("     --*--               /c - change  settings")
        exit(1)

    def _manageSettings(self,command):
        parameters = command[1:]
        
        config = configparser.ConfigParser()
        config.read('./settings/settings.ini')
        try:
            if "DOWNLOAD" in config:
                self.userConfig["folder_path"] = config["DOWNLOAD"]["folder_path"]
        except:
            print("Config should consist 'path' and 'fname' labels ")
            raise parseError("Error while parsing settings file")
            
        if "init" in parameters:
            return
        if '/s' in parameters:
            print("Download settings: ")
            for key in self.userConfig:
                print(key,": ", self.userConfig[key])

        elif '/c' in parameters:
            print("Type new settings ( Empty line to left old value )")
            for key in self.userConfig:
                value = input("{}: ".format(key))
                
                if value is "":
                    continue
                self.userConfig[key] = value
            
            config["DOWNLOAD"] =  self.userConfig
            with open("./settings/settings.ini", "w") as f:
                config.write(f)
        else:
            print("Wrong parameters")

    def _saveActiveHosts(self):
        with open("./settings/hosts.txt","w") as f:
            f.write("# This file conatins all previously found hosts\n")
            f.write("# The hosts may be not actual\n")
            f.write("# Run client with SCAN argument to get currently active servers\n")
            f.write("[HOSTS]\n")
            for user in self.usersDescriptor["HOST"]:
                f.write("{}={}\n".format(user["IP"],user['NICK']) )  
   
    def _loadLastActiveHosts(self, command):
        config = configparser.ConfigParser()
        config.read("./settings/hosts.txt")
        print("Last active hosts : ")
        try:
            if "HOSTS" in config:
                for key in config["HOSTS"]:
                    self.usersDescriptor["HOST"].append( { "IP" : key, "NICK" : config["HOSTS"][key] } )
                    print("IP :  {}  NICK : {}".format(key ,config["HOSTS"][key] ) )  
        except:
            raise parseError("Error while parsing host file")
        
        

    def _showActiveUsers(self):
        print("Available hosts: ")
        for user in self.usersDescriptor["HOST"]:
            print("IP :  {}  NICK : {}".format(user["IP"],user['NICK']) )  

    if os.name == "nt":
        def _get_connection_name_from_reg(self, regValue):
            reg = wr.ConnectRegistry(None, wr.HKEY_LOCAL_MACHINE)
            reg_key = wr.OpenKey(reg, r'SYSTEM\CurrentControlSet\Control\Network\{4d36e972-e325-11ce-bfc1-08002be10318}')
            try:
                reg_subkey = wr.OpenKey(reg_key, regValue + r'\Connection')
                deviceName = wr.QueryValueEx(reg_subkey, 'Name')[0]
                return str(deviceName)
            except:
                return "( Unknown )"
        def get_connection_names_from_reg(self, iface_guids):
            iface_names = ['(unknown)' for i in range(len(iface_guids))]
            reg = wr.ConnectRegistry(None, wr.HKEY_LOCAL_MACHINE)
            reg_key = wr.OpenKey(reg, r'SYSTEM\CurrentControlSet\Control\Network\{4d36e972-e325-11ce-bfc1-08002be10318}')
            for i in range(len(iface_guids)):
                try:
                    reg_subkey = wr.OpenKey(reg_key, iface_guids[i] + r'\Connection')
                    iface_names[i] = wr.QueryValueEx(reg_subkey, 'Name')[0]
                except FileNotFoundError:
                    pass
            return iface_names         

def main():
    instance = client()
    try:
        instance._run(" ".join(sys.argv[1:]) )
    except KeyboardInterrupt:
        print("\nLeaving...")
        sys.exit(0)

if __name__ == "__main__":
    main()
