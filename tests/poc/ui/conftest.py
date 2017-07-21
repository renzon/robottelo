# coding: utf-8
"""Global ui package Configurations for py.test runner"""
import pytest as pytest

from robottelo.ui.org import Org


@pytest.fixture(scope='session')
def ui_org_manager(browser):
    return Org(browser)
