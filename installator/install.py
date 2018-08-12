import os
import sys
from instalib import fetchArg, CompilationException
from shutil import copyfile
from subprocess import call as subprocessCall

print("USP INSTALLER")

# INSTALLATION FLAGS #
INSTALL_PACKAGES = False

errmsg = 'Given path is invalid.'
INSTALLATION_PATH = os.path.abspath(fetchArg('Supply installation dir path: ', errmsg, os.path.isdir))
SHARED_PATH = os.path.abspath(fetchArg('Supply dir from which share files: ', errmsg, os.path.isdir))
DOWNLOAD_DIR_PATH = os.path.abspath(fetchArg('Supply dir which will store downloaded files: ', errmsg, os.path.isdir))
SHARED_NICKNAME = fetchArg('Supply your nickname shared to others in network: ', '', lambda _unused: True)

del errmsg

INSTALLATION_PATH = os.path.join(INSTALLATION_PATH,'USP')

CLIENT_PATH = os.path.join(INSTALLATION_PATH, 'client')

SERVER_PATH = os.path.join(INSTALLATION_PATH, 'server')

# Client files
os.makedirs(CLIENT_PATH, exist_ok=True)

copyfile('../client/client.py', os.path.join(CLIENT_PATH,'client.py'))
copyfile('../client/preferences.conf', os.path.join(CLIENT_PATH,'preferences.conf'))

# Server files
os.makedirs(SERVER_PATH, exist_ok=True)

copyfile('../server/main.py', os.path.join(SERVER_PATH,'main.py'))
copyfile('../server/FileServer.py', os.path.join(SERVER_PATH,'FileServer.py'))
copyfile('../server/sockethelpers.py', os.path.join(SERVER_PATH,'sockethelpers.py'))

# Creating default ini files
CLIENT_SETTINGS = os.path.join(CLIENT_PATH, 'settings')
os.makedirs(CLIENT_SETTINGS, exist_ok=True)

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

daemonizer_dir = os.path.join('..','server','daemonizer')

if sys.platform in ('linux', 'cygwin'):
    copyfile(os.path.join(daemonizer_dir, 'serverdaemonizer.sh'), os.path.join(SERVER_PATH,'serverdeamonizer.sh'))
elif sys.platform == 'win32':
    print("Comapiling daemonizer . . . ", flush=True)
    if subprocessCall(['make'], cwd=daemonizer_dir) != 0:
        raise CompilationException('Failed to compile server daemonizer from source!')
    print("Compilation successed")
    copyfile(os.path.join(daemonizer_dir, 'serverdaemonizer.exe'), os.path.join(SERVER_PATH, 'serverdeamonizer.exe'))
else:
    print("WARNING: deamonizer for server not supported for your platform / os.")
