
import socket,threading
import sys
import time
import netifaces
import random
import struct
import hashlib
import configparser 

class SocketError(Exception):
    pass
class parseError(Exception):
    pass
class client:
    def __init__(self):
        
        PORT = 53025   
        if len(sys.argv) == 2:
            PORT = int(sys.argv[1] )
        # main socket   
        self.sock  =  socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # keep information about avaliable hosts and port
        self.usersDescriptor = {
            "HOST" :[],    
            "PORT" : PORT
        }
        self.filePath = ""
        # keep user config to download files
        self.userConfig ={}
        # keep user files
        self.userFiles = {}

    def _run(self):
        command = ""
        self._handleCommand("SCAN")
        self._handleCommand("HELP")
        self._handleCommand("SETTINGS init")
        self.filePath = self.userConfig["folder_path"] +\
                        self.userConfig["folder_name"] +"/"
        
        while True:
            command = input("Type command : ")
            command = command 
            self._handleCommand(command)

        return

    def _handleCommand(self, command):
        command = command.replace(",", " ")
        command = command.split(" ")
        command[0] = command[0].upper()

        cmd = {
            "SCAN" : self._scanNet, 
            "GET" : self._getFile,
            "GETLIST" : self._getFileList,
            "SHOWFILES" : self._listFiles,
            "HELP" : self._printHelp,
            "SETTINGS" : self._manageSettings
        }
        if command[0] not in cmd:
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

            #  append device prefered by user saved in file
            preferredDevices = list( filter(None,configFile) )
            netmask = ''
            ip_addr = ''

    
            # if user don't have config file, let him choose devices  
            if len(preferredDevices) == 0:
                avaliabledevices = netifaces.interfaces()
                print("List of avaliable devices: ")
                for key, value in enumerate(avaliabledevices):
                    print("{} {}".format(key,value))
                
                devId = int(input("Choose device: "))
                preferredDevices.append(avaliabledevices[devId])

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
        

        self._handleCommand("GETLIST")

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

    def _getFile(self, command):

        if len(self.usersDescriptor["HOST"]) == 0:
            print("No active users were found. Rescan your network")
            return False;
        
        reqestedFiles = []
        reqestedUsers = []
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

        asterix_in_file = False
        asterix_in_user = False
        
        #  it has to be at least one file in command and if '*' occured it can't be more files as args
        if len(FILES) == 0  or  len(FILES) > 1 and '*' in FILES:
            print("Incorrect syntax ")
            self._handleCommand("HELP")
            return False
        # same rules as file 
        if len(USERS) == 0 or len(USERS) > 1 and  '*' in USERS:
            print("Incorrect syntax ")
            self._handleCommand("HELP")
            return False

        # check for wildcard sytax in command
        if '*' in FILES:
            asterix_in_file = True;
        if '*' in USERS:
            asterix_in_user = True;
        
        # get users
        if asterix_in_user:
            for usr in self.usersDescriptor[ "HOST" ] :
                reqestedUsers.append(usr[ "IP" ]) 
        else :
            for i,usr in enumerate(USERS) :
                usrIdx = self._searchUsr(usr) 
                if usrIdx == -1:
                    continue
                print(i)          
                reqestedUsers.append(self.usersDescriptor[ "HOST" ][usrIdx][ "IP" ] )  
            

        if asterix_in_file :
            # get all files form user
             for usr in self.usersDescriptor["HOST"]:
                for f in self.userFiles[usr["IP"]]:
                    reqestedFiles.append(f)
        else:# get requested files
            reqestedFiles = FILES 

        

        # print(reqestedFiles, reqestedUsers)
        for file in reqestedFiles:
            for usr in reqestedUsers:
                # print(file,usr
                if file in self.userFiles[usr]:
                    self._downloadFile(file,usr)
        

    def _searchUsr(self, usr):
        for i in range(len(self.usersDescriptor["HOST"])):
            if usr == self.usersDescriptor["HOST"][i]["NICK"]:
                return i
        return -1
    

    def _downloadFile(self, fileName, ip):
        fileDownloadPath = filePath + fileName
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        self.sock.connect((ip, self.usersDescriptor["PORT"] ))

        self.sock.sendall(b"GET ")
        self.sock.sendall(bytes(fileName, "utf-8") )
        self.sock.sendall(b'\n')
        
        fileSize = struct.unpack("<Q", self.sock.recv(8))[0]
        if fileSize == 0 :
            print("FILE NOT FOUND")
            return False

        sha256Sign = self.sock.recv(1 * 32)
        print(sha256Sign)
        file = []
        dataLeft = fileSize

        print("Downloadin file: {}, from :{} \n".format(fileSize,ip) )
        with open(fileDownloadPath, "wb" )  as f:
            while dataLeft > 0:
                data =  self.sock.recv(dataLeft)
                file.extend(data)
                dataLeft -= len(data)

            file = bytearray(file)                
            if hashlib.sha256(file).digest() != sha256Sign :
                print ("SHA256 Incorrect")
                return False      

            f.write(bytearray(file) )

        self.sock.close()
        return True

    def _getFileList(self,command):
    
        if len(self.usersDescriptor["HOST"]) == 0:
            print("No active users were found. Rescan your network")
            return False;

        reqestedUsers = []
        # if user want to get only selected hosts files
        if len(command) > 1:
                command = command[1:]
                for usr in command:
                    usrIdx = self._searchUsr(usr)
                    if usrIdx == -1:
                        continue
                    reqestedUsers.append(self.usersDescriptor["HOST"][usrIdx])
        else: # get all avaliable hosts files
            reqestedUsers = self.usersDescriptor["HOST"] 
        self.userFiles = {}

        for i, host in enumerate(reqestedUsers):
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if host in self.usersDescriptor["HOST"]:
                self.sock.connect( (host["IP"], self.usersDescriptor["PORT"] ) )
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.sock.send(bytes("GETLIST\n", "UTF-8") )
                byteRead = ""
                fileName = ""
                
                while byteRead != b'\n':
                    byteRead = self.sock.recv(1)

                    if byteRead == b'\0' :
                        
                        if host["IP"] not in self.userFiles:
                            self.userFiles.update({ host["IP"] : [ ] })
                        else:
                            self.userFiles[host["IP"]].append(fileName)  
                        fileName = ""
                    else:
                        fileName += byteRead.decode("utf-8")
                
            self.sock.close()
        self._handleCommand("SHOWFILES")
        return True
    
    def _listFiles(self, command):

        print("Avaliable files: ")
        
        reqestedUsers = []
        # if user want to display only selected hosts files
        if len(command) > 1:
                command = command[1:]
                for usr in command:
                    usrIdx = self._searchUsr(usr)
                    if usrIdx == -1:
                        continue
                    reqestedUsers.append(self.usersDescriptor["HOST"][usrIdx])
        else: # display all avaliable hosts files
            reqestedUsers = self.usersDescriptor["HOST"]

        for usr in reqestedUsers:
            if usr["IP"] not in self.userFiles:
                continue
            print("IP :  {}  NICK : {}".format(usr["IP"],usr['NICK']) )    
            for f in self.userFiles[usr["IP"]]:
                print("   -- ", f)

    def _printHelp(self, command):
        print("Avalaiable commands : ")
        print(" --SCAN         -- scan network for active servers")
        print(" --SHOWFILES    -- list all files avaliable for download")
        print("     --*--         you can also specify host Ex. SHOWFILES user1") 
        print(" --GETLIST      -- get file list from all active users ")
        print("     --*--         you can also specify host Ex. GETLIST user1") 
        print(" --GET * from * -- download files from users.")
        print("     --*--         You can specify files and user Ex.") 
        print("     --*--         get file1 file2 from user1 user2...")
        print(" --SETTINGS     -- manage your settings ")
        print("     --*--         /s - show settings")
        print("     --*--         /c - change  settings")

    def _manageSettings(self,command):
        parameters = command[1:]
        
        config = configparser.ConfigParser()
        config.read('./settings')
        try:
            if "DOWNLOAD" in config:
                self.userConfig["folder_path"] = config["DOWNLOAD"]["folder_path"]
                self.userConfig["folder_name"] = config["DOWNLOAD"]["folder_name"]
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
            with open("settings", "w") as f:
                config.write(f)
        else:
            print("Wrong parameters")


def main():
    instance = client()
    try:
        instance._run()
    except KeyboardInterrupt:
        print("\nLeaving...")
        sys.exit(0)

if __name__ == "__main__":
    main()