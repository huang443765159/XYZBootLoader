import sys

from PyQt5.QtWidgets import QApplication

from example.Gui.Gui import Gui


class App:

    def __init__(self):
        self._gui = Gui()
        self._gui.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    test = App()
    app.exec_()
