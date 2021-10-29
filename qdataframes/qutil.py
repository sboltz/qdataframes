#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{insert description here}

Created on 8/20/21

@author: SBoltz
"""
from functools import wraps
from typing import Callable, Optional, Any, List, Iterable

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


def test_mode_wrapper(
    func: Callable,
) -> Any:  # There has to be a less messy way to handle this... especially if other packages are going to be using it
    """ Determines if it's a project is running in test mode and modifies behavior accordingly """

    @wraps(func)
    def check_test_mode(
        *args: Any, parent: Optional[QtWidgets.QWidget] = None, **kwargs: Any
    ) -> Optional[int]:
        """ Identify if package is in test mode and don't show the msgbox if it is"""
        msg = func(*args, **kwargs)
        if _TEST_MODE and parent:
            parent._msgbox = msg
            return None
        elif _TEST_MODE:
            raise AttributeError(
                f"Test mode for {func.__name__} requires specification of a parent object"
            )
        else:
            return msg.exec_()

    return check_test_mode


@test_mode_wrapper
def popup_message(
    txt: str, mtype: str = "info", ok_cancel: bool = False, default: str = "ok"
) -> int:
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
    """
    Line edit widget with autocompletion

    Parameters
    ----------
    parent
        The parent widget for the object

    Attributes
    ----------
    suggestions
        The list of possible suggestions for the completer

    See Also
    --------
    See PySide2.QtWidgets.QLineEdit for additional methods and attributes
    """

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)
        completer = QtWidgets.QCompleter()
        completer.setModel(QtGui.QStandardItemModel())
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.setCompleter(completer)

    @property
    def suggestions(self) -> List[str]:
        """ Get the list of possible suggestions for the widget """
        completion_model = self.completer().model()
        return [
            completion_model.item(i).text() for i in range(completion_model.rowCount())
        ]

    @suggestions.setter
    def suggestions(self, suggestions: Iterable[str]) -> None:
        """ Set the list of possible suggestions for the widget """
        completion_model = self.completer().model()
        completion_model.clear()
        for suggestion in suggestions:
            item = QtGui.QStandardItem(suggestion)
            completion_model.appendRow(item)


class QAutoCompleteDelegate(QtWidgets.QStyledItemDelegate):
    """
    Line edit delegate with autocompletion capabilities

    Notes
    -----
    The associated model for this delegate should have a method called
    'autocomplete_suggestions' that returns the possible list of suggestions
    for the completer

    See Also
    --------
    See PySide2.QtWidgets.QStyledItemDelegate for methods and attributes
    """

    def createEditor(
        self,
        parent: QtWidgets.QWidget,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex,
    ) -> QtWidgets.QWidget:
        """ Create the editor for the delegate """
        return QAutoCompleteLineEdit(parent)

    def setEditorData(
        self, editor: QAutoCompleteLineEdit, index: QtCore.QModelIndex
    ) -> None:
        """ Update the suggestions for the completer """
        val = index.model().data(index, Qt.EditRole)
        mod = index.model()
        try:
            suggestions = mod.autocomplete_suggestions(index)
        except AttributeError:
            raise MissingAutocompleteError(
                "Data model must have an 'autocomplete_suggestions' method"
            )
        editor.setText(val)
        editor.suggestions = suggestions

    def updateEditorGeometry(
        self,
        editor: QtWidgets.QWidget,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex,
    ) -> None:
        """ Make sure the editor geometry is correct """
        editor.setGeometry(option.rect)


class MissingAutocompleteError(Exception):
    """ Raise if the associated data model for the autocomplete doesn't have an 'autocomplete_suggestions' method """
