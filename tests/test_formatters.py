#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the formatters

Created on 8/21/21

@author: SBoltz
"""

import pytest

import pandas as pd
import numpy as np

from PySide6 import QtWidgets

from qdataframes.formatters import (
    TypeConversionError,
    FormatterMixIn,
    TyperMixIn,
    handle_str_nan,
)


@pytest.fixture(scope="function")
def formatter(init_app: QtWidgets.QApplication) -> FormatterMixIn:
    """ Initialize the formatter mixin for testing """
    return FormatterMixIn()


@pytest.fixture(scope="function")
def typer(init_app: QtWidgets.QApplication) -> TyperMixIn:
    """ Initialize the typer mixin for testing """
    return TyperMixIn()


class TestFormatters:
    """ Tests for the different formatters attached to the FormatterMixIn class """

    def test_format_date(self, formatter: FormatterMixIn) -> None:
        """ Test that dates can be formatted properly """
        inp = pd.Series(
            [
                pd.Timestamp("2020-01-01"),
                pd.Timestamp("2020-01-02T01:03:04.000"),
                pd.Timestamp("2020-02-01"),
            ]
        )
        assert formatter.format_date(inp).equals(
            pd.Series(["2020-01-01", "2020-01-02", "2020-02-01"])
        )

    def test_format_str(self, formatter: FormatterMixIn) -> None:
        """ Test that strings can be formatted properly (and NaNs are removed) """
        inp = pd.Series(["abcd", "efg", None, "lmnop", np.NAN])
        assert formatter.format_str(inp).equals(
            pd.Series(["abcd", "efg", "", "lmnop", ""])
        )


class TestTypers:
    """ Tests for the different typers attached to the TyperMixIn """

    def test_typer_str(self, typer: TyperMixIn) -> None:
        """ Make sure it is possible to convert a str to a str (sans NaNs) """
        assert typer.typer_str("abcd") == "abcd"
        assert typer.typer_str("NaN") == ""

    @pytest.mark.parametrize(
        "date",
        (
            "11/1/2020",
            "2020-11-1",
            "2020-11-01T00:00:00",
            "11-1-2020",
            "11-01-20",
            "11/1/20",
            "20201101",
        ),
    )
    def test_typer_date(self, date: str, typer: TyperMixIn) -> None:
        """ Make sure it is possible to handle dates input in various formats """
        assert typer.typer_date(date) == pd.Timestamp("2020-11-01")

    @pytest.mark.parametrize(
        "date", ("abcd", "123456", "111111111", "2020-11-99", "True", "None")
    )
    def test_typer_date_bogus(self, date: str, typer: TyperMixIn) -> None:
        """ Make sure typer raises predictable error on bogus date input """
        with pytest.raises(TypeConversionError, match="not a valid date string"):
            typer.typer_date(date)


class TestMiscellaneous:
    """ Tests for miscellaneous formatting functions"""

    @pytest.mark.parametrize(
        "ser", (pd.Series([pd.NaT]), pd.Series([np.NAN]), pd.Series(["NaN"]))
    )
    def test_handle_str_nan(self, ser: pd.Series) -> None:
        """
        Make sure function for removing NaNs from str Series works as
        advertised
        """
        out = handle_str_nan(ser)
        assert (out == "").all()
