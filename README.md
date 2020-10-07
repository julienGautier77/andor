# andor


andor  is an user interface library to control Andor apogee camera.

It can make plot profile and data measurements  analysis

    https://github.com/julienGautier77/andor

## Requirements

*  install Apogee Setup.exe from andor
*  add  frameWork 3.5 : Control Panel\All Control Panel Items\Programs and Features : Turn windows feature on or off
*   python 3.x
*   Numpy
*   PyQt5
*   visu
    


## Usage

    from PyQt5.QtWidgets import QApplication
    import sys
    import qdarkstyle
    import andor
    
    appli = QApplication(sys.argv)   
    appli.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    e = ANDOR('camDefault')
    e.show()
-----------------------------------------
-----------------------------------------
