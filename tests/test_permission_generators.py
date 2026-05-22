#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Tests for UserWithRole and HasActionNeed permission generators."""

from __future__ import annotations

from flask_principal import Identity, Need, RoleNeed, UserNeed
from invenio_access import ActionNeed
from invenio_records_permissions import RecordPermissionPolicy
from invenio_search.engine import dsl

from oarepo_workflows.services.permissions.generators import HasActionNeed, UserWithRole

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _identity(user_id: int, *extra_needs: Need) -> Identity:
    """Build a minimal Identity with a UserNeed and optional extra needs."""
    i = Identity(user_id)
    i.provides.add(UserNeed(user_id))
    for need in extra_needs:
        i.provides.add(need)
    return i


# ===========================================================================
# HasActionNeed — pure Python tests (no Flask app context required)
# ===========================================================================


def test_has_action_need_repr():
    """repr() returns the canonical string representation."""
    gen = HasActionNeed("administration")
    assert repr(gen) == "HasActionNeed(administration)"


def test_has_action_need_str_equals_repr():
    """str() and repr() return the same value."""
    gen = HasActionNeed("administration")
    assert str(gen) == repr(gen)


def test_has_action_need_needs_contains_one_action_need():
    """needs() returns a list with a single ActionNeed."""
    gen = HasActionNeed("administration")
    needs = gen.needs()
    assert len(needs) == 1
    assert needs[0].method == "action"
    assert needs[0].value == "administration"


def test_has_action_need_needs_equals_action_need():
    """needs() result equals [ActionNeed(action)] by value."""
    gen = HasActionNeed("administration")
    assert gen.needs() == [ActionNeed("administration")]


def test_has_action_need_needs_different_actions_produce_different_needs():
    """Two generators with distinct actions produce distinct needs."""
    gen_a = HasActionNeed("administration")
    gen_b = HasActionNeed("curator")
    assert gen_a.needs() != gen_b.needs()
    assert gen_a.needs()[0].value == "administration"
    assert gen_b.needs()[0].value == "curator"


def test_has_action_need_excludes_are_empty():
    """excludes() returns an empty list (default Generator behaviour)."""
    gen = HasActionNeed("administration")
    assert gen.excludes() == []


def test_has_action_need_reference_receivers():
    """reference_receivers() returns the action name keyed under 'action_need'."""
    gen = HasActionNeed("administration")
    assert gen.reference_receivers() == [{"action_need": "administration"}]


def test_has_action_need_reference_receivers_for_different_action():
    """reference_receivers() reflects whichever action was passed to __init__."""
    gen = HasActionNeed("superuser-access")
    assert gen.reference_receivers() == [{"action_need": "superuser-access"}]


# ===========================================================================
# HasActionNeed — policy allows() tests (require Flask app + DB)
# ===========================================================================


def test_has_action_need_allows_when_identity_has_action(app, db):
    """Identity that carries the matching ActionNeed is allowed."""
    action_need = ActionNeed("administration")

    class MyPolicy(RecordPermissionPolicy):
        can_test = (HasActionNeed("administration"),)

    assert MyPolicy("test").allows(_identity(1, action_need)) is True


def test_has_action_need_denies_when_identity_lacks_action(app, db):
    """Identity without the ActionNeed is denied."""

    class MyPolicy(RecordPermissionPolicy):
        can_test = (HasActionNeed("administration"),)

    assert MyPolicy("test").allows(_identity(1)) is False


def test_has_action_need_denies_for_different_action(app, db):
    """Identity holding a *different* ActionNeed is still denied."""
    wrong_action = ActionNeed("curator")

    class MyPolicy(RecordPermissionPolicy):
        can_test = (HasActionNeed("administration"),)

    assert MyPolicy("test").allows(_identity(1, wrong_action)) is False


def test_has_action_need_multiple_users_only_privileged_allowed(app, db):
    """Only the identity that carries the action need is allowed; others are not."""
    action_need = ActionNeed("administration")

    class MyPolicy(RecordPermissionPolicy):
        can_test = (HasActionNeed("administration"),)

    assert MyPolicy("test").allows(_identity(1, action_need)) is True
    assert MyPolicy("test").allows(_identity(2)) is False
    assert MyPolicy("test").allows(_identity(3)) is False


# ===========================================================================
# UserWithRole — pure Python tests (no Flask app context required)
# ===========================================================================


def test_user_with_role_repr():
    """repr() returns the canonical string representation."""
    gen = UserWithRole("it-dep")
    assert repr(gen) == "UserWithRole(it-dep)"


def test_user_with_role_str_equals_repr():
    """str() and repr() return the same value."""
    gen = UserWithRole("it-dep")
    assert str(gen) == repr(gen)


# ===========================================================================
# UserWithRole — needs() tests (require Flask app + DB + role fixture)
# ===========================================================================


def test_user_with_role_needs_returns_role_need_when_role_exists(app, db, role):
    """needs() returns [RoleNeed(role.id)] when the role exists in the datastore."""
    gen = UserWithRole("it-dep")
    needs = gen.needs()
    # The 'role' fixture creates a role with id="it-dep"
    assert needs == [RoleNeed("it-dep")]


def test_user_with_role_needs_returns_empty_when_role_not_found(app, db):
    """needs() returns [] when the role does not exist in the datastore."""
    gen = UserWithRole("nonexistent-role-xyz")
    assert gen.needs() == []


# ===========================================================================
# UserWithRole — query_filter() tests (require Flask app + DB)
# ===========================================================================


def test_user_with_role_query_filter_match_all_when_identity_has_role(app, db):
    """query_filter returns match_all when the identity provides the role."""
    gen = UserWithRole("it-dep")
    i = _identity(1, RoleNeed("it-dep"))
    assert gen.query_filter(identity=i) == dsl.Q("match_all")


def test_user_with_role_query_filter_match_none_when_identity_lacks_role(app, db):
    """query_filter returns match_none when the identity does not have the role."""
    gen = UserWithRole("it-dep")
    assert gen.query_filter(identity=_identity(1)) == dsl.Q("match_none")


def test_user_with_role_query_filter_match_none_without_identity(app, db):
    """query_filter returns match_none when no identity is supplied."""
    gen = UserWithRole("it-dep")
    assert gen.query_filter() == dsl.Q("match_none")


def test_user_with_role_query_filter_match_none_for_different_role(app, db):
    """Identity carrying a *different* role still gets match_none."""
    gen = UserWithRole("it-dep")
    i = _identity(1, RoleNeed("other-role"))
    assert gen.query_filter(identity=i) == dsl.Q("match_none")


def test_user_with_role_query_filter_checks_role_name_not_id(app, db):
    """query_filter compares against the role name passed to __init__."""
    gen_a = UserWithRole("it-dep")
    gen_b = UserWithRole("finance")

    i = _identity(1, RoleNeed("it-dep"))

    assert gen_a.query_filter(identity=i) == dsl.Q("match_all")
    assert gen_b.query_filter(identity=i) == dsl.Q("match_none")


# ===========================================================================
# UserWithRole — reference_receivers() test (require Flask app + DB + role)
# ===========================================================================


def test_user_with_role_reference_receivers(app, db, role):
    """reference_receivers() returns a list containing the group's role ID."""
    gen = UserWithRole("it-dep")
    # The 'role' fixture creates a role with id="it-dep"
    receivers = gen.reference_receivers()
    assert receivers == [{"group": "it-dep"}]


# ===========================================================================
# UserWithRole — policy allows() tests (require Flask app + DB + role)
# ===========================================================================


def test_user_with_role_allows_when_identity_has_role(app, db, role):
    """Identity whose provides include the correct RoleNeed is allowed."""
    role_need = RoleNeed("it-dep")

    class MyPolicy(RecordPermissionPolicy):
        can_test = (UserWithRole("it-dep"),)

    assert MyPolicy("test").allows(_identity(1, role_need)) is True


def test_user_with_role_denies_when_identity_lacks_role(app, db, role):
    """Identity without the role is denied."""

    class MyPolicy(RecordPermissionPolicy):
        can_test = (UserWithRole("it-dep"),)

    assert MyPolicy("test").allows(_identity(1)) is False


def test_user_with_role_denies_for_different_role(app, db, role):
    """Identity carrying a *different* role is denied."""
    wrong_role = RoleNeed("other-role")

    class MyPolicy(RecordPermissionPolicy):
        can_test = (UserWithRole("it-dep"),)

    assert MyPolicy("test").allows(_identity(1, wrong_role)) is False


def test_user_with_role_multiple_users_only_member_allowed(app, db, role):
    """Among several identities, only the one with the correct role is allowed."""
    role_need = RoleNeed("it-dep")

    class MyPolicy(RecordPermissionPolicy):
        can_test = (UserWithRole("it-dep"),)

    assert MyPolicy("test").allows(_identity(1, role_need)) is True
    assert MyPolicy("test").allows(_identity(2)) is False
    assert MyPolicy("test").allows(_identity(3, RoleNeed("other-role"))) is False
