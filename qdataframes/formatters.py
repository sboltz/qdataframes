#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Functions/classes for formatting data

Created on 8/20/21

@author: SBoltz
"""
import pandas as pd
from pandas.errors import ParserError

from qdataframes.util import compose_docstring


_formatter_doc = """Parameters
----------
ser
    Series to format

Returns
-------
The converted series
"""


class FormatterMixIn:
    """ Helper methods for formatting table columns """

    @staticmethod
    @compose_docstring(format=_formatter_doc)
    def format_date(ser: pd.Series) -> pd.Series:
        """
        Convert series of timestamps to the date as a string

        {format}
        """
        ser = pd.to_datetime(ser)
        return ser.dt.date.astype(str)

    @staticmethod
    @compose_docstring(format=_formatter_doc)
    def format_str(ser: pd.Series) -> pd.Series:
        """
        Simply display the column as a str

        {format}
        """
        ser = ser.astype(str)
        # Deal with NaNs because they are a pain in the @$$
        ser = handle_str_nan(ser)
        return ser


_typer_doc = """Parameters
----------
x
    String to format

Returns
-------
The converted object
"""


class TyperMixIn:
    """ Helper methods for converting user inputs to appropriate types """

    @staticmethod
    @compose_docstring(typer=_typer_doc)
    def typer_str(x: str) -> str:
        """
        Remove NaNs and return

        {typer}
        """
        # I hate NaNs
        if x.lower() == "nan":
            x = ""
        return str(x)

    @staticmethod
    @compose_docstring(typer=_typer_doc)
    def typer_date(x: str) -> pd.Timestamp:
        """
        Convert a string to a pandas Timestamp

        {typer}
        """
        try:
            return pd.to_datetime(x)
        except (ValueError, ParserError):
            raise TypeConversionError(f"'{x}' is not a valid date string")


def handle_str_nan(ser: pd.Series) -> pd.Series:
    """
    Replace NaNs in str dtyped Series

    Parameters
    ----------
    ser
        Series to modify

    Returns
    -------
    The modified series
    """
    # Deal with NaNs because they are a pain in the @$$
    ser = ser.fillna("")
    ser.loc[ser.str.lower() == "nan"] = ""
    return ser


class TypeConversionError(ValueError):
    """
    Raised when data entered into a form/table cell cannot be converted correctly
    """