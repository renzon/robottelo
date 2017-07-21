# coding: utf-8
"""Global poc package Configurations for py.test runner"""
import logging

import pytest as pytest
from fauxfactory import gen_string
from nailgun import entities

from robottelo.config import settings as _settings
from robottelo.ui.browser import browser as lib_browser, DockerBrowser
from robottelo.ui.session import Session

logger = logging.getLogger(__name__)


@pytest.fixture(scope='session')
def settings():
    _settings.configure()
    return _settings


@pytest.fixture(scope='session')
def ui_user(settings, ui_org):
    username = gen_string('alpha')
    try:
        user_obj = entities.User(
            firstname='Robottelo User {0}'.format(username),
            login=username,
            password=settings.server.admin_password,
            admin=True,
            default_organization=ui_org
        ).create()
    except Exception as e:
        logger.warn('Unable to create session_user: %s', str(e))
    else:
        # Need to reassign password once it is not returned from server
        user_obj.password = settings.server.admin_password
        yield user_obj
        user_obj.delete(synchronous=False)


@pytest.fixture(scope='session')
def browser(settings):
    if settings.browser == 'docker':
        _docker_browser = DockerBrowser()
        _docker_browser.start()
        browser_obj = _docker_browser.webdriver
        clean_up = _docker_browser.stop
    else:
        browser_obj = lib_browser(settings.browser, settings.webdriver)
        clean_up = browser_obj.quit
    browser_obj.maximize_window()
    browser_obj.get(settings.server.get_url())
    # Workaround 'Certificate Error' screen on Microsoft Edge
    if (settings.webdriver == 'edge' and
            'Certificate Error' in browser_obj.title or
            'Login' not in browser_obj.title):
        browser_obj.get(
            "javascript:document.getElementById('invalidcert_continue')"
            ".click()"
        )

    yield browser_obj
    clean_up()


@pytest.fixture(scope='session')
def session(browser, ui_user):
    session = Session(browser, user=ui_user.login, password=ui_user.password)
    session.login()
    yield session
    session.logout()


@pytest.fixture(scope='session')
def ui_org():
    """Create a org once to be used among all tests. Tests must not edit
    this organization once it is shared. User 'local_ui_org' on this case"""
    return local_ui_org()


@pytest.fixture
def local_ui_org():
    """Create organization for each test. It can be edited once it is not
    shared among tests"""

    return entities.Organization().create()
