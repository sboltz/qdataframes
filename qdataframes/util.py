#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Various Utilities

Created on 8/20/21

@author: SBoltz
"""
import textwrap
from typing import Callable, Union, Sequence, Any
from functools import wraps

from PySide6.QtWidgets import QTableView


def update_display(func: Callable) -> Callable:
    """
    (correctly) Update the data in a tableView
    """

    @wraps(func)
    def update(table: QTableView, *args: Any, **kwargs: Any) -> None:
        """ Perform the update """
        table.layoutAboutToBeChanged.emit()
        func(table, *args, **kwargs)
        table.update_displayed_data()
        table.layoutChanged.emit()

    return update


def compose_docstring(**kwargs: Union[str, Sequence[str]]) -> Callable:
    """
    Compose docstrings by substituting variables (similar to f-strings)

    This allows components of docstrings which are often repeated to be
    specified in a single place. Values provided to this function should
    have string keys and string or list values. Keys are found in curly
    brackets in the wrapped functions docstring and their values are
    substituted with proper indentation.

    Notes
    -----
    A function's docstring can be accessed via the `__docs__` attribute.

    Examples
    --------
    @compose_docstring(some_value='10')
    def example_function():
        '''
        Some useful description

        The following line will be the string '10':
        {some_value}
        '''
    """

    def _wrap(func: Callable) -> Callable:
        """ Do black magic w/ the docstring """

        docstring = func.__doc__
        # iterate each provided value and look for it in the docstring
        for key, value in kwargs.items():
            value = value if isinstance(value, str) else "\n".join(value)
            # strip out first line if needed
            value = value.lstrip()
            search_value = "{%s}" % key
            # find all lines that match values
            lines = [x for x in docstring.split("\n") if search_value in x]
            for line in lines:
                # determine number of spaces used before matching character
                spaces = line.split(search_value)[0]
                # ensure only spaces precede search value
                assert set(spaces) == {" "}
                new = textwrap.indent(textwrap.dedent(value), spaces)
                docstring = docstring.replace(line, new)

        func.__doc__ = docstring
        return func

    return _wrap
