#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test setup

Created on 8/20/21

@author: SBoltz
"""

import pytest

from PySide6 import QtWidgets


@pytest.fixture(scope="session")
def init_app() -> QtWidgets.QApplication:  # type: ignore[misc]
    """ Initialize FiPy """
    app = QtWidgets.QApplication()
    yield app
    del app
