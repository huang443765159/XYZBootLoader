from PyQt5.QtWidgets import QFileDialog, QMainWindow

from XYZBootLoader.BootLoader import BootLoader
from example.Gui.UI.UI import Ui_MainWindow

PATH = '../Hexs/'


class Gui(QMainWindow):

    def __init__(self):
        super().__init__()
        self._loader = BootLoader()
        self._loader.sign_cur_state.connect(self._signal_cur_state)
        self._loader.sign_cur_per.connect(self._signal_cur_per)
        self._ui = Ui_MainWindow()
        self._ui.setupUi(self)
        self._ui.btn_choose_hex.clicked.connect(self._choose_hex)

    def _choose_hex(self):
        self._ui.cur_progress.setValue(0)
        file_type_list = 'stl File (*.txt *.bin);; All File (*.*)'
        file = QFileDialog.getOpenFileName(caption='选取单文件',
                                           directory=PATH,
                                           filter=file_type_list,
                                           options=QFileDialog.DontUseNativeDialog)[0]
        self._loader.load_file(path=file)

    def _signal_cur_state(self, cur_state: str):
        text = self._ui.lb_show.text()
        if text != cur_state:
            self._ui.lb_show.setText(cur_state)

    def _signal_cur_per(self, cur_per: int, cur_pkt_id: int, all_pkt: int):
        self._ui.cur_progress.setValue(cur_per)
        self._ui.lb_show.setText(f'烧录第{cur_pkt_id}/{all_pkt}个包')
