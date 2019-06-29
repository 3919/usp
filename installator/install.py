#!/usr/bin/python3
import os
import sys
from instalib import fetchPath, CompilationException
from shutil import copyfile
from subprocess import call as subprocessCall
from pathlib import Path

print("USP INSTALLER")

# INSTALLATION FLAGS #
INSTALL_PACKAGES = False

errmsg = 'Given path is invalid.'
INSTALLATION_PATH = os.path.expanduser(fetchPath('Supply installation dir path: ', errmsg, os.path.isdir))
SHARED_PATH = os.path.expanduser(fetchPath('Supply dir from which share files: ', errmsg, os.path.isdir))
DOWNLOAD_DIR_PATH = os.path.expanduser(fetchPath('Supply dir which will store downloaded files: ', errmsg, os.path.isdir))
SHARED_NICKNAME = fetchPath('Supply your nickname shared to others in network: ', '', lambda _unused: True)

del errmsg

INSTALLATION_PATH = os.path.join(INSTALLATION_PATH,'USP')

CLIENT_PATH = os.path.join(INSTALLATION_PATH, 'client')

SERVER_PATH = os.path.join(INSTALLATION_PATH, 'server')

# Client files
os.makedirs(CLIENT_PATH, exist_ok=True)

copyfile('../client/client.py', os.path.join(CLIENT_PATH,'client.py'))
copyfile('../client/helpers.py', os.path.join(CLIENT_PATH,'helpers.py'))
copyfile('../client/preferences.conf', os.path.join(CLIENT_PATH,'preferences.conf'))

# Server files
os.makedirs(SERVER_PATH, exist_ok=True)

copyfile('../server/main.py', os.path.join(SERVER_PATH,'main.py'))
copyfile('../server/FileServer.py', os.path.join(SERVER_PATH,'FileServer.py'))
copyfile('../server/sockethelpers.py', os.path.join(SERVER_PATH,'sockethelpers.py'))

# Creating default ini files
CLIENT_SETTINGS = os.path.join(CLIENT_PATH, 'settings')
os.makedirs(CLIENT_SETTINGS, exist_ok=True)

open(os.path.join(CLIENT_SETTINGS,"hosts.txt" ), "w" ).close()

SERVER_SETTINGS = os.path.join(SERVER_PATH, 'settings')
os.makedirs(SERVER_SETTINGS, exist_ok=True)

SERVER_LOGS = os.path.join(SERVER_PATH, 'logs')
os.makedirs(SERVER_LOGS, exist_ok=True)

CLIENT_SETTINGS = os.path.join(CLIENT_SETTINGS, 'settings.ini')
SERVER_SETTINGS = os.path.join(SERVER_SETTINGS, 'settings.ini')

with open(CLIENT_SETTINGS, 'w') as f:
    f.write('[DOWNLOAD]\n')
    f.write('folder_path={} \n'.format(DOWNLOAD_DIR_PATH))

with open(SERVER_SETTINGS, 'w') as f:
    f.write('[main]\n')
    f.write('shared_path={} \n'.format(SHARED_PATH))
    f.write('shared_name={} \n'.format(SHARED_NICKNAME))

del CLIENT_SETTINGS
del SERVER_SETTINGS
del SERVER_LOGS

DAEMONIZER_DIR = os.path.join('..','server','daemonizer')
UTILS_DIR = os.path.join('..','utils')
USER_HOME_DIR = str(Path.home())
USER_BIN_DIR = os.path.join(USER_HOME_DIR, '.local', 'bin')

if sys.platform in ('linux', 'cygwin'):
    copyfile(os.path.join(DAEMONIZER_DIR, 'serverdaemonizer.sh'), os.path.join(SERVER_PATH,'serverdeamonizer.sh'))
    copyfile(os.path.join(UTILS_DIR, 'usp-remove'), os.path.join(USER_BIN_DIR, 'usp-remove'))
    copyfile(os.path.join(UTILS_DIR, 'usp-share'), os.path.join(USER_BIN_DIR, 'usp-share'))
elif sys.platform == 'win32':
    print("Comapiling daemonizer . . . ", flush=True)
    if subprocessCall(['make'], cwd=DAEMONIZER_DIR) != 0:
        raise CompilationException('Failed to compile server daemonizer from source!')
    print("Compilation successed")
    copyfile(os.path.join(DAEMONIZER_DIR, 'serverdaemonizer.exe'), os.path.join(SERVER_PATH, 'serverdeamonizer.exe'))
else:
    print("WARNING: deamonizer for server not supported for your platform / os.")

print("Installation complete.")
