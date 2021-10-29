#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for QT utilities

Created on 4/20/21

@author: SBoltz
"""
import pytest
from typing import List

import pandas as pd


from PySide2 import QtWidgets, QtCore
from PySide2.QtCore import Qt

from qdataframes.qutil import (
    QAutoCompleteDelegate,
    QAutoCompleteLineEdit,
    MissingAutocompleteError,
)
from qdataframes import EditableTableModel, BaseTableModel
from qdataframes.formatters import TyperMixIn, FormatterMixIn


class MockTableView(QtWidgets.QMainWindow):
    """ Very simple tableview for testing """

    def __init__(self) -> None:
        super().__init__()
        self.tableView = QtWidgets.QTableView(self)
        self.tableView.setItemDelegate(QAutoCompleteDelegate(self.tableView))


class TestAutoCompleteDelegate:
    """ Make sure that the QAutoCompleteDelegate works as intended """

    data = pd.DataFrame([["a", 1], ["b", 2], ["c", 3]], columns=["Letter", "Number"])
    suggestions = ["abcd", "bacd", "bcde", "defg", "aaae"]

    @pytest.fixture(scope="class")
    def thing_requiring_autocomplete(
        self, init_app: QtWidgets.QApplication
    ) -> MockTableView:
        """ Return something that needs autocomplete functionality """
        specs = {
            "Letter": {
                "display_format": "str",
                "editable": True,
                "col_number": 0,
                "autocomplete": True,
                "data_type": "str",
                "visible": True,
            },
            "Number": {
                "display_format": "str",
                "editable": True,
                "col_number": 1,
                "autocomplete": True,
                "data_type": "int",
                "visible": True,
            },
        }
        suggestions = self.suggestions

        class Autocompletable(EditableTableModel, TyperMixIn, FormatterMixIn):
            """ Simple model that returns predictable autocomplete suggestions """

            def autocomplete_suggestions(self, index: QtCore.QModelIndex) -> List[str]:
                """ Return a few suggestions """
                return suggestions

        tv = MockTableView()
        tv.tableView.setModel(
            Autocompletable(
                self.data,
                table_meta=pd.DataFrame(specs, columns=specs.keys()).transpose(),
                parent=tv.tableView,
            )
        )
        return tv

    @pytest.fixture(scope="class")
    def bad_autocompleting_object(
        self, init_app: QtWidgets.QApplication
    ) -> MockTableView:
        """ Return something that needs autocomplete, but doesn't provide the required suggestions """
        tv = MockTableView()
        tv.tableView.setModel(BaseTableModel(self.data, parent=tv.tableView))
        return tv

    def test_delegate_editor_type(
        self, thing_requiring_autocomplete: MockTableView
    ) -> None:
        """ Make sure the delegate has an autocompleting LineEdit as its underlying object """
        # thing_requiring_autocomplete.tableView
        editor = thing_requiring_autocomplete.tableView.itemDelegate().createEditor(
            thing_requiring_autocomplete,
            QtWidgets.QStyleOptionViewItem.ViewItemFeature.None_,
            index=QtCore.QModelIndex(),
        )
        assert isinstance(editor, QAutoCompleteLineEdit)

    def test_completion_filtering(self, init_app: QtWidgets.QApplication) -> None:
        """ Make sure the settings on the completer will filter as expected """
        # This test might be pointless
        editor = QAutoCompleteLineEdit()
        completer = editor.completer()
        assert completer.caseSensitivity() == Qt.CaseInsensitive
        assert completer.filterMode() == Qt.MatchContains

    def test_delegate_has_autocomplete_vals(
        self, thing_requiring_autocomplete: MockTableView
    ) -> None:
        """
        Make sure the autocomplete delegate has the correct suggestions
        """
        # Create an editor to pass to an itemDelegate (easiest way to do this...)
        editor = QAutoCompleteLineEdit()
        # Pass the editor to the item delegate
        ind = thing_requiring_autocomplete.tableView.model().index(0, 0)
        thing_requiring_autocomplete.tableView.itemDelegate().setEditorData(
            editor, index=ind
        )
        assert set(editor.suggestions) == set(self.suggestions)

    def test_delegate_has_no_suggestions(
        self, bad_autocompleting_object: MockTableView
    ) -> None:
        """
        Verify behaves gracefully if can't access 'autocomplete_suggestions'
        """
        # Create an editor to pass to an itemDelegate (easiest way to do this...)
        editor = QAutoCompleteLineEdit()
        # Attempt to set data on the editor
        ind = bad_autocompleting_object.tableView.model().index(0, 0)
        with pytest.raises(
            MissingAutocompleteError,
            match="Data model must have an 'autocomplete_suggestions' method",
        ):
            bad_autocompleting_object.tableView.itemDelegate().setEditorData(
                editor, index=ind
            )
