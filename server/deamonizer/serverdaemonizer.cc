#include <windows.h>
#include <string>

std::string getCurrentExePath();

int main(void)
{
	STARTUPINFO info={sizeof(info)};
	PROCESS_INFORMATION processInfo;
	std::string cmdline = "C:\\Python36\\python.exe ";
	
	cmdline += getCurrentExePath();
	cmdline += "\\main.py";

	auto ret = CreateProcess(
	  NULL, const_cast<char *>(cmdline.c_str()), NULL, NULL, FALSE,
    CREATE_DEFAULT_ERROR_MODE | CREATE_NO_WINDOW | DETACHED_PROCESS,
    NULL, NULL, &info, &processInfo);

	if (!ret)
		return 1;
	return 0;
}

std::string getCurrentExePath()
{
	char *lpFilename = new char[MAX_PATH];
	GetModuleFileName(NULL, lpFilename, MAX_PATH);

	std::string filename(lpFilename);
	size_t found = filename.find_last_of('\\');
	filename = filename.substr(0, found);

	delete [] lpFilename;
	return filename;
}




