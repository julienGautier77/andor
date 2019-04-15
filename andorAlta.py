#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 27 17:07:24 2019
Modified on Fri Mar  1 15:21:38 2019
a Python user interface for Ador Alta camera




on conda prompt 
pip install pymba (https://github.com/morefigs/pymba.git )
pip install qdarkstyle (https://github.com/ColinDuquesnoy/QDarkStyleSheet.git)
pip install pyqtgraph (https://github.com/pyqtgraph/pyqtgraph.git)
pip install visu
modify vimba.camera :acquire_frame(self) : self._single_frame.wait_for_capture(1000000)
and comment the line (?)(?)

@author: juliengautier
version : 2019.3
"""
__version__='2019.4'
__author__='julien Gautier'
version=__version__

from PyQt5.QtWidgets import QApplication,QVBoxLayout,QHBoxLayout,QWidget,QPushButton
from PyQt5.QtWidgets import QComboBox,QSlider,QLabel,QSpinBox
from pyqtgraph.Qt import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import sys,time
import numpy as np
import pathlib,os

import ctypes
import win32com.client
from win32com.client import constants as Constants
# generate and import apogee ActiveX module
apogee_module = win32com.client.gencache.EnsureModule(
    '{A2882C73-7CFB-11D4-9155-0060676644C1}', 0, 1, 0)



try :
    from visu import SEE
except:
    print ('No visu module installed : pip install visu' )
    
import qdarkstyle


class ANDOR(QWidget):
    '''Andor class for allied vision Camera
    '''
    def __init__(self,cam='camDefault'):
        
        super(ANDOR, self).__init__()
        p = pathlib.Path(__file__)
        self.conf=QtCore.QSettings(str(p.parent / 'confCCD.ini'), QtCore.QSettings.IniFormat)
        sepa=os.sep
        self.icon=str(p.parent) + sepa+'icons' +sepa
      
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        self.iconPlay=pathlib.Path(self.icon+'Play.svg')
        self.iconPlay=pathlib.PurePosixPath(self.iconPlay)
        self.iconStop=pathlib.Path(self.icon+'Stop.svg')
        self.iconStop=pathlib.PurePosixPath(self.iconStop)
        self.nbcam=cam
        self.initCam()
        self.setup()
        self.itrig=0
        self.actionButton()
        self.camIsRunnig=False
        self.initTemp()
       
        
    def initCam(self):
        '''initialisation of cam parameter 
        '''
        self.LineTrigger='trigg'
       
        try:
                
            self.cam0 = win32com.client.Dispatch('Apogee.Camera2')
            self.ccdName=self.conf.value(self.nbcam+"/nameCDD")
            self.isConnected=True
        except:
            self.isConnected=False
            self.ccdName='no camera'
        
        self.setWindowTitle(self.ccdName+'       v.'+ version)
        
        if self.isConnected==True:
            try :
                self.cam0.Init(Constants.Apn_Interface_USB,0, 0, 0)
            except :
                discover = win32com.client.Dispatch('Apogee.CamDiscover')
                discover.DlgCheckUsb = True
                discover.ShowDialog(True)
                if not discover.ValidSelection:
                    raise ValueError('No camera selected')
        #self.interface = self._reverse_constants[discover.SelectedInterface]
                self.camera_number = discover.SelectedCamIdOne
                self.camera_num2 = discover.SelectedCamIdTwo
            #print(self.camera_number,self.camera_num2)
                self.cam0.Init(Constants.Apn_Interface_USB,self.camera_number, self.camera_num2, 0)
            
            print(self.ccdName, 'is connected @:'  ,self.cam0.CameraModel, 'serial:',self.cam0.CameraSerialNumber)
            self.sh=float(self.conf.value(self.nbcam+'/shutter'))
            h=self.cam0.RoiPixelsH
            w=self.cam0.RoiPixelsV
            print('camera size',h,'*',w)
            self.buffer = np.zeros((h, w), dtype=np.uint16)
          
            
    def setup(self):  
        """ user interface definition: 
        """
        vbox1=QVBoxLayout() 
       
        self.camName=QLabel(self.ccdName,self)
        self.camName.setAlignment(Qt.AlignCenter)
        
        self.camName.setStyleSheet('font :bold  30pt;color: white')
        vbox1.addWidget(self.camName)
        
        hbox1=QHBoxLayout() # horizontal layout pour run et stop
        self.runButton=QPushButton(self)
        self.runButton.setMaximumWidth(60)
        self.runButton.setMinimumHeight(60)
        
        self.runButton.setStyleSheet("QPushButton:!pressed{border-image: url(%s);background-color: rgb(0, 0, 0,0) ;border-color: green;}""QPushButton:pressed{image: url(%s);background-color: rgb(0, 0, 0,0) ;border-color: rgb(0, 0, 0)}"% (self.iconPlay,self.iconPlay) )
        self.stopButton=QPushButton(self)
        
        self.stopButton.setMaximumWidth(60)
        self.stopButton.setMinimumHeight(60)
        
        self.stopButton.setStyleSheet("QPushButton:!pressed{border-image: url(%s);background-color: gray ;border-color: rgb(0, 0, 0,0);}""QPushButton:pressed{image: url(%s);background-color: gray ;border-color: rgb(0, 0, 0)}"% (self.iconStop,self.iconStop) )
        self.stopButton.setEnabled(False)
        
        hbox1.addWidget(self.runButton)
        hbox1.addWidget(self.stopButton)
        
        vbox1.addLayout(hbox1)
        
        self.trigg=QComboBox()
        self.trigg.setMaximumWidth(60)
        self.trigg.addItem('OFF')
        self.trigg.addItem('ON')
        self.labelTrigger=QLabel('Trigger')
        self.labelTrigger.setMaximumWidth(60)
        self.itrig=self.trigg.currentIndex()
        
        hbox2=QHBoxLayout()
        hbox2.addWidget(self.labelTrigger)
        hbox2.addWidget(self.trigg)
        
        vbox1.addLayout(hbox2)
        
        self.labelExp=QLabel('Exposure (ms)')
        self.labelExp.setMaximumWidth(120)
        self.labelExp.setAlignment(Qt.AlignCenter)
        vbox1.addWidget(self.labelExp)
        self.hSliderShutter=QSlider(Qt.Horizontal)
        self.hSliderShutter.setMinimum(50)
        self.hSliderShutter.setMaximum(1000)
        if self.isConnected==True:
            self.hSliderShutter.setValue(self.sh)
        self.hSliderShutter.setMaximumWidth(80)
        self.shutterBox=QSpinBox()
        self.shutterBox.setMinimum(50)
        self.shutterBox.setMaximum(1000)

        if self.isConnected==True:
            self.shutterBox.setValue(self.sh)
        hboxShutter=QHBoxLayout()
        hboxShutter.addWidget(self.hSliderShutter)
        hboxShutter.addWidget(self.shutterBox)
        vbox1.addLayout(hboxShutter)
        
        self.labelGain=QLabel('Gain')
        self.labelGain.setMaximumWidth(120)
        self.labelGain.setAlignment(Qt.AlignCenter)
        vbox1.addWidget(self.labelGain)
        hboxGain=QHBoxLayout()
        self.hSliderGain=QSlider(Qt.Horizontal)
        self.hSliderGain.setMaximumWidth(80)
        if self.isConnected==True:
            self.hSliderGain.setMinimum(0)
            self.hSliderGain.setMaximum(1023)
            self.hSliderGain.setValue(float(self.conf.value(self.nbcam+'/gain')))
        self.gainBox=QSpinBox()
        if self.isConnected==True:
            self.gainBox.setMinimum(0)
            self.gainBox.setMaximum(1023)
        self.gainBox.setMaximumWidth(60)
        if self.isConnected==True:
            self.gainBox.setValue(int(self.conf.value(self.nbcam+'/gain')))
       # self.mSliderGain.setEnabled(False)   
        self.gainBox.setEnabled(False)
        hboxGain.addWidget(self.hSliderGain)
        hboxGain.addWidget(self.gainBox)
        vbox1.addLayout(hboxGain)
        
        hboxTemp=QHBoxLayout()
        self.tempButton=QPushButton('Temp')
        hboxTemp.addWidget(self.tempButton)
        self.tempBox=QLabel('?')
        hboxTemp.addWidget(self.tempBox)
        vbox1.addLayout(hboxTemp)
        
        self.IoButton=QPushButton('IO settings')
        vbox1.addWidget(self.IoButton)
        vbox1.addStretch(1)
        hMainLayout=QHBoxLayout()
        hMainLayout.addLayout(vbox1)
        
        
        self.visualisation=SEE() ## Widget for visualisation and tools 
        
        vbox2=QVBoxLayout() 
        vbox2.addWidget(self.visualisation)
        hMainLayout.addLayout(vbox2)
        
        self.setLayout(hMainLayout)
        
        
    def actionButton(self): 
        '''action when button are pressed
        '''
        self.runButton.clicked.connect(self.acquireMultiImage)
        self.stopButton.clicked.connect(self.stopAcq)      
        self.shutterBox.editingFinished.connect(self.shutter)    
        self.hSliderShutter.sliderReleased.connect(self.mSliderShutter)
        
        self.gainBox.editingFinished.connect(self.gain)    
        self.hSliderGain.sliderReleased.connect(self.mSliderGain)
        self.trigg.currentIndexChanged.connect(self.trigA)
        self.tempButton.clicked.connect(self.TempButton)
        self.IoButton.clicked.connect(self.IOSet)
    
    def initTemp(self):
        self.threadRunTemp=ThreadRunTemp(cam0=self.cam0)
        self.threadRunTemp.newTemp.connect(self.Temp)
        self.threadRunTemp.start()
        
    def Temp(self,temp):
        self.tempBox.setText('%.1f °C'%temp)
    
    def TempButton(self):
        self.cam0.ShowTempDialog()
        
    def IOSet (self):
        self.cam0.ShowIoDialog()
        
    def softTrigger(self):
        '''to have a sofware trigger (todo)
        '''
        print('trig soft')
      
    
    def shutter (self):
        '''set exposure time 
        '''
        self.sh=self.shutterBox.value() # 
        self.hSliderShutter.setValue(self.sh) # set value of slider
        time.sleep(0.1)
        self.conf.setValue(self.nbcam+"/shutter",float(self.sh))
        self.conf.sync()
    
    def mSliderShutter(self): # for shutter slider 
        self.sh=self.hSliderShutter.value()
        self.shutterBox.setValue(self.sh) # 
        time.sleep(0.1)
        self.conf.setValue(self.nbcam+"/shutter",float(self.sh))
    
    def gain (self):
        '''set gain
        '''
        g=self.gainBox.value() # 
        self.hSliderGain.setValue(g) # set slider value
        time.sleep(0.1)
        self.cam0.SetAdGain(int(g),int(1),int(0))
        gainnn=ctypes.c_ulong(0)
        print( "gain ",self.cam0.GetAdGain(gainnn,int(1),int(0)))
        self.conf.setValue(self.nbcam+"/gain",float(g))
        self.conf.sync()
    
    def mSliderGain(self):
        g=self.hSliderGain.value()
        self.gainBox.setValue(g) # set  box vleue 
        time.sleep(0.1)
        self.cam0.SetAdGain(int(g),int(0),int(0))
        print( "gain ",g)
        self.conf.setValue(self.nbcam+"/gain",float(g))
        self.conf.sync()
        
    def trigA(self):
        '''to select trigger mode
        '''
        self.itrig=self.trigg.currentIndex()
        if self.itrig==1:
            self.cam0.TriggerNormalGroup=(bool(True))
            self.cam0.TriggerNormalEach=(bool(False))
            print('Trig on')
        else:
            self.cam0.TriggerNormalGroup=(bool(False))
            self.cam0.TriggerNormalEach=(bool(False))
            print('Trig off')
            
    def acquireMultiImage(self):    
        ''' start the acquisition thread
        '''
        self.runButton.setEnabled(False)
        self.runButton.setStyleSheet("QPushButton:!pressed{border-image: url(%s);background-color: gray ;border-color: rgb(0, 0, 0,0);}""QPushButton:pressed{image: url(%s);background-color: gray ;border-color: rgb(0, 0, 0)}"%(self.iconPlay,self.iconPlay))
        
        self.stopButton.setEnabled(True)
        self.stopButton.setStyleSheet("QPushButton:!pressed{border-image: url(%s);background-color: rgb(0, 0, 0,0) ;border-color: rgb(0, 0, 0,0);}""QPushButton:pressed{image: url(%s);background-color: rgb(0, 0, 0,0) ;border-color: rgb(0, 0, 0)}"%(self.iconStop,self.iconStop) )
        
        self.trigg.setEnabled(False)
        self.hSliderShutter.setEnabled(False)
        self.shutterBox.setEnabled(False)
        
        self.threadRunAcq=ThreadRunAcq(cam0=self.cam0,itrig=self.itrig,sh=self.sh,buffer=self.buffer)
        self.threadRunAcq.newDataRun.connect(self.Display)
        self.threadRunAcq.start()
        self.camIsRunnig=True 
        
    
    def stopAcq(self):
        '''Stop     acquisition
        '''
        print('stop')
        if self.camIsRunnig==True:
            self.threadRunAcq.stopThreadRunAcq()
            
            self.camIsRunnig=False
            
        self.runButton.setEnabled(True)
        self.runButton.setStyleSheet("QPushButton:!pressed{border-image: url(%s);background-color: rgb(0, 0, 0,0) ;border-color: rgb(0, 0, 0,0);}""QPushButton:pressed{image: url(%s);background-color: rgb(0, 0, 0,0) ;border-color: rgb(0, 0, 0)}"%(self.iconPlay,self.iconPlay))
        self.stopButton.setEnabled(False)
        self.stopButton.setStyleSheet("QPushButton:!pressed{border-image: url(%s);background-color: gray ;border-color: rgb(0, 0, 0,0);}""QPushButton:pressed{image: url(%s);background-color: gray ;border-color: rgb(0, 0, 0)}"%(self.iconStop,self.iconStop) )
        
        self.trigg.setEnabled(True)
        self.hSliderShutter.setEnabled(True)
        self.shutterBox.setEnabled(True)
        
        if self.itrig==1:
            #self.cam0.Reset()
            print('Reset')
            self.cam0.StopExposure(bool(False))
            self.cam0.ResetSystem()
#            self.cam0.Init(Constants.Apn_Interface_USB,0, 0, 0)
#            print('init')
            
    def Display(self,data):
        '''Display data with Visu module
        '''
        self.data=data
        self.visualisation.newDataReceived(self.data) # send data to visualisation widget
        
    def closeEvent(self,event):
        ''' closing window event (cross button)
        '''
        print(' close')
        self.stopAcq()
        time.sleep(0.2)
        
          
        
        
        
class ThreadRunAcq(QtCore.QThread):
    '''Second thread for controling acquisition independtly
    '''
    newDataRun=QtCore.Signal(object)
    
    def __init__(self, parent=None,cam0=None,itrig=None,sh=0.01,buffer=None):
        
        super(ThreadRunAcq,self).__init__(parent)
        self.cam0 = cam0
        self.stopRunAcq=False
        self.itrig= itrig
        self.sh=sh/1000
        
        self.buffer=buffer
        
    def run(self):
        
        while self.stopRunAcq is not True :
            self.cam0.Expose(float(self.sh), bool(True))
            #print(self.cam0.ImagingStatus,Constants.Apn_Status_WaitingOnTrigger)#,self.cam0.ImagingStatus_WaitingOnTrigger) 
            while self.cam0.ImagingStatus != Constants.Apn_Status_ImageReady:
                pass
            self.cam0.GetImage(self.buffer.ctypes.data)
            dat1=self.buffer
            if dat1 is not None:
                data=dat1#.buffer_data_numpy()
                data=np.rot90(data,3)
                if self.stopRunAcq==True:
                    pass
                else :
                    self.newDataRun.emit(data)
            
            
    def stopThreadRunAcq(self):
        
        self.stopRunAcq=True
        time.sleep(0.5)
        
        #self.cam0.StopExposure(bool(True))
        
         

class ThreadRunTemp(QtCore.QThread):
    '''Second thread for controling temperature
    '''
    newTemp=QtCore.Signal(object)
    
    def __init__(self,cam0=None):
        super(ThreadRunTemp,self).__init__(parent=None)
        self.cam0 = cam0
        self.stopRunTemp=False
        
    def run(self):
        
        while self.stopRunTemp is not True :
            time.sleep(5)
            temp=float(self.cam0.TempCCD)
            self.newTemp.emit(temp)
    
    def stopThreadTemp(self):
        self.stopRunTemp=True
        
        
        
if __name__ == "__main__":       
    
    appli = QApplication(sys.argv) 
    appli.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    e = ANDOR('cam1')  
    e.show()
    appli.exec_()       
    
    