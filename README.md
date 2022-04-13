# pvCam


pvCam camera control is an user interface to control Photometrics scientifics camera 

This software is not associated with Photometrics . Use it at your own risk.

it use PyVCAM library from :
https://github.com/Photometrics/PyVCAM

It can make plot profile and data measurements analysis by using :
https://github.com/julienGautier77/visu

## Requirements
*   python 3.x
*   Numpy
*   PyQt5
*   visu 2022.04

## Installation
install PVCAM and PVCAM SDK from : https://www.photometrics.com/support/software-and-drivers#software
install PyVCAM from https://github.com/Photometrics/PyVCAM

install visu :

pip install git+https://github.com/julienGautier77/visu



## Usage
    appli = QApplication(sys.argv)
    
    appli.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    e = PVCAM()  
    e.show()
    appli.exec_()      
