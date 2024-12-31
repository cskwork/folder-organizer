@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

:: Download MeCab installer
echo Downloading MeCab installer...
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/ikegami-yukino/mecab/releases/download/v0.996.2/mecab-64-0.996.2.exe' -OutFile 'mecab-installer.exe'"

:: Run MeCab installer
echo Installing MeCab...
start /wait mecab-installer.exe /S

:: Download MeCab dictionary
echo Downloading MeCab dictionary...
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/ikegami-yukino/mecab/releases/download/v0.996.2/mecab-ko-dic-2.1.1-20180720.tar.gz' -OutFile 'mecab-ko-dic.tar.gz'"

:: Extract dictionary
echo Extracting dictionary...
tar -xf mecab-ko-dic.tar.gz -C "C:\Program Files\MeCab\dic"

:: Clean up
del mecab-installer.exe
del mecab-ko-dic.tar.gz

echo MeCab installation completed!
pause
