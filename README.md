# pvCam


pvCam camera control is an user interface to control Photometrics scientifics camera 

This software is not associated with Photometrics . Use it at your own risk.

it use PyVCAM library from :
https://github.com/Photometrics/PyVCAM

It can make plot profile and data measurements analysis by using :
https://github.com/julienGautier77/visu
## It is tested :
on win 11 64 bits (AMD64) 
with python 3.9.7 MSC v.1916 with 64 bits anaconda installation
on a retiga 600 camera

## Requirements
*   python 3.x
*   Numpy
*   PyQt6
*   visu 

## Installation
Install PVCAM and PVCAM SDK from : https://www.photometrics.com/support/software-and-drivers#software
Onstall PyVCAM :

Install vs_buildtools https://visualstudio.microsoft.com/fr/downloads/

I window app sdk https://developer.microsoft.com/fr-fr/windows/downloads/windows-sdk/

Donwload PyVcam from : https://github.com/Photometrics/PyVCAM 

Navigate into the directory that contains setup.py and  do python setup.py install


For firewire camera Thesycon driver must be intalled see https://www.photometrics.com/support/software-and-drivers

Install visu :

pip install git+https://github.com/julienGautier77/visu



## Usage
    appli = QApplication(sys.argv)
    
    appli.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    e = PVCAM()  
    e.show()
    appli.exec_()      
