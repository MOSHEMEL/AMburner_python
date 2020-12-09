source env/Scripts/activate
pyinstaller --hidden-import=serial --hidden-import=requests --onefile --add-binary "ARmentaSmall.png;." --paths env\Lib\site-packages AMburner.py
pause
