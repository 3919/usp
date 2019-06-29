import os
import shutil
import random

# Length of hash that is generated when directory with name ~/.usp_old already
# exists but copy of ~/usp dir must be done.
HASH_LENGTH_ON_COPY_BITS = 32

# Amount of attempts that will be done with generating random hash for
# ~/.usp_copy_<hash> when attempting to create copy of exisiting ~/usp directory
HASH_GENERATION_ATTEMPTS = 100

USP_INFO_DIR = os.path.expanduser('~/.usp')
USP_INFO_FILE = os.path.join(USP_INFO_DIR, 'info')

def fetchPath(msg, errmsg, verify):
    isOk = False

    arg = input(msg)
    isOk = verify(os.path.expanduser(arg))

    while not isOk:
        print(errmsg)
        arg = input(msg)
        isOk = verify(os.path.expanduser(arg))

    return arg

# Creates directory which contains files with general info about currently installed usp instance
def createGlobalInfoDirectory(INSTALLATION_PATH):
    if os.path.isdir(USP_INFO_DIR):
        opt = ''
        while 1:
            opt = input('WARNING: ~/.usp directory already exists! Do you want to overwrite it? (Y/N): ')

            if opt == 'N':
                print('Installation cannot proceed then ;(. Aborting.')
                exit(-1)

            # If user wants to overwrite .usp directory its make copy.
            # First check ~/.usp_old, if this dir name is not free neither
            # generate random hash and attach to ~/.usp_old and then try for 100 times
            # if any of random generated filenames already exists then exit.
            if opt == 'Y':
                usp_copy_dir = USP_INFO_DIR + '_old'

                if not os.path.isdir(usp_copy_dir):
                  shutil.move(USP_INFO_DIR, usp_copy_dir)
                  break

                hash = ''
                attempts = 0
                while os.path.isdir(usp_copy_dir + '_' + hash) and attempts < 100:
                    hash = str(random.getrandbits(HASH_LENGTH_ON_COPY_BITS))
                    attempts += 1

                if attempts == HASH_GENERATION_ATTEMPTS:
                    print(f'Tried to make copy of ~/.usp directory but while'
                          f'generating random file name for it failed for {attempts} times.')
                    exit(-2)

                shutil.move(USP_INFO_DIR, usp_copy_dir + '_' + hash)
                os.mkdir(USP_INFO_DIR)
                break

    else:
      os.mkdir(USP_INFO_DIR)

    with open(USP_INFO_FILE, 'w+') as infofile:
        infofile.write(f'USP_INSTALL_DIR={INSTALLATION_PATH}\n')


class CompilationException(Exception):
    pass

