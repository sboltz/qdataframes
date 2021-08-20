#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{insert description here}

Created on 8/20/21

@author: SBoltz
"""
from functools import wraps

from PySide2 import QtWidgets, QtGui, QtCore
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QMessageBox


_TEST_MODE = False


msg_icons = {
    "info": QMessageBox.Information,
    "warning": QMessageBox.Warning,
    "critical": QMessageBox.Critical,
}
default_button = {
    "ok": QMessageBox.Ok,
    "cancel": QMessageBox.Cancel,
}


def test_mode_wrapper(func):  # There has to be a less messy way to handle this... especially if other packages are going to be using it
    """ Determines if it's a project is running in test mode and modifies behavior accordingly """
    @wraps(func)
    def check_test_mode(*args, parent=None, **kwargs):
        msg = func(*args, **kwargs)
        if _TEST_MODE and parent:
            parent._msgbox = msg
        elif _TEST_MODE and not parent:
            raise AttributeError(f"Test mode for {func.__name__} requires specification of a parent object")
        else:
            ret = msg.exec_()
            return ret

    return check_test_mode


@test_mode_wrapper
def popup_message(txt: str, mtype: str = "info", ok_cancel: bool = False, default: str = "ok") -> int:
    """
    Create a message box from the current window

    Parameters
    ----------
    txt
        Text to display in the message box
    mtype
        Type of message box to display
    ok_cancel
        If True, dialog has an "Ok" and "Cancel" button instead of just an "Ok" button
    default
        Specifies which button should be the default for the dialog

    Returns
    -------
    The return value from the message box
    """
    msg = QMessageBox()
    msg.setIcon(msg_icons[mtype])
    msg.setText(txt)
    if ok_cancel:
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg.setDefaultButton(default_button[default])
    return msg


class QAutoCompleteLineEdit(QtWidgets.QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        completer = QtWidgets.QCompleter()
        completer.setModel(QtGui.QStandardItemModel())
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.setCompleter(completer)

    @property
    def suggestions(self):
        completion_model = self.completer().model()
        return [
            completion_model.item(i).text()
            for i in range(completion_model.rowCount())
        ]

    @suggestions.setter
    def suggestions(self, suggestions):
        completion_model = self.completer().model()
        completion_model.clear()
        for suggestion in suggestions:
            item = QtGui.QStandardItem(suggestion)
            completion_model.appendRow(item)


class QAutoCompleteDelegate(QtWidgets.QStyledItemDelegate):

    def createEditor(self, parent: QtWidgets.QWidget, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> QtWidgets.QWidget:
        return QAutoCompleteLineEdit(parent)

    def setEditorData(self, editor: QAutoCompleteLineEdit, index: QtCore.QModelIndex):
        val = index.model().data(index, Qt.EditRole)
        mod = index.model()
        try:
            suggestions = mod.autocomplete_suggestions(index)
        except AttributeError:
            raise MissingAutocompleteError("Data model must have an 'autocomplete_suggestions' method")
        editor.setText(val)
        editor.suggestions = suggestions

    def updateEditorGeometry(self, editor: QtWidgets.QWidget, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex):
        editor.setGeometry(option.rect)


class MissingAutocompleteError(Exception):
    """ Raise if the associated data model for the autocomplete doesn't have an 'autocomplete_suggestions' method """
