python setup.py build
7zr a -t7z diaboli-ex.7z build\exe.win-amd64-3.4\*
copy /b 7zS.sfx + config.txt + diaboli-ex.7z diaboli-ex.exe
rm diaboli-ex.7z
rmdir /S /Q build
