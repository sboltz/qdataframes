#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for table models

Created on 5/8/21

@author: SBoltz
"""

import pytest
from typing import Dict

import pandas as pd
from PySide2.QtCore import Qt

from qdataframes import BaseTableModel, EditableTableModel, FormattedTableModel
from qdataframes.formatters import FormatterMixIn, TyperMixIn


# --- Helper functions/classes
# noinspection PyMissingTypeHints
class FormatModel(FormattedTableModel, FormatterMixIn):
    """ Simple FormattedTableModel w/ necessary formatting method(s) """

    @staticmethod
    def format_two_decimals(ser: pd.Series) -> pd.Series:
        """ Format a series of floats as strings with two decimal points """

        # noinspection PyMissingOrEmptyDocstring
        def format_two_decimals(val: float) -> str:
            return f"{val:0.2f}"

        return ser.apply(format_two_decimals)  # type: ignore[return-value]


# --- Fixtures
@pytest.fixture(scope="module")
def simple_df() -> pd.DataFrame:
    """ Return a test df of data """
    return pd.DataFrame(
        [
            ["a", 1, pd.Timestamp("2021-01-01"), "this"],
            ["d", 2, pd.Timestamp("2021-01-02"), "is"],
            ["b", 3, pd.Timestamp("2021-02-01"), "not"],
            ["c", 4, pd.Timestamp("2021-03-01"), "visible"],
        ],
        columns=["Letter", "Number", "Date", "Extra"],
    )


@pytest.fixture(scope="module")
def data_col_numbers(simple_df: pd.DataFrame) -> Dict[str, int]:
    """ Map the column names to their index """
    return {y: x for x, y in enumerate(simple_df.columns)}


@pytest.fixture(scope="class")
def meta_df() -> pd.DataFrame:
    """ Return a metadata table"""
    return pd.DataFrame(
        [
            # col_name  col_number  display_format  visible
            ["Letter", 1, "str", True],
            ["Number", 2, "two_decimals", True],
            ["Date", 0, "date", True],
            ["Extra", -9, "str", False],
        ],
        columns=["col_name", "col_number", "display_format", "visible"],
    ).set_index("col_name")


# noinspection PyMissingTypeHints
class TestBaseTableModel:
    """ Tests for the base table model """

    index0 = (0, 0)
    index1 = (0, 1)

    @pytest.fixture(scope="class")
    def base_table(self, simple_df: pd.DataFrame) -> BaseTableModel:
        """ Return a BaseTableModel """
        return BaseTableModel(simple_df)

    def test_displayed_data(
        self, base_table: BaseTableModel, simple_df: pd.DataFrame
    ) -> None:
        """ Verify that the displayed data is simply the input DataFrame """
        assert (base_table._displayed_data == simple_df).all().all()

    def test_data(self, base_table: BaseTableModel, simple_df: pd.DataFrame) -> None:
        """ Verify that the data at a given index matches the input DataFrame """
        ind = base_table.index(*self.index0)
        assert base_table.data(ind, Qt.DisplayRole) == simple_df.iloc[self.index0]
        ind = base_table.index(*self.index1)
        assert base_table.data(ind, Qt.DisplayRole) == simple_df.iloc[self.index1]

    def test_data_non_display_role(self, base_table: BaseTableModel) -> None:
        """ Verify that the table does nothing (and doesn't except) if given a role other than DisplayRole """
        # Implicitly tests BaseTableModel.role_based_behavior and BaseTableModel.register_roles
        ind = base_table.index(*self.index0)
        assert base_table.data(ind, Qt.EditRole) is None

    def test_table_dimensions(
        self, base_table: BaseTableModel, simple_df: pd.DataFrame
    ) -> None:
        """ Verify the data dimensions match the dimensions of the input DataFrame"""
        ind = base_table.index(*self.index0)
        assert base_table.rowCount(ind) == len(simple_df)
        assert base_table.columnCount(ind) == len(simple_df.columns)

    def test_header(self, base_table: BaseTableModel, simple_df: pd.DataFrame) -> None:
        """ Verify the table header matches the DataFrame header """
        for ind, col in enumerate(simple_df.columns):
            assert base_table.headerData(ind, Qt.Horizontal, Qt.DisplayRole) == col

    def test_row_name(self, base_table: BaseTableModel) -> None:
        """ Verify that the row name is not populated/shown """
        assert base_table.headerData(0, Qt.Vertical, Qt.DisplayRole) is None

    def test_header_non_display_role(self, base_table: BaseTableModel) -> None:
        """ Verify that the table header returns None if not in DisplayRole """
        assert base_table.headerData(0, Qt.Horizontal, Qt.EditRole) is None

    def test_sort(
        self, base_table: BaseTableModel, data_col_numbers: Dict[str, int]
    ) -> None:
        """ Verify that table sorting works predictably... """
        # Should sort ascending
        base_table.sort(column=data_col_numbers["Letter"])
        assert base_table._data["Letter"].tolist() == ["a", "b", "c", "d"]
        # Should sort descending
        base_table.sort(column=data_col_numbers["Letter"], order=Qt.DescendingOrder)
        assert base_table._data["Letter"].tolist() == ["d", "c", "b", "a"]
        # Should sort ascending
        base_table.sort(column=data_col_numbers["Letter"], order=Qt.AscendingOrder)
        assert base_table._data["Letter"].tolist() == ["a", "b", "c", "d"]
        # Should sort ascending (on the Number column)
        base_table.sort(column=data_col_numbers["Number"])
        assert base_table._data["Number"].tolist() == [1, 2, 3, 4]

    # def test_getter(self, base_table, simple_df):  <- >:(
    #     """ Verify shortcut for getting a cell's index """
    #     row, col = self.index0
    #     ind = base_table[row, col]
    #     assert ind.row() == row
    #     assert ind.column() == col
    #     assert ind.model() == base_table
    #     assert ind.data() == simple_df.iloc[self.index0]


# noinspection PyMissingTypeHints
class TestFormattedTableModel:
    """ Tests for a table model that allows formatting for columns """

    expected_display = {"Letter": "a", "Number": "1.00", "Date": "2021-01-01"}
    expected_data = {
        "Letter": "a",
        "Number": 1,
        "Date": pd.Timestamp("2021-01-01"),
        "Extra": "this",
    }

    @pytest.fixture(scope="class")
    def format_table(
        self, meta_df: pd.DataFrame, simple_df: pd.DataFrame
    ) -> FormatModel:
        """ Return a FormattedTableModel """
        return FormatModel(simple_df, table_meta=meta_df)

    @pytest.fixture
    def missing_meta_col(self, meta_df: pd.DataFrame) -> pd.DataFrame:
        """ Return a meta table with a missing column """
        return meta_df[["visible", "display_format"]]

    @pytest.fixture
    def missing_meta_val(self, meta_df: pd.DataFrame) -> pd.DataFrame:
        """ Return a meta df that is missing a value """
        df = meta_df.copy()
        df.loc["Date", "display_format"] = ""
        return df

    @pytest.fixture
    def extra_data_col(self, simple_df: pd.DataFrame) -> pd.DataFrame:
        """ Return a meta df that has a record for an extra data column """
        df = simple_df.copy()
        df["Stuff"] = "hello"
        return df

    def test_missing_meta_column(
        self, missing_meta_col: pd.DataFrame, simple_df: pd.DataFrame
    ) -> None:
        """ Verify errors predictably on a missing column in the meta table """
        with pytest.raises(
            KeyError, match="missing the following columns: {'col_number'}"
        ):
            FormatModel(simple_df, table_meta=missing_meta_col)

    def test_missing_meta_value(
        self, missing_meta_val: pd.DataFrame, simple_df: pd.DataFrame
    ) -> None:
        """ Verify errors predictably if there is a missing value in the meta table """
        with pytest.raises(ValueError, match="missing values"):
            FormatModel(simple_df, table_meta=missing_meta_val)

    def test_missing_data_col(
        self, meta_df: pd.DataFrame, extra_data_col: pd.DataFrame
    ) -> None:
        """ Verify errors predictably if the meta table is missing one of the data columns """
        with pytest.raises(
            KeyError, match="No metadata for the following data columns: {'Stuff'}"
        ):
            FormatModel(extra_data_col, table_meta=meta_df)

    def test_extra_data_col(
        self, meta_df: pd.DataFrame, simple_df: pd.DataFrame
    ) -> None:
        """ Verify an extra data column in the meta table doesn't raise """
        FormatModel(simple_df[["Letter", "Number", "Extra"]], table_meta=meta_df)

    def test_visible(
        self, format_table: FormattedTableModel, simple_df: pd.DataFrame
    ) -> None:
        """
        Verify 'displayed' table has the correct visible columns (and that the
        'data' table has columns)
        """
        assert set(format_table._displayed_data.columns) == {"Letter", "Number", "Date"}
        assert set(format_table._data.columns) == set(simple_df.columns)

    def test_formatting(self, format_table: FormattedTableModel) -> None:
        """ Verify the 'displayed' table is properly formatted (and the underlying data weren't touched) """
        row = format_table._displayed_data.iloc[0]
        for key, val in self.expected_display.items():
            assert row[key] == val
        row = format_table._data.iloc[0]
        for key, val in self.expected_data.items():
            assert row[key] == val

    def test_missing_formatter(
        self, meta_df: pd.DataFrame, simple_df: pd.DataFrame
    ) -> None:
        """ Verify that a missing formatter fails early """
        with pytest.raises(
            AttributeError,
            match="'FormattedTableModel' object has no attribute 'format_str'",
        ):
            FormattedTableModel(simple_df, table_meta=meta_df)

    def test_column_order(
        self, format_table: FormattedTableModel, meta_df: pd.DataFrame
    ) -> None:
        """ Verify that the column order matches what is in the meta data """
        for col, num in meta_df.loc[meta_df.visible]["col_number"].iteritems():
            assert format_table._displayed_data.columns[num] == col


# noinspection PyMissingTypeHints
class TestEditableTableModel:
    """ Tests for a table that allows editing of cell values """

    @pytest.fixture(scope="class")
    def editable_meta(self, meta_df: pd.DataFrame) -> pd.DataFrame:
        """ Adapt the existing meta table to include editing information """
        meta_df = meta_df.copy()
        meta_df["editable"] = meta_df.index.map(
            {"Letter": True, "Number": False, "Date": True, "Extra": False}
        )
        meta_df["autocomplete"] = meta_df.index.map(
            {"Letter": True, "Number": False, "Date": False, "Extra": False}
        )
        meta_df["data_type"] = meta_df.index.map(
            {"Letter": "str", "Number": "int", "Date": "date", "Extra": "str"}
        )
        return meta_df

    @pytest.fixture(scope="class")
    def editable_col_numbers(self, editable_meta: pd.DataFrame) -> pd.Series:
        """ Return a mapping of columns to their index number """
        return editable_meta["col_number"]

    @pytest.fixture(scope="function")
    def editable_table(
        self, editable_meta: pd.DataFrame, simple_df: pd.DataFrame
    ) -> EditableTableModel:
        """ Create an editable table """

        class EditModel(EditableTableModel, FormatModel, TyperMixIn):
            """ Editable model with formatters """

        return EditModel(simple_df, table_meta=editable_meta)

    @pytest.fixture(scope="function")
    def edit_table(
        self, editable_table: EditableTableModel, editable_col_numbers: pd.Series
    ) -> EditableTableModel:
        """ Edit each of the visible columns in the table """
        ind = editable_table.index(0, editable_col_numbers["Date"])
        editable_table.setData(ind, "2021-05-09", Qt.EditRole)
        ind = editable_table.index(0, editable_col_numbers["Letter"])
        editable_table.setData(ind, "z", Qt.EditRole)
        # This shouldn't have any effect because "Number" is noneditable
        ind = editable_table.index(0, editable_col_numbers["Number"])
        editable_table.setData(ind, "100", Qt.EditRole)
        return editable_table

    def test_displayed_table_edits(self, edit_table: EditableTableModel) -> None:
        """ Verify the values in the displayed table match the user input """
        row = edit_table._displayed_data.iloc[0]
        assert row["Date"] == "2021-05-09"
        assert row["Letter"] == "z"

    def test_data_table_edits(self, edit_table: EditableTableModel) -> None:
        """ Verify the values in the data table were updated and are the correct type """
        row = edit_table._data.iloc[0]
        assert row["Date"] == pd.Timestamp("2021-05-09")
        assert row["Letter"] == "z"

    def test_unedited(self, edit_table: EditableTableModel) -> None:
        """ Verify the value in the 'Number' column wasn't changed """
        displayed = edit_table._displayed_data.iloc[0]["Number"]
        assert displayed == "1.00"
        data = edit_table._data.iloc[0]["Number"]
        assert data == 1

    def test_autocomplete_suggestions(
        self,
        editable_table: EditableTableModel,
        editable_col_numbers: pd.Series,
        simple_df: pd.DataFrame,
    ) -> None:
        """ Verify the autocomplete suggestions match expectations """
        ind = editable_table.index(0, editable_col_numbers["Letter"])
        suggestions = editable_table.autocomplete_suggestions(ind)
        assert set(suggestions) == set(simple_df["Letter"])

    def test_autocomplete_suggestions_not_autocompletable(
        self, editable_table: EditableTableModel, editable_col_numbers: pd.Series
    ) -> None:
        """ Verify no suggestions return if autocomplete=False """
        ind = editable_table.index(0, editable_col_numbers["Number"])
        suggestions = editable_table.autocomplete_suggestions(ind)
        assert len(suggestions) == 0

    def test_get_modified_data(self, edit_table: EditableTableModel) -> None:
        """ Make sure it is possible to grob the rows that were modified """
        modified = edit_table.get_modified_data()
        assert len(modified) == 1
        # Make sure it returned the row that was actually changed
        assert modified.iloc[0]["Letter"] == "z"

    def test_empty_modified_data_cache(self, edit_table: EditableTableModel) -> None:
        """ Make sure you can empty the modified data cache """
        edit_table.empty_modified_data_cache()
        assert len(edit_table.get_modified_data()) == 0
