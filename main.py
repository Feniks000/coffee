import sys
import os
from PyQt5 import uic
import sqlite3
from PyQt5.QtWidgets import *
from PyQt5 import QtCore


def replace(elem: iter, index: int, table: dict) -> tuple:
    elem = list(elem)
    elem[index] = table[elem[index]]
    return tuple(elem)


def standart(elem: iter) -> tuple:
    elem = list(elem)
    elem[4] = text_fixed(elem[4])
    return tuple(elem)


def text_fixed(string_for_fix: str) -> str:
    data = string_for_fix.split()
    out = [[]]
    flag1 = True
    flag2 = True
    for elem in data:
        if len(elem) + len(' '.join(out[-1])) + 1 <= 40:
            out[-1].append(elem)
        else:
            out.append([elem])
    return '\n'.join(map(lambda x: ' '.join(x), out))


def ask(path, sql_statement: str):
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    try:
        cursor.execute(sql_statement)
        result = cursor.fetchall()
    except sqlite3.DatabaseError:
        return 'Error'
    else:
        conn.commit()
        conn.close()
        return result


class time_to_update(QtCore.QObject):
    running = False
    update_table = QtCore.pyqtSignal()

    def run(self):
        while True:
            self.update_table.emit()
            QtCore.QThread.msleep(1000)


class APP(QMainWindow):
    def __init__(self):
        super(APP, self).__init__()
        uic.loadUi('main.ui', self)
        self.action.triggered.connect(self.loader)
        self.action_2.triggered.connect(self.closer)
        self.path = None
        self.data = None
        self.thread = QtCore.QThread()
        self.time_to_update = time_to_update()
        self.time_to_update.moveToThread(self.thread)
        self.time_to_update.update_table.connect(self.update_table)
        self.thread.started.connect(self.time_to_update.run)
        self.thread.start()

    def loader(self):
        print('clicked')
        path = QFileDialog.getOpenFileName(self, 'select database', os.curdir)[0]
        if path:
            self.path = path
            a = ask(self.path, '''PRAGMA table_info('coffee');''') == 'Error'
            b = ask(self.path, '''PRAGMA table_info('degree of roasting');''') == 'Error'
            c = ask(self.path, '''PRAGMA table_info('types');''') == 'Error'
            if a or b or c:
                self.path = None
                self.err_message('Данная база повреждена или некорректна.')

    def closer(self):
        self.path = None

    def update_table(self):
        if self.path is not None:

            degree_of_roasting, types, data = dict(), dict(), list()
            for elem in ask(self.path, """select * from 'degree of roasting';"""):
                degree_of_roasting[elem[0]] = elem[1]
            for elem in ask(self.path, """select * from 'types';"""):
                types[elem[0]] = elem[1]
            for elem in ask(self.path, '''select * from 'coffee';'''):
                data.append(standart(replace(replace(elem, 1, degree_of_roasting), 3, types)))
            if len(data) == 0 or self.data == data:
                return

            self.tableWidget.clear()
            self.tableWidget.setColumnCount(len(data[-1]))
            for i, title in enumerate(ask(self.path, f'''PRAGMA table_info('coffee');''')):
                self.tableWidget.setHorizontalHeaderItem(i, QTableWidgetItem(str(title[1])))
            self.tableWidget.setRowCount(len(data))
            for i, row in enumerate(data):
                self.tableWidget.sizeHintForRow(i)
                for j, elem in enumerate(row):
                    self.tableWidget.setItem(i, j, QTableWidgetItem(str(elem)))
            print('updated')
            self.tableWidget.resizeColumnsToContents()
            self.tableWidget.resizeRowsToContents()
            self.data = data
        else:
            self.tableWidget.clear()
            self.tableWidget.setColumnCount(0)
            self.tableWidget.setRowCount(0)

    def err_message(self, text: str) -> None:
        QMessageBox().warning(self, 'Error', text)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = APP()
    widget.show()
    sys.exit(app.exec())
