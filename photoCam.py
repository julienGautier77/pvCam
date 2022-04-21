# -*- coding: utf-8 -*-
"""
Created on Mon Dec 31 23:14:46 2001
on conda prompt 

pip install qdarkstyle (https://github.com/ColinDuquesnoy/QDarkStyleSheet.git)
pip install pyqtgraph (https://github.com/pyqtgraph/pyqtgraph.git)
pip install visu
install PVCAM and PVCAM sdk
donwload PyVcam from : https://github.com/Photometrics/PyVCAM 
avigate into the directory that contains setup.py and run python setup.py install
install vs_buildtools https://visualstudio.microsoft.com/fr/downloads/
install window app sdk https://developer.microsoft.com/fr-fr/windows/downloads/windows-sdk/
@author: juliengautier
modified 2019/08/13 : add position RSAI motors
"""

__version__='2020.6'
__author__='julien Gautier'
version=__version__

from PyQt5.QtWidgets import QApplication,QVBoxLayout,QHBoxLayout,QWidget,QPushButton,QDockWidget,QMenu
from PyQt5.QtWidgets import QComboBox,QSlider,QLabel,QSpinBox,QDoubleSpinBox,QGridLayout,QToolButton,QInputDialog
from pyqtgraph.Qt import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5 import QtGui 
import sys,time
import numpy as np
import pathlib,os
import pyqtgraph as pg 

#
#except:
#    print ('No visu module installed : pip install visu' )
try :
    from pyvcam import pvc 
    from pyvcam.camera import Camera   
    from pyvcam import constants as const 
except:
    print('can not control ropper camera: cameraClass or picam_types module is missing')   


import qdarkstyle
# from visu import SEE



class PVCAM(QWidget):
    
    signalData=QtCore.pyqtSignal(object)
    def __init__(self,cam=None,confFile='conf.ini',**kwds):
        self.isConnected=False
        super(PVCAM, self).__init__()
        p = pathlib.Path(__file__)
        sepa=os.sep
        self.kwds=kwds
        
        if "confpath" in kwds:
            self.confpath=kwds["confpath"]
        else  :
            self.confpath=None
        
        if self.confpath==None:
            self.confpath=str(p.parent / confFile) # ini file with global path
        
        self.conf=QtCore.QSettings(self.confpath, QtCore.QSettings.IniFormat) # ini file 
        
        
        self.kwds["confpath"]=self.confpath
        
        self.icon=str(p.parent) + sepa+'icons' +sepa
        self.configMotorPath="./fichiersConfig/"
        self.configMotName='configMoteurRSAI.ini'
        self.confMotorPath=self.configMotorPath+self.configMotName
       
        self.confMot=QtCore.QSettings(str(p.parent / self.confMotorPath), QtCore.QSettings.IniFormat)
        self.kwds["conf"]=self.conf
        # self.kwds["confMot"]=self.confMot # add motor rsai position in visu
        
        
        if "affLight" in kwds:
            self.light=kwds["affLight"]
        else:
            self.light=False
        if "multi" in kwds:
            self.multi=kwds["multi"]
        else:
            self.multi=False 
        
        if "separate" in kwds:
            self.separate=kwds["separate"]
        else: 
            self.separate=False
            
        if "aff" in kwds: #  affi of Visu
            self.aff=kwds["aff"]
        else: 
            self.aff="right"  
            
        self.icon=str(p.parent) + sepa+'icons'+sepa
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.iconPlay=self.icon+'Play.png'
        self.iconSnap=self.icon+'Snap.png'
        self.iconStop=self.icon+'Stop.png'
        self.iconPlay=pathlib.Path(self.iconPlay)
        self.iconPlay=pathlib.PurePosixPath(self.iconPlay)
        self.iconStop=pathlib.Path(self.iconStop)
        self.iconStop=pathlib.PurePosixPath(self.iconStop)
        self.iconSnap=pathlib.Path(self.iconSnap)
        self.iconSnap=pathlib.PurePosixPath(self.iconSnap)
        self.nbShot=1
        
        if cam==None: # si None on prend la première...
            self.nbcam='cam0'
        else:self.nbcam=cam

        
        self.ccdName=self.conf.value(self.nbcam+"/nameCDD")
        self.camID=self.conf.value(self.nbcam+"/camID")
        
        
        
        self.setup()
        self.initCam()
        self.itrig=0
        self.actionButton()
        self.camIsRunnig=False
       
    
    def initCam(self):
#        print('init cam')
        

        pvc.init_pvcam()                   # Initialize PVCAM 
        
        try :
            self.cam=Camera.select_camera(self.camID)
            
        except: 
            try:
                self.cam = next(Camera.detect_camera()) # Use generator to find first camera.
            except:
                self.isConnected=False
        try :
            self.cam.open()                         # Open the camera.
            self.isConnected=True
            self.sn=pvc.get_param(self.cam.handle,const.PARAM_HEAD_SER_NUM_ALPHA,const.ATTR_CURRENT)
            
        except:
            self.isConnected=False
            self.cam=None
        
            
        if  self.isConnected==True:
            
            #start temperature thread : have to be off when acquiring
            self.threadTemp = ThreadTemperature(cam=self.cam)
            self.threadTemp.TEMP.connect(self.update_temp)
            self.threadTemp.stopTemp=False
            self.threadTemp.start()
            self.cam.temp_setpoint=500 # temp en mC ?
            self.cam.exp_mode='Timed'
            self.cam.set_param(const.PARAM_CLEAR_CYCLES, int(1))
            # self.cam.set_param("CleanCycleHeight"    , int(1))
            # print('cam',self.cam)
            
            self.cam.exp_time=int(self.conf.value(self.nbcam+"/shutter"))# set cam to 100 ms 
            self.sh=self.cam.exp_time
            
            # #self.cammte.setParameter("TriggerResponse"     , int(1)) # pas de trig
           
            # self.cam.setParameter("TriggerDetermination", int(1))
            self.dimx = self.cam.sensor_size[0] 
            self.dimy = self.cam.sensor_size[1] 
            self.dimx=2400
            self.dimy=2000
            self.cam.set_roi(0, 0, self.dimx,self.dimy) ## ? strange but full frame doesn't work speed of usb see photometric mail
    #        print('adc',self.cam.getParameter("AdcSpeed"))
    #        print('ShutterTimingMode',self.cam.getParameter("ShutterTimingMode"))
            
            min_exp_time = self.cam.get_param(const.PARAM_EXPOSURE_TIME, const.ATTR_MIN)
            max_exp_time = self.cam.get_param(const.PARAM_EXPOSURE_TIME, const.ATTR_MAX)
            
            self.hSliderShutter.setMinimum(min_exp_time)
            self.shutterBox.setMinimum(min_exp_time)
            self.hSliderShutter.setMaximum(1000) # or max_exp_time but too long
            self.shutterBox.setMaximum(1000) # or max_exp_time but too long
            self.hSliderShutter.setValue(self.sh)
            self.shutterBox.setValue(self.sh)
            self.tempWidget=TEMPWIDGET(self)
            self.settingWidget=SETTINGWIDGET(self,visualisation=self.visualisation)
            self.setWindowTitle(self.sn+"   " + self.ccdName)
            
        else :
            self.runButton.setEnabled(False)
            self.runButton.setStyleSheet("QPushButton:!pressed{border-image: url(%s);background-color: gray ;border-color: rgb(0, 0, 0,0);}""QPushButton:pressed{image: url(%s);background-color: gray ;border-color: rgb(0, 0, 0)}"%(self.iconPlay,self.iconPlay))
            self.stopButton.setEnabled(False)
            self.stopButton.setStyleSheet("QPushButton:!pressed{border-image: url(%s);background-color: gray ;border-color: rgb(0, 0, 0,0);}""QPushButton:pressed{image: url(%s);background-color: gray ;border-color: rgb(0, 0, 0)}"%(self.iconStop,self.iconStop) )
            self.trigg.setEnabled(False)
            self.hSliderShutter.setEnabled(False)
            self.shutterBox.setEnabled(False)  
           
    def update_temp(self, temp=None):
        if temp == None:
            temp = self.cam.temp
        self.tempBox.setText('%.1f °C' % temp)
        
        
    def setup(self):  
        """ user interface definition: 
        """
        
        hbox1=QHBoxLayout() # horizontal layout pour run snap stop
        self.sizebuttonMax=40
        self.sizebuttonMin=40
        self.runButton=QToolButton(self)
        self.runButton.setMaximumWidth(self.sizebuttonMax)
        self.runButton.setMinimumWidth(self.sizebuttonMax)
        self.runButton.setMaximumHeight(self.sizebuttonMax)
        self.runButton.setMinimumHeight(self.sizebuttonMax)
        self.runButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: green;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"% (self.iconPlay,self.iconPlay) )
        
        self.snapButton=QToolButton(self)
        self.snapButton.setPopupMode(0)
        menu=QMenu()
        #menu.addAction('acq',self.oneImage)
        menu.addAction('set nb of shot',self.nbShotAction)
        self.snapButton.setMenu(menu)
        self.snapButton.setMaximumWidth(self.sizebuttonMax)
        self.snapButton.setMinimumWidth(self.sizebuttonMax)
        self.snapButton.setMaximumHeight(self.sizebuttonMax)
        self.snapButton.setMinimumHeight(self.sizebuttonMax)
        self.snapButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: green;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"% (self.iconSnap,self.iconSnap) )
        
        self.stopButton=QToolButton(self)
        
        self.stopButton.setMaximumWidth(self.sizebuttonMax)
        self.stopButton.setMinimumWidth(self.sizebuttonMax)
        self.stopButton.setMaximumHeight(self.sizebuttonMax)
        self.stopButton.setMinimumHeight(self.sizebuttonMax)
        self.stopButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: gray ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"% (self.iconStop,self.iconStop) )
        self.stopButton.setEnabled(False)
      
        
        hbox1.addWidget(self.runButton)
        hbox1.addWidget(self.snapButton)
        hbox1.addWidget(self.stopButton)
        hbox1.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        hbox1.setContentsMargins(0, 20, 0, 10)
        self.widgetControl=QWidget(self)
        
        self.widgetControl.setLayout(hbox1)
        self.dockControl=QDockWidget(self)
        self.dockControl.setWidget(self.widgetControl)
        self.dockControl.resize(100,100)
        self.trigg=QComboBox()
        self.trigg.setMaximumWidth(80)
        self.trigg.addItem('OFF')
        self.trigg.addItem('ON')
        self.trigg.setStyleSheet('font :bold  10pt;color: white')
        self.labelTrigger=QLabel('Trigger')
        self.labelTrigger.setMaximumWidth(70)
        self.labelTrigger.setStyleSheet('font :bold  8pt')
        self.itrig=self.trigg.currentIndex()
        
        
        hbox2=QHBoxLayout()
        hbox2.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        hbox2.setContentsMargins(5, 15, 0, 0)
        hbox2.addWidget(self.labelTrigger)
        
        hbox2.addWidget(self.trigg)
        self.widgetTrig=QWidget(self)
        
        self.widgetTrig.setLayout(hbox2)
        self.dockTrig=QDockWidget(self)
        self.dockTrig.setWidget(self.widgetTrig)
        
        self.labelExp=QLabel('Exposure (ms)')
        self.labelExp.setStyleSheet('font :bold  9pt')
        self.labelExp.setMaximumWidth(160)
        self.labelExp.setAlignment(Qt.AlignCenter)
        
        self.hSliderShutter=QSlider(Qt.Horizontal)
        self.hSliderShutter.setMaximumWidth(80)
        self.shutterBox=QSpinBox()
        self.shutterBox.setStyleSheet('font :bold  8pt')
        self.shutterBox.setMaximumWidth(120)
        
        hboxShutter=QHBoxLayout()
        hboxShutter.setContentsMargins(5, 0, 0, 0)
        hboxShutter.setSpacing(10)
        vboxShutter=QVBoxLayout()
        vboxShutter.setSpacing(0)
        vboxShutter.addWidget(self.labelExp)#,Qt.AlignLef)
        
        hboxShutter.addWidget(self.hSliderShutter)
        hboxShutter.addWidget(self.shutterBox)
        vboxShutter.addLayout(hboxShutter)
        vboxShutter.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        vboxShutter.setContentsMargins(5, 5, 0, 0)
        
        self.widgetShutter=QWidget(self)
        
        self.widgetShutter.setLayout(vboxShutter)
        self.dockShutter=QDockWidget(self)
        self.dockShutter.setWidget(self.widgetShutter)
        
        
        
        self.labelGain=QLabel('Gain')
        self.labelGain.setStyleSheet('font :bold  10pt')
        self.labelGain.setMaximumWidth(120)
        self.labelGain.setAlignment(Qt.AlignCenter)
        
        self.hSliderGain=QSlider(Qt.Horizontal)
        self.hSliderGain.setMaximumWidth(80)
        self.gainBox=QSpinBox()
        self.gainBox.setMaximumWidth(60)
        self.gainBox.setStyleSheet('font :bold  8pt')
        self.gainBox.setMaximumWidth(120)
        self.hSliderGain.setDisabled(True)
        self.gainBox.setDisabled(True)
        hboxGain=QHBoxLayout()
        hboxGain.setContentsMargins(5, 0, 0, 0)
        hboxGain.setSpacing(10)
        vboxGain=QVBoxLayout()
        vboxGain.setSpacing(0)
        vboxGain.addWidget(self.labelGain)

        hboxGain.addWidget(self.hSliderGain)
        hboxGain.addWidget(self.gainBox)
        vboxGain.addLayout(hboxGain)
        vboxGain.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        vboxGain.setContentsMargins(5, 5, 0, 0)
        
        self.widgetGain=QWidget(self)
        self.widgetGain.setLayout(vboxGain)
        self.dockGain=QDockWidget(self)
        self.dockGain.setWidget(self.widgetGain)
        
        self.widgetTemp=QWidget(self)
        vboxTemp=QVBoxLayout()
        hboxTemp=QHBoxLayout()
        self.tempButton=QPushButton('Temp')
        self.tempButton.setMaximumWidth(80)
        hboxTemp.addWidget(self.tempButton)
        self.tempBox=QLabel('?')
        hboxTemp.addWidget(self.tempBox)
        vboxTemp.addLayout(hboxTemp,0)
        self.settingButton=QPushButton('Settings')
        vboxTemp.addWidget(self.settingButton)
        vboxTemp.setContentsMargins(5, 0, 0,0)
        self.widgetTemp.setLayout(vboxTemp)
        self.dockTemp=QDockWidget(self)
        self.dockTemp.setWidget(self.widgetTemp)
        
        
        hMainLayout=QHBoxLayout()
        
        if self.light==False:
            from visu import SEE
            self.visualisation=SEE(parent=self,name=self.nbcam,**self.kwds) ## Widget for visualisation and tools  self.confVisu permet d'avoir plusieurs camera et donc plusieurs fichier ini de visualisation
        else:
            from visu import SEELIGHT
            
            self.visualisation=SEELIGHT(parent=self,name=self.nbcam,**self.kwds)
        
        
            
        self.dockTrig.setTitleBarWidget(QWidget())        
        self.dockControl.setTitleBarWidget(QWidget()) # to avoid tittle
        self.dockShutter.setTitleBarWidget(QWidget())
        self.dockGain.setTitleBarWidget(QWidget())
        self.dockTemp.setTitleBarWidget(QWidget())
        if self.separate==True:
            self.dockTrig.setTitleBarWidget(QWidget())
            if self.aff=='left':
                self.visualisation.addDockWidget(Qt.LeftDockWidgetArea,self.dockControl)
                self.visualisation.addDockWidget(Qt.LeftDockWidgetArea,self.dockTrig)
                self.visualisation.addDockWidget(Qt.LeftDockWidgetArea,self.dockShutter)
                self.visualisation.addDockWidget(Qt.LeftDockWidgetArea,self.dockGain)
                self.visualisation.addDockWidget(Qt.LeftDockWidgetArea,self.dockTemp)
            else:
                self.visualisation.addDockWidget(Qt.RightDockWidgetArea,self.dockControl)
                self.visualisation.addDockWidget(Qt.RightDockWidgetArea,self.dockTrig)
                self.visualisation.addDockWidget(Qt.RightDockWidgetArea,self.dockShutter)
                self.visualisation.addDockWidget(Qt.RightDockWidgetArea,self.dockGain)
                self.visualisation.addDockWidget(Qt.RightDockWidgetArea,self.dockTemp)
        else:
        #self.dockControl.setFeatures(QDockWidget.DockWidgetMovable)
            self.visualisation.addDockWidget(Qt.TopDockWidgetArea,self.dockControl)
            self.visualisation.addDockWidget(Qt.TopDockWidgetArea,self.dockTrig)
            self.visualisation.addDockWidget(Qt.TopDockWidgetArea,self.dockShutter)
            self.visualisation.addDockWidget(Qt.TopDockWidgetArea,self.dockGain)
            self.visualisation.addDockWidget(Qt.TopDockWidgetArea,self.dockTemp)
            
            
        hMainLayout.addWidget(self.visualisation)
        self.setLayout(hMainLayout)
        self.setContentsMargins(0, 0, 0, 0)
        
        
        
        
        
        
        self.setLayout(hMainLayout)
    
    def shutter (self):
        '''set exposure time 
        '''
        self.sh=self.shutterBox.value() # 
        self.hSliderShutter.setValue(self.sh) # set value of slider
        self.cam.exp_time=int(self.sh)
        time.sleep(0.1)
        self.conf.setValue(self.nbcam+"/shutter",float(self.sh))
        self.conf.sync()
    
    def mSliderShutter(self): # for shutter slider 
        self.sh=self.hSliderShutter.value()
        self.shutterBox.setValue(self.sh)
        self.cam.exp_time=int(self.sh) 
        time.sleep(0.1)
        self.conf.setValue(self.nbcam+"/shutter",float(self.sh))
    
    def actionButton(self): 
        '''action when button are pressed
        '''
        self.runButton.clicked.connect(self.acquireMultiImage)
        self.snapButton.clicked.connect(self.acquireOneImage)
        self.stopButton.clicked.connect(self.stopAcq)      
        self.shutterBox.editingFinished.connect(self.shutter)    
        self.hSliderShutter.sliderReleased.connect(self.mSliderShutter)
        self.trigg.currentIndexChanged.connect(self.TrigA)
        self.tempButton.clicked.connect(lambda:self.open_widget(self.tempWidget) )
        self.settingButton.clicked.connect(lambda:self.open_widget(self.settingWidget) )
        
        self.threadRunAcq=ThreadRunAcq(self)
        self.threadRunAcq.newDataRun.connect(self.Display)
        self.threadOneAcq=ThreadOneAcq(self)
        self.threadOneAcq.newDataRun.connect(self.Display)#,QtCore.Qt.DirectConnection)
        self.threadOneAcq.endAcqState.connect(self.stopAcq)
        
        
        
    def acquireMultiImage(self):    
        ''' start the acquisition thread
        '''
        self.runButton.setEnabled(False)
        self.runButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: gray ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconPlay,self.iconPlay))
        self.snapButton.setEnabled(False)
        self.snapButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: gray ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconSnap,self.iconSnap))
        self.stopButton.setEnabled(True)
        self.stopButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconStop,self.iconStop) )
        self.trigg.setEnabled(False)
        self.camIsRunnig=True
        
        self.threadTemp.stopThreadTemp()
        
        self.threadRunAcq.newRun() # to set stopRunAcq=False
        self.threadRunAcq.start()
       
    def acquireOneImage(self):
        
        
        self.runButton.setEnabled(False)
        self.runButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: gray ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconPlay,self.iconPlay))
        self.snapButton.setEnabled(False)
        self.snapButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: gray ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconSnap,self.iconSnap))
        self.stopButton.setEnabled(True)
        self.stopButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconStop,self.iconStop) )
        self.trigg.setEnabled(False)
        
        self.threadTemp.stopThreadTemp()
        self.camIsRunnig=True
        
        self.threadOneAcq.newRun() # to set stopRunAcq=False
        self.threadOneAcq.start()
        
        
    def nbShotAction(self):
        '''
        number of snapShot
        '''
        nbShot, ok=QInputDialog.getInt(self,'Number of SnapShot ','Enter the number of snapShot ')
        if ok:
            self.nbShot=int(nbShot)
            if self.nbShot<=0:
               self.nbShot=1
        else:
            self.nbShot=1
    
    def stopAcq(self):
        
        self.threadRunAcq.stopThreadRunAcq()
        self.threadOneAcq.stopThreadOneAcq()
        
        self.runButton.setEnabled(True)
        self.runButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconPlay,self.iconPlay))
        self.snapButton.setEnabled(True)
        self.snapButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconSnap,self.iconSnap))
        self.stopButton.setEnabled(False)
        self.stopButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: gray ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconStop,self.iconStop) )
        self.trigg.setEnabled(True)
        
        self.threadTemp.stopTemp=False
        self.threadTemp.start()
        self.visualisation.frameNumber=1
        
    def TrigA(self):
    ## trig la CCD
        itrig=self.trigg.currentIndex()
        if itrig==0:
            self.cam.exp_mode='Timed'
            # self.cam.setParameter("TriggerResponse", int(1))
            # self.cam.setParameter("TriggerDetermination", int(1))
            # self.cam.sendConfiguration()
            print ('trigger OFF')
        if itrig==1:
            self.cam.exp_mode='Trigger First'
            #Available keys are: ['Timed', 'Strobed', 'Bulb', 'Trigger First', 'Variable Timed']
            #self.mte.setParameter("TriggerSource","TriggerSource_External")
            # self.cam.setParameter("TriggerResponse", int(2))
            # self.cam.setParameter("TriggerDetermination", int(1))
            # self.cam.sendConfiguration()
            print ('Trigger ON ')
    
    def Display(self,data):
        '''Display data with Visu module
        '''
        
        self.signalData.emit(data)
        # self.visualisation.newDataReceived(self.data) # send data to visualisation widget
    
    
    
    def open_widget(self,fene):
        
        """ open new widget 
        """
        
        if fene.isWinOpen==False:
            print("New widget")
            fene.show()
            fene.isWinOpen=True
    
        else:
            #fene.activateWindow()
            fene.raise_()
            fene.showNormal()
        
    def closeEvent(self,event):
        ''' closing window event (cross button)
        '''
        print(' close')
        try :
            self.threadTemp.stopThreadTemp()
        except:
            print('no camera connected')
        #self.threadTemp.stopThreadTemp()
        try :
            self.cam.close()
            pvc.uninit_pvcam()
        except :pass
        if self.isConnected==True:
            if self.settingWidget.isWinOpen==True:
                self.settingWidget.close()

class ThreadOneAcq(QtCore.QThread):
    
    '''Second thread for controling one or more  acquisition independtly
    '''
    newDataRun=QtCore.Signal(object)
    newStateCam=QtCore.Signal(bool)
    endAcqState=QtCore.Signal(bool)
    
    def __init__(self, parent):
        
        super(ThreadOneAcq,self).__init__(parent)
        self.parent=parent
        self.cam= self.parent.cam
        self.stopRunAcq=False
       
        
        
    def newRun(self):
        self.stopRunAcq=False
        
    def run(self):
        
        self.newStateCam.emit(True)
             
        for i in range (self.parent.nbShot):
            if self.stopRunAcq is not True :
                if i<self.parent.nbShot-1:
                    self.newStateCam.emit(True)
                    
                    time.sleep(0.01)
                else:
                    self.newStateCam.emit(False)
                                
                sh=self.parent.sh
                try: 
                    data = self.cam.get_frame(exp_time=sh)
                    data=np.rot90(data,-1)
                    self.newDataRun.emit(data)
                except :pass
                
        self.newStateCam.emit(False)
        self.endAcqState.emit(True)
        
        
    def stopThreadOneAcq(self):
        self.stopRunAcq=True
        self.cam.finish()
        
        
        
class ThreadRunAcq(QtCore.QThread):
    
    newDataRun=QtCore.Signal(object)
    
    def __init__(self, parent=None):
        super(ThreadRunAcq,self).__init__(parent)
        self.parent=parent
        self.cam = self.parent.cam
        self.stopRunAcq=False
       
    
    def newRun(self):
       
        self.stopRunAcq=False
    
    def run(self):
        print('-----> Start  multi acquisition')
        
        while True :

            if self.stopRunAcq:
                break
            
            sh=self.parent.sh
            try:
                data = self.cam.get_frame(exp_time=sh) # slow could be improve by using livemode
                # print(str(self.cam.check_frame_status()))
                data=np.rot90(data,-1)
                self.newDataRun.emit(data)
            except:
                pass   
                
            
            
        
    
    def stopThreadRunAcq(self):
        self.stopRunAcq=True
        self.cam.finish()
        self.cam.abort()
        
        
class ThreadTemperature(QtCore.QThread):
    """
    Thread pour la lecture de la temperature toute les 2 secondes
    """
    TEMP =QtCore.pyqtSignal(float) # signal pour afichage temperature

    def __init__(self, parent=None,cam=None):
        super(ThreadTemperature,self).__init__(parent)
        self.cam    = cam
        self.stopTemp=False
        
    def run(self):
        while self.cam is not None:
            temp = self.cam.temp
            time.sleep(2)
            self.TEMP.emit(temp)
            if self.stopTemp:
                break
            
            
    def stopThreadTemp(self):
        self.stopTemp=True
        print ('stop thread temperature')  
        self.terminate()        


class TEMPWIDGET(QWidget):
    
    def __init__(self,parent):
        
        super(TEMPWIDGET, self).__init__()
        self.parent=parent
        self.cam=self.parent.cam
        self.isWinOpen=False
        self.setup()
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        
    def setup(self) :   
        self.setWindowIcon(QIcon('./icons/LOA.png'))
        self.setWindowTitle('Temperature')
        self.vbox=QVBoxLayout()
        labelT=QLabel('Temperature')
        self.tempVal= QDoubleSpinBox(self)
        self.tempVal.setSuffix(" %s" % '°C')
        min_temp = self.cam.get_param(const.PARAM_TEMP_SETPOINT, const.ATTR_MIN)
        max_temp = self.cam.get_param(const.PARAM_TEMP_SETPOINT, const.ATTR_MAX)
       
        self.tempVal.setMaximum(max_temp/100)
        self.tempVal.setMinimum( min_temp/100)
        self.tempVal.setValue(self.cam.temp)
        self.tempSet=QPushButton('Set')
        self.hbox=QHBoxLayout()
        self.hbox.addWidget(labelT)
        self.hbox.addWidget(self.tempVal)
        self.hbox.addWidget(self.tempSet)
        self.vbox.addLayout(self.hbox)
        self.setLayout(self.vbox)
        self.tempSet.clicked.connect(self.SET)
        
        
        
    def SET(self):
        temp = self.tempVal.value()
        
        self.cam.temp_setpoint=int(temp*100)
        
    
    def closeEvent(self, event):
        """ when closing the window
        """
        self.isWinOpen=False
        
        time.sleep(0.1)
        event.accept() 
        
        
class SETTINGWIDGET(QWidget):
    
    def __init__(self, parent,visualisation=None):
        
        super(SETTINGWIDGET, self).__init__()
        self.parent=parent
        self.cam=self.parent.cam
        self.visualisation=visualisation
        self.isWinOpen=False
        
        self.setup()
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        
        self.actionButton()
        self.roi1Is=False
        
    def setup(self) : 
        self.dimx =self.cam.sensor_size[0]
        self.dimy =self.cam.sensor_size[1]
        self.setWindowIcon(QIcon('./icons/LOA.png'))
        self.setWindowTitle('SETTINGS')
        self.vbox=QVBoxLayout()
        
        hboxShutter=QHBoxLayout()
        shutterLabel=QLabel('ShutterMode')
        self.shutterMode=QComboBox()
        self.shutterMode.setMaximumWidth(100)
        self.shutterMode.addItem('Normal')
        self.shutterMode.addItem('Always Close')
        self.shutterMode.addItem('Always Open')
        self.shutterMode.addItem('Open before trig')
        
        hboxShutter.addWidget(shutterLabel)
        hboxShutter.addWidget(self.shutterMode)
        self.vbox.addLayout(hboxShutter)
        
        hboxFrequency=QHBoxLayout()
        frequencyLabel=QLabel('Frequency')
        self.frequency=QComboBox()
        self.frequency.setMaximumWidth(100)
        self.frequency.addItem('Normal')
        self.frequency.addItem('Always Close')
        self.frequency.addItem('Always Open')
        hboxFrequency.addWidget(frequencyLabel)
        hboxFrequency.addWidget(self.frequency)
        self.vbox.addLayout(hboxFrequency)
        
        hboxROI=QHBoxLayout()
        
        hbuttonROI=QVBoxLayout()
        self.setROIButton=QPushButton('Set ROI')
        self.setROIFullButton=QPushButton('Set full Frame')
        self.setROIMouseButton=QPushButton('Mousse')
        hbuttonROI.addWidget(self.setROIButton)
        hbuttonROI.addWidget(self.setROIFullButton)
        hbuttonROI.addWidget(self.setROIMouseButton)
        hboxROI.addLayout(hbuttonROI)
        
        roiLay= QVBoxLayout()
        labelROIX=QLabel('ROI Xo')
        self.ROIX=QDoubleSpinBox(self)
        self.ROIX.setMinimum(0)
        self.ROIX.setMaximum(self.dimx)
        
        self.ROIY=QDoubleSpinBox(self)
        self.ROIY.setMinimum(1)
        self.ROIY.setMaximum(self.dimy)
        labelROIY=QLabel('ROI Yo')
        
        labelROIW=QLabel('ROI Width')
        self.ROIW=QDoubleSpinBox(self)
        self.ROIW.setMinimum(0)
        self.ROIW.setMaximum(self.dimx)     
        
        labelROIH=QLabel('ROI Height')
        self.ROIH=QDoubleSpinBox(self)
        self.ROIH.setMinimum(1)
        self.ROIH.setMaximum(self.dimy) 
        
        labelBinX=QLabel('Bin X')
        self.BINX=QDoubleSpinBox(self)
        self.BINX.setMinimum(1)
        self.BINX.setMaximum(self.dimx) 
        labelBinY=QLabel('Bin Y ')
        self.BINY=QDoubleSpinBox(self)
        self.BINY.setMinimum(1)
        self.BINY.setMaximum(self.dimy) 
        
        grid_layout = QGridLayout()
        grid_layout.addWidget(labelROIX,0,0)
        grid_layout.addWidget(self.ROIX,0,1)
        grid_layout.addWidget(labelROIY,1,0)
        grid_layout.addWidget(self.ROIY,1,1)
        grid_layout.addWidget(labelROIW,2,0)
        grid_layout.addWidget(self.ROIW,2,1)
        grid_layout.addWidget(labelROIH,3,0)
        grid_layout.addWidget(self.ROIH,3,1)
        grid_layout.addWidget(labelBinX,4,0)
        grid_layout.addWidget(self.BINX,4,1)
        grid_layout.addWidget(labelBinY,5,0)
        grid_layout.addWidget(self.BINY,5,1)
        
        roiLay.addLayout(grid_layout)
        hboxROI.addLayout(roiLay)
        self.vbox.addLayout(hboxROI)

        self.setLayout(self.vbox)
        
        self.r1=100
        self.roi1=pg.RectROI([self.dimx/2,self.dimy/2], [2*self.r1, 2*self.r1],pen='r',movable=True)
        self.roi1.setPos([self.dimx/2-self.r1,self.dimy/2-self.r1])
        
    def actionButton(self):
        self.setROIButton.clicked.connect(self.roiSet)
        self.setROIFullButton.clicked.connect(self.roiFull)
        self.frequency.currentIndexChanged.connect(self.setFrequency)
        self.shutterMode.currentIndexChanged.connect(self.setShutterMode)
        self.setROIMouseButton.clicked.connect(self.mousseROI)
        self.roi1.sigRegionChangeFinished.connect(self.moussFinished)
        
    def mousseROI(self):
        
        self.visualisation.p1.addItem(self.roi1)
        self.roi1Is=True
        
    def moussFinished(self):
        
        posRoi=self.roi1.pos()
        sizeRoi=self.roi1.size()
        self.x0=int(posRoi.x())
        self.wroi=int(sizeRoi.x())
        self.hroi=int(sizeRoi.y())
        self.y0=posRoi.y()+sizeRoi.y()
              
        self.ROIX.setValue(self.x0)
        self.ROIY.setValue(self.y0)
        self.ROIW.setValue(self.wroi)
        self.ROIH.setValue(self.hroi)
        
    def roiSet(self):
        
        self.x0=int(self.ROIX.value())
        self.y0=int(self.ROIY.value())
        self.w=int(self.ROIW.value())
        self.h=int(self.ROIH.value())
        self.BinX=int(self.BINX.value())
        self.BinY=int(self.BINY.value())
        # print('bin',self.cam.bin_x)
        self.cam.bin_x=self.BinX
        self.cam.bin_Y=self.BinY
        # self.cam.set_roi(0, 0, self.dimx,self.dimy)
        
        self.cam.set_roi(self.x0, self.dimy-self.y0, self.w, self.h) # ROI start up left pyqtgraph botton left
        
        
        if self.roi1Is==True:
            self.visualisation.p1.removeItem(self.roi1)
            self.roi1Is=False
        
    def roiFull(self):
        
        self.w = self.parent.dimx
        self.h = self.parent.dimy
        self.ROIX.setValue(0)
        self.ROIY.setValue(0)
        self.ROIW.setValue(self.w)
        self.ROIH.setValue(self.h)
        self.BINX.setValue(1)
        self.BINX.setValue(1)
        self.cam.bin_x=int(1)
        self.cam.bin_Y=int(1)
        self.cam.set_roi(0, 0,self.w,self.h) # full frame
        
        print("fullframe")
        if self.roi1Is==True:
            self.visualisation.p1.removeItem(self.roi1)
            self.roi1Is=False
        
    def setFrequency(self) :
        """
        set frequency reading in Mhz
        """          
        ifreq=self.freqency.currentIndex()
        
        # toDO
        
        # if ifreq==0:
        #      self.cam.setParameter("AdcSpeed",0.1)
        # if ifreq==0:
        #      self.cam.setParameter("AdcSpeed",1)
        # if ifreq==0:
        #      self.cam.setParameter("AdcSpeed",2)
             
        # print('adc frequency(Mhz)',self.cam.getParameter("AdcSpeed"))

    def setShutterMode(self):
        """ set shutter mode
        """
        ishut=self.shutterMode.currentIndex()
        print('shutter')
        ## todo
        # if ishut==0:
        #      self.cam.setParameter("ShutterTimingMode",0)
        # if ishut==1:
        #      self.cam.setParameter("ShutterTimingMode",1) 
        # if ishut==2:
        #      self.cam.setParameter("ShutterTimingMode",2) 
        # if ishut==3:
        #      self.cam.setParameter("ShutterTimingMode",3)
        #      print('OutputSignal',self.mte.getParameter("ShutterTimingMode"))
             
    def closeEvent(self, event):
        """ when closing the window
        """
        self.isWinOpen=False
        if self.roi1Is==True:
            self.visualisation.p1.removeItem(self.roi1)
            self.roi1Is=False
        time.sleep(0.1)
        
        event.accept() 
        
if __name__ == "__main__":       
    
    appli = QApplication(sys.argv)
    # confpathVisu='C:/Users/Salle-Jaune/Desktop/Python/Princeton/confVisuFootPrint.ini'
    appli.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    e = PVCAM(camID=None)  
    e.show()
    appli.exec_()       