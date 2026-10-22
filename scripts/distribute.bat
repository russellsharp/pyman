poetry run pyinstaller pyman.spec
robocopy .\dist\ c:\bin /np
echo Y | xcopy .\dist\pyman.exe \\fatty\dev