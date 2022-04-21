# pvCam


pvCam camera control is an user interface to control Photometrics scientifics camera 

This software is not associated with Photometrics . Use it at your own risk.

it use PyVCAM library from :
https://github.com/Photometrics/PyVCAM

It can make plot profile and data measurements analysis by using :
https://github.com/julienGautier77/visu
## It is tested :
on win 11 64 bits (AMD64) 
with python 3.9.7 MSC v.1916 with anaconda installation
on a retiga 600 camera

## Requirements
*   python 3.x
*   Numpy
*   PyQt5
*   visu 2022.04

## Installation
install PVCAM and PVCAM SDK from : https://www.photometrics.com/support/software-and-drivers#software
install PyVCAM :



donwload PyVcam from : https://github.com/Photometrics/PyVCAM 
Navigate into the directory that contains setup.py and run python setup.py install

install vs_buildtools https://visualstudio.microsoft.com/fr/downloads/
install window app sdk https://developer.microsoft.com/fr-fr/windows/downloads/windows-sdk/

install visu :
pip install qdarkstyle (https://github.com/ColinDuquesnoy/QDarkStyleSheet.git)
pip install pyqtgraph (https://github.com/pyqtgraph/pyqtgraph.git)
pip install git+https://github.com/julienGautier77/visu



## Usage
    appli = QApplication(sys.argv)
    
    appli.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    e = PVCAM()  
    e.show()
    appli.exec_()      
