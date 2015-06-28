from cx_Freeze import setup, Executable
import os
import sys
includefiles = [('locations/__init__.py', 'locations/__init__.py')]
from main import VERSION

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="diaboli-ex",
    version=VERSION,
    description="Diabloi Ex",
    options={"build_exe": {
        "includes": "PyQt5.QtPrintSupport",
        'include_files': includefiles
        }
    },
    executables=[Executable("main.py", base=base)],
)

config = """;!@Install@!UTF-8!
Title="Diaboli Ex v%s"
BeginPrompt="Do you want to install Diaboli Ex v%s?"
RunProgram="build\exe.win-amd64-3.4\main.exe"
;!@InstallEnd@!""" % (VERSION, VERSION)
with open('config.txt', 'w') as f:
    f.write(config)
