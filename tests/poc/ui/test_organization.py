# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from robottelo.datafactory import generate_strings_list
from robottelo.decorators import tier1
from robottelo.ui.factory import make_org
from robottelo.ui.locators import locators


@tier1
def test_positive_search_autocomplete(session, local_ui_org, ui_org_manager):
    """Search for an organization can be auto-completed by partial
    name

    :id: f3c492ab-46fb-4b1d-b5d5-29a82385d681

    :expectedresults: Auto search for created organization works as
        intended

    :CaseImportance: Critical
    """

    part_string = local_ui_org.name[:3]
    auto_search = ui_org_manager.auto_complete_search(
        session.nav.go_to_org,
        locators['org.org_name'], part_string, local_ui_org.name,
        search_key='name')
    assert auto_search is not None


@tier1
@pytest.mark.parametrize('org_name', generate_strings_list())
def test_positive_create_with_name(session, org_name, ui_org_manager):
    """Create organization with valid name only.

    :id: bb5c6400-e837-4e3b-add9-bab2c0b826c9

    :expectedresults: Organization is created, label is auto-generated

    :CaseImportance: Critical
    """
    make_org(session, org_name=org_name)
    assert ui_org_manager.search(org_name) is not None
