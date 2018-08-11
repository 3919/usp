import time
print("")
for i in range(10):
	hashStr = "#"*i
	print( "Progress: (" + str(i)+"/10)" + hashStr + "\r" , end='', flush=True)
	time.sleep(1)

print( "\033[2K", sep='', end='', flush=True)
print("File Dowloaded")