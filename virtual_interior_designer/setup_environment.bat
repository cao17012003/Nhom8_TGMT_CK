@echo off
echo Activating virtual environment...
call "venv\Scripts\activate.bat"

echo Installing required packages...
pip install django

echo Installing PyTorch and related packages...
pip install torch torchvision

echo Installing computer vision packages...
pip install opencv-python
pip install git+https://github.com/facebookresearch/segment-anything.git

echo Installing LaMa dependencies...
pip install pytorch-lightning==1.9.5
pip install kornia==0.5.0
pip install easydict
pip install scikit-image
pip install scikit-learn
pip install albumentations==0.5.2
pip install hydra-core
pip install matplotlib
pip install tqdm
pip install webdataset

echo Installing additional requirements...
pip install numpy
pip install PyYAML
pip install omegaconf
pip install opencv-python-headless
pip install tabulate
pip install pandas
pip install chumpy

echo Adding lama-with-refiner to Python path...
cd ..
set PYTHONPATH=%PYTHONPATH%;%CD%\lama-with-refiner
cd virtual_interior_designer

echo Environment setup completed.
echo To run the server, use: run_server.bat 