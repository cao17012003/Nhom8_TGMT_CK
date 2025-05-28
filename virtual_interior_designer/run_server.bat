@echo off
echo Activating virtual environment...
call "venv\Scripts\activate.bat"

echo Setting Python path to include lama-with-refiner and global Python libraries...
cd ..
set PYTHONPATH=%PYTHONPATH%;%CD%\lama-with-refiner;C:\Users\cao17\AppData\Local\Programs\Python\Python311\Lib\site-packages
cd virtual_interior_designer

echo Verifying webdataset installation...
python -c "import sys; print('Python path:'); print(sys.path); print('Checking for webdataset:'); try: import webdataset; print('webdataset is installed'); except ImportError: print('webdataset is NOT installed')"

echo Starting Django server...
python manage.py runserver 