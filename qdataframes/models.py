#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generic data models
Created on 4/20/21

@author: SBoltz
"""

from typing import Optional, Union, Tuple, List, Any, Callable

import pandas as pd
from PySide6 import QtCore
from PySide6.QtCore import Qt

from qdataframes.util import update_display
from qdataframes.formatters import TypeConversionError
from qdataframes.qutil import popup_message


class BaseTableModel(QtCore.QAbstractTableModel):
    """
    A very basic Qt table model

    Parameters
    ----------
    data
        The data to display in the table
    parent
        Parent object of the model (should be a table view)

    Methods
    -------
    data
        Method to control what/how data is displayed
    rowCount
        Return the number of rows in the displayed table
    columnCount
        Return the number of columns in the displayed table
    headerData
        Return the row/column headers for the displayed table
    sort
        Sort the displayed table by the indicated column and order
    update_displayed_data
        Update the data that is displayed in the table
    _apply_behavior
        Apply the appropriate behavior to the index based on the specified role
    _register_roles
        Add the appropriate roles to the dictionary of role-based behaviors

    Attributes
    ----------
    _data
        The data attached to the model
    _displayed_data
        The data formatted as it should be displayed
    _role_based_behavior
        Listing of the appropriate behaviors for each Qt role
    """

    def __init__(self, data: pd.DataFrame, parent: Optional[QtCore.QObject] = None):
        super().__init__(parent=parent)
        self._data = data.copy()
        self._displayed_data = self._data
        self._role_based_behavior = {}
        self._register_roles()

    def data(self, index: QtCore.QModelIndex, role: Qt.ItemDataRole) -> Any:  # type: ignore[override]
        """
        Control what/how data is displayed

        Parameters
        ----------
        index
            The index of the cell to act upon
        role
            The current role

        Returns
        -------
        The expected behavior
        """
        # Should only ever refer to the data by iloc in this method, unless you
        # go specifically fetch the correct loc based on the iloc
        # breakpoint()
        return self._apply_behavior(index, role)

    def _apply_behavior(self, index: QtCore.QModelIndex, role: Qt.ItemDataRole) -> Any:
        """
        Apply the appropriate behavior to the index based on the specified role
        """
        row, col = index.row(), index.column()
        behavior = self._role_based_behavior.get(role, lambda r, c: None)
        return behavior(row, col)

    def _register_roles(self) -> None:
        """
        Add the appropriate roles to the dictionary of role-based behaviors
        """
        self._role_based_behavior[
            Qt.DisplayRole
        ] = lambda row, col: self._displayed_data.iloc[row, col]

    def rowCount(self, index: QtCore.QModelIndex) -> int:  # type: ignore[override]
        """
        Return the number of rows in the displayed table

        Parameters
        ----------
        index
            Index of the current cell (not used)
        """
        return len(self._displayed_data)

    def columnCount(self, index: QtCore.QModelIndex) -> int:  # type: ignore[override]
        """
        Return the number of columns in the displayed table

        Parameters
        ----------
        index
            Index of the current cell (not used)
        """
        return len(self._displayed_data.columns)

    def headerData(  # type: ignore[override]
        self, col: int, orientation: Qt.Orientation, role: Qt.ItemDataRole
    ) -> Union[None, str]:
        """
        Return the row/column headers for the displayed table

        Parameters
        ----------
        col
            Index of the row/column
        orientation
            Indicator of whether to retrieve the row or column header
        role
            The current role

        Returns
        -------
        The label for the column if the current role is Qt.DisplayRole, otherwise None
        """
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._displayed_data.columns[col]
        return None

    # def __getitem__(self, ind: Tuple[int, int]):   # TODO: I DO NOT UNDERSTAND WHAT PYTEST DOESN'T LIKE ABOUT THIS!
    #     if isinstance(ind, int):
    #         breakpoint()
    #     print(self.index(ind[0], ind[1]))
    #     return self.index(ind[0], ind[1])

    @update_display
    def sort(self, column: int, order: Optional[Qt.SortOrder] = None) -> None:
        """ Sort the model and display """
        # get column name and ascending status
        colname = self._displayed_data.columns[column]
        # Important: Qt sort order is backwards from pandas (AscendingOrder evaluates to False)
        order = not order if order is not None else not Qt.AscendingOrder
        # perform sorting on the underlying data
        self._data = self._data.sort_values(by=colname, ascending=order)

    def update_displayed_data(self) -> None:
        """ Update the data that is displayed in the table """
        self._displayed_data = self._data.copy()


class FormattedTableModel(BaseTableModel):
    """
    Table model with the ability to apply formatting to columns

    Parameters
    ----------
    data
        The data to display in the table
    table_meta
        A dataframe that describes how each column should be formatted. See
        notes for required columns.
    parent
        Parent object of the model (should be a table view)

    Methods
    -------
    formatter
        Retrieve the appropriate data formatter for the specified column
    update_displayed_data
        Update the data that is displayed in the table
    _validate_meta
        Make sure the table metadata is complete
    _format_columns
        Apply the desired formatting to each column of the data table

    Attributes
    ----------
    visible_columns
        The columns from the provided input dataframe that should actually be displayed in the table view
    display_formats
        The display format for each column in the table

    Notes
    -----
    The table meta requires the following columns:
        col_number
            The order in which the data columns should appear in the table
        display_format
            The format to be applied to the column prior to displaying
        visible
            Whether or not the column should be visible to the user

    See Also
    --------
    fipy.models.BaseTableModel
    """

    _meta_table_columns = {"col_number", "display_format", "visible"}

    def __init__(
        self,
        data: pd.DataFrame,
        table_meta: pd.DataFrame,
        parent: Optional[QtCore.QObject] = None,
    ):
        self._validate_meta(table_meta, data)
        self._table_meta = table_meta
        super().__init__(data, parent=parent)
        self.update_displayed_data()

    @property
    def visible_columns(self) -> pd.Index:
        """
        Return the columns that should be displayed in the table view

        Notes
        -----
        The columns will be returned in the order they should be displayed in
        the table
        """
        viz = self._table_meta.loc[self._table_meta["visible"]]
        return viz.sort_values(by="col_number").index

    @property
    def display_formats(self) -> pd.Series:
        """ Return the format for each column in the table """
        return self._table_meta["display_format"]

    def formatter(self, column: str) -> Callable:
        """
        Retrieve the appropriate data formatter for the specified column

        Parameters
        ----------
        column
            Column for which to retrieve the formatter

        Returns
        -------
        Method to use to apply the formatting
        """
        formatter = self.display_formats[column]
        return getattr(self, f"format_{formatter}")

    def _format_columns(self) -> pd.DataFrame:
        """
        Apply the desired formatting to each column of the data table

        Returns
        -------
        A copy of the data table with the appropriate formatting
        """
        df = self._data.copy()
        for col in self.display_formats.index:
            if col in df:
                df[col] = self.formatter(col)(df[col])
        return df.reindex(columns=self.visible_columns)

    def update_displayed_data(self) -> None:
        """ Update the data that is displayed in the table """
        self._displayed_data = self._format_columns()

    def _validate_meta(self, table_meta: pd.DataFrame, data: pd.DataFrame) -> None:
        """ Make sure the table metadata is complete """
        # Make sure the meta table isn't missing any columns
        if not set(table_meta.columns).issuperset(self._meta_table_columns):
            raise KeyError(
                "Table metadata missing the following columns: "
                f"{self._meta_table_columns - set(table_meta.columns)}"
            )
        # Make sure there's a record in the meta table for every column in the df
        if not set(table_meta.index).issuperset(data.columns):
            raise KeyError(
                "No metadata for the following data columns: "
                f"{set(data.columns) - set(table_meta.index)}"
            )
        # Make sure the meta table isn't missing any values
        e = ValueError("Table metadata cannot contain missing values")
        if table_meta.isna().any().any():
            raise e
        for col in table_meta:
            if (table_meta[col].astype(str) == "").any():
                raise e


class EditableTableModel(FormattedTableModel):
    """
    A formattable table model with the ability for the user to edit cells

    Parameters
    ----------
    data
        The data to display in the table
    table_meta
        A dataframe that describes how each column should be formatted. See
        notes for required columns.
    parent
        Parent object of the model (should be a table view)

    Methods
    -------
    type_converter
        Fetch the appropriate type converter for the specified column
    autocomplete_suggestions
        Return a list of autocomplete suggestions for the specified index
    setData
        Set the value for the given index
    flags
        Returns the flags for the index
    get_modified_data
        Return any rows that have been modified since the cache was emptied
    empty_modified_data_cache
        Empty the modified data cache
    _register_roles
        Add the appropriate roles to the dictionary of role-based behaviors
    _validate_edit_role
        Validate that the given index is really editable
    _validate_value
        Verify that the value is appropriate

    Attributes
    ----------
    editable_columns
        A list of indices of the columns that are editable
    data_types
        A list of the data type conversions to apply to user-entered data

    Notes
    -----
    The table meta requires the following columns:
        col_number
            The order in which the data columns should appear in the table
        display_format
            The format to be applied to the column prior to displaying
        visible
            Whether or not the column should be visible to the user
        data_type
            The type conversion to be applied to user-entered data
        editable
            Whether or not a column is user-editable
        autocomplete
            Whether or not a list of autocomplete options should be displayed

    See Also
    --------
    fipy.models.FormattedTableModel
    """

    _meta_table_columns = FormattedTableModel._meta_table_columns.union(
        {"data_type", "editable", "autocomplete"}
    )

    def __init__(
        self,
        data: pd.DataFrame,
        table_meta: pd.DataFrame,
        parent: Optional[QtCore.QObject] = None,
    ):
        super().__init__(data, table_meta=table_meta, parent=parent)
        self._modified_rows = set([])

    @property
    def editable_columns(self) -> pd.Series:
        """
        Return indices of the editable columns

        Notes
        -----
        It is important to note that this provides the indices of the columns
        as they are listed in the -displayed- table.
        """
        return self._table_meta.loc[self._table_meta["editable"]]["col_number"]

    @property
    def data_types(self) -> pd.Series:
        """ Return the data type conversions to apply to user-entered data """
        return self._table_meta.loc[self._table_meta["editable"]]["data_type"]

    def type_converter(self, column: str) -> Callable:
        """
        Fetch the appropriate type converter for the specified column

        Parameters
        ----------
        column
            Column for which to fetch the converter

        Returns
        -------
        Method for applying the type conversion
        """
        data_type = self._table_meta.loc[column, "data_type"]
        return getattr(self, f"typer_{data_type}")

    def _register_roles(self) -> None:
        """ Add the appropriate roles to the dictionary of role-based behaviors """
        super()._register_roles()
        self._role_based_behavior[
            Qt.EditRole
        ] = lambda row, col: self._displayed_data.iloc[row, col]

    def autocomplete_suggestions(self, index: QtCore.QModelIndex) -> List[str]:
        """
        Return a list of autocomplete suggestions for the specified index

        Parameters
        ----------
        index
            Index for which to retrieve the suggestions
        """
        column = index.column()
        col_name = self._displayed_data.columns[column]
        if self._table_meta.loc[col_name, "autocomplete"]:
            return list(self._displayed_data[col_name].unique())
        else:
            return list()

    def setData(  # type: ignore[override]
        self, index: QtCore.QModelIndex, value: str, role: Qt.ItemDataRole
    ) -> bool:
        """
        Set the value for the given index

        Parameters
        ----------
        index
            Index of the cell for which to set the data
        value
            Value to set to the cell
        role
            The current role

        Returns
        -------
        True if the value was set, else False
        """
        ind = self._validate_edit_role(index, role)
        if not ind:
            return False
        # Get the actual row and column of the table
        row = self._displayed_data.index[ind[0]]
        col = self._displayed_data.columns[ind[1]]
        # Verify the column is editable
        if col not in self.editable_columns:
            return False
        # Format the value
        try:
            value = self.type_converter(col)(value)
        except TypeConversionError as e:
            popup_message(txt=e.args[0], mtype="critical", parent=self)
            return True
        if self.validate_value(value, col):
            self._data.loc[row, col] = value
            self.update_displayed_data()
            self.dataChanged.emit(index, index)
            # Append to the list of modified rows
            self._modified_rows.add(row)
        return True

    def _validate_edit_role(
        self, index: QtCore.QModelIndex, role: Qt.ItemDataRole
    ) -> Optional[Tuple[int, int]]:
        """ Validate that the given index is really editable """
        row = index.row()
        col = index.column()
        cond1 = not index.isValid()
        cond2 = role != Qt.EditRole
        cond3 = row < 0 or row >= len(self._data.values)
        cond4 = col < 0 or col >= self._data_columns.size
        if any([cond1, cond2, cond3, cond4]):
            return None
        return row, col

    def validate_value(
        self, value: Any, column: str
    ) -> bool:  # TODO: I'm not going to delete this yet because it's clearly meant as a hook for something, but I'm not sure why this is here
        """ Verify that the value is appropriate """
        return True

    def flags(self, index: QtCore.QModelIndex) -> Qt.ItemFlag:  # type: ignore[override]
        """
        Return the flags for the index

        Parameters
        ----------
        index
            Index for which to get the flags
        """
        col = index.column()
        # This is a mess, but I kept getting infinite recursion otherwise...
        flags = super(self.__class__.__mro__[1], self).flags(index)  # type: ignore[arg-type]
        if col in self.editable_columns.values:
            flags |= Qt.ItemIsEditable
        flags |= Qt.ItemIsSelectable
        flags |= Qt.ItemIsEnabled
        flags |= Qt.ItemIsDragEnabled
        flags |= Qt.ItemIsDropEnabled
        return flags

    def get_modified_data(self) -> pd.DataFrame:
        """
        Return any rows that have been modified since the cache was emptied
        """
        return self._data.loc[list(self._modified_rows)]

    def empty_modified_data_cache(self) -> None:
        """ Empty the modified data cache """
        self._modified_rows = set([])
