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
    print(sql_statement)
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    try:
        cursor.execute(sql_statement)
        result = cursor.fetchall()
    except sqlite3.DatabaseError as err:
        print(err)
        return 'Error'
    else:
        conn.commit()
        conn.close()
        return result


# class time_to_update(QtCore.QObject):
#     running = False
#     update_table = QtCore.pyqtSignal()
#
#     def run(self):
#         while True:
#             self.update_table.emit()
#             QtCore.QThread.msleep(1000)


class Main(QMainWindow):
    def __init__(self, state: int) -> None:
        if state == 0:
            super(Main, self).__init__()
            # self.thread = QtCore.QThread()
            # self.time_to_update = time_to_update()
            # self.time_to_update.moveToThread(self.thread)
            # self.time_to_update.update_table.connect(self.update_table)
            # self.thread.started.connect(self.time_to_update.run)
        uic.loadUi('main.ui', self)
        self.action.triggered.connect(self.loader)
        self.action_2.triggered.connect(self.closer)
        self.action_3.triggered.connect(self.open_redactor)
        self.path = None
        self.table_changed = False
        # self.redactor = Redactor()
        # self.data = None
        # self.thread.start()

    def loader(self) -> None:
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
                return
            self.update_table()

    def closer(self) -> None:
        self.path = None
        self.update_table()

    def close_redactor(self) -> None:
        self.__init__(1)

    def err_message(self, text: str) -> None:
        QMessageBox().warning(self, 'Error', text)

    def update_table(self) -> None:
        if self.path is not None:

            degree_of_roasting, types, data = dict(), dict(), list()
            for elem in ask(self.path, """select * from 'degree of roasting';"""):
                degree_of_roasting[elem[0]] = elem[1]
            for elem in ask(self.path, """select * from 'types';"""):
                types[elem[0]] = elem[1]
            for elem in ask(self.path, '''select * from 'coffee';'''):
                data.append(standart(replace(replace(elem, 1, degree_of_roasting), 3, types)))
            # if len(data) == 0 or self.data == data:
            #     return
            if len(data) == 0:
                return
            self.table_changed = True

            self.tableWidget.clear()
            self.tableWidget.setColumnCount(len(data[-1]))
            self.titles = ask(self.path, f'''PRAGMA table_info('coffee');''')
            for i, title in enumerate(self.titles):
                self.tableWidget.setHorizontalHeaderItem(i, QTableWidgetItem(str(title[1])))
            self.tableWidget.setRowCount(len(data))
            for i, row in enumerate(data):
                self.tableWidget.sizeHintForRow(i)
                for j, elem in enumerate(row):
                    self.tableWidget.setItem(i, j, QTableWidgetItem(str(elem)))
            print('updated')

            self.tableWidget.resizeColumnsToContents()
            self.tableWidget.resizeRowsToContents()
            self.table_changed = False
            # self.data = data
        else:
            self.table_changed = True
            self.tableWidget.clear()
            self.tableWidget.setColumnCount(0)
            self.tableWidget.setRowCount(0)
            self.table_changed = False

    def open_redactor(self) -> None:
        uic.loadUi('addEditCoffeeForm.ui', self)
        self.action_6.triggered.connect(self.close_redactor)
        self.action.triggered.connect(self.loader)
        self.action_2.triggered.connect(self.closer)
        self.action_5.triggered.connect(self.add_coffee)
        self.action_id.triggered.connect(self.delete_coffee_by_id)
        self.action_4.triggered.connect(self.delete_coffee_using_parameters)
        self.tableWidget.itemChanged.connect(self.item_changed_handler)

    def add_coffee(self) -> None:
        if self.path is None:
            self.err_message('Сначала загрузите базу данных')
            return
        ask(self.path, '''INSERT INTO coffee('degree of roasting', 'grade', 'type', 'taste', 
        'cost', 'volume') VALUES (1, '---', 1, '---', 0, 0)''')
        self.update_table()
        return

    def delete_coffee_by_id(self) -> None:
        if self.path is None:
            self.err_message('Сначала загрузите базу данных')
            return
        text, ok = QInputDialog.getText(self, " ", "Введите id для удаления")
        if ok:
            if text.isdigit():
                if not len(ask(self.path, f'''select * from coffee WHERE id = {text}''')):
                    self.err_message('Такого id нет в базе!')
                    return
                ask(self.path, f'''DELETE from coffee WHERE id = {text}''')
            else:
                self.err_message('id должно быть числовым значением!')
                return
        self.update_table()

    def delete_coffee_using_parameters(self) -> None:
        if self.path is None:
            self.err_message('Сначала загрузите базу данных')
            return
        st = 'Выберите параметр по которому собираетесь удалять элементы'
        it = map(lambda x: str(x[1]), ask(self.path, f'''PRAGMA table_info('coffee');''')[1:])
        text, ok = QInputDialog.getItem(self, " ", st, it, False, False)
        if ok:
            text2, ok = QInputDialog.getText(self, " ", "Введите чему должен бать равен параметр")
            if ok:
                if text == 'degree of roasting':
                    degree_of_roasting, all_elem = dict(), list()
                    for elem in ask(self.path, """select * from 'degree of roasting';"""):
                        degree_of_roasting[elem[1]] = elem[0]
                        all_elem.append(elem[1])
                    if text2 not in all_elem:
                        self.err_message('Данный параметр не может принимать такие значения!')
                        return
                    a = degree_of_roasting[text2]
                    st = f'''DELETE from 'coffee' WHERE "degree of roasting" = {a};'''
                    ask(self.path, st)
                    print(degree_of_roasting[text2])
                    self.update_table()
                    return
                if text == 'type':
                    types, all_elem = dict(), list()
                    for elem in ask(self.path, """select * from 'types';"""):
                        types[elem[1]] = elem[0]
                        all_elem.append(elem[1])
                    if text2 not in all_elem:
                        self.err_message('Данный параметр не может принимать такие значения!')
                        return
                    print(text)
                    st = f'''DELETE from 'coffee' WHERE "type" = {types[text2]};'''
                    ask(self.path, st)
                    print(types[text2])
                    self.update_table()
                    return
                st = f'''DELETE from 'coffee' WHERE "{text}" = '{text2}';'''
                ask(self.path, st)
                self.update_table()
                return

    def item_changed_handler(self, item: QTableWidgetItem) -> None:
        if self.table_changed:
            return
        if item.column() == 0:
            self.update_table()
            return
        if item.column() == 1:
            degree_of_roasting, all_elem = dict(), list()
            for elem in ask(self.path, """select * from 'degree of roasting';"""):
                degree_of_roasting[elem[1]] = elem[0]
                all_elem.append(elem[1])
            if item.text() not in all_elem:
                self.err_message('Такого типа обжарки не существует')
                self.update_table()
                return
            ask(self.path, f'''UPDATE coffee 
                                SET 'degree of roasting' = {degree_of_roasting[item.text()]} 
                                WHERE id == {self.tableWidget.item(item.row(), 0).text()}''')
            return
        if item.column() in (2, 4):
            ask(self.path, f'''UPDATE coffee 
                                SET '{"grade" if item.column() == 2 else "taste"}' = '{item.text()}' 
                                WHERE id == {self.tableWidget.item(item.row(), 0).text()}''')
            return
        if item.column() == 3:
            types, all_elem = dict(), list()
            for elem in ask(self.path, """select * from 'types';"""):
                types[elem[1]] = elem[0]
                all_elem.append(elem[1])
            if item.text() not in all_elem:
                self.err_message('Такого типа помола не существует')
                self.update_table()
                return
            ask(self.path, f'''UPDATE coffee 
                                SET 'type' = {types[item.text()]} 
                                WHERE id == {self.tableWidget.item(item.row(), 0).text()}''')
            return
        if item.column() in (5, 6):
            if item.text().isdigit():
                ask(self.path, f'''UPDATE coffee 
                                SET '{"cost" if item.column() == 5 else "volume"}' = {item.text()} 
                                WHERE id == {self.tableWidget.item(item.row(), 0).text()}''')
                return
            else:
                self.update_table()
                self.err_message('Извините, но данный столбец предназначен только для числовых '
                                 'значений!')
                return


if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = Main(0)
    widget.show()
    sys.exit(app.exec())
