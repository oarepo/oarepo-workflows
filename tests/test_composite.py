#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-workflows is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Tests for RequireAll and BooleanPermissionPolicyMixin."""

from __future__ import annotations

from typing import Any

import pytest
from flask_principal import Identity, Need, UserNeed
from invenio_records_permissions import RecordPermissionPolicy
from invenio_records_permissions.generators import Generator

from oarepo_workflows.services.permissions.composite import (
    BooleanPermissionPolicyMixin,
    HashableList,
    RequireAll,
)

# ---------------------------------------------------------------------------
# Helper generators (pure Python, no Flask context required)
# ---------------------------------------------------------------------------


class FixedNeedsGenerator(Generator):
    """Generator that always returns a fixed list of needs."""

    def __init__(self, *needs: Need) -> None:
        """Initialize with the fixed list of needs."""
        self._needs = list(needs)

    def needs(self, **_kwargs: Any):
        """Return the fixed list of needs."""
        return list(self._needs)

    def excludes(self, **_kwargs: Any):
        """Return no excludes."""
        return []


class FixedExcludesGenerator(Generator):
    """Generator with configurable needs *and* excludes."""

    def __init__(self, needs=(), excludes=()):
        """Initialize with the fixed list of needs and excludes."""
        self._needs = list(needs)
        self._excludes = list(excludes)

    def needs(self, **_kwargs: Any):
        """Return the fixed list of needs."""
        return list(self._needs)

    def excludes(self, **_kwargs: Any):
        """Return the fixed list of excludes."""
        return list(self._excludes)


class EmptyGenerator(Generator):
    """Generator that returns no needs and no excludes."""

    def needs(self, **_kwargs: Any):
        """Return no needs."""
        return []

    def excludes(self, **_kwargs: Any):
        """Return no excludes."""
        return []


# ---------------------------------------------------------------------------
# Base policy used by all allows() tests (defines the module-level mixin)
# ---------------------------------------------------------------------------


class _CompositeTestPolicy(BooleanPermissionPolicyMixin, RecordPermissionPolicy):
    """Concrete policy for composite tests.

    Invenio's ``BasePermissionPolicy.__init__`` automatically injects
    ``permission_policy=self`` into ``over``, which ``RequireAll`` uses to
    verify the policy type at needs-collection time.
    """


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _identity(user_id: int, *extra_needs: Need) -> Identity:
    """Build a minimal Identity with a UserNeed and any extra needs."""
    i = Identity(user_id)
    i.provides.add(UserNeed(user_id))
    for need in extra_needs:
        i.provides.add(need)
    return i


# ===========================================================================
# HashableList
# ===========================================================================


def test_hashable_list_is_hashable():
    """HashableList must be hashable so it can be stored inside a Need."""
    hl = HashableList([1, 2, 3])
    assert isinstance(hash(hl), int)


def test_hashable_list_hash_is_stable_for_same_instance():
    """The hash must be the same across multiple calls on the same instance."""
    hl = HashableList([10, 20, 30])
    assert hash(hl) == hash(hl)


def test_hashable_list_different_instances_have_different_hashes():
    """Two instances with identical contents must produce different hashes."""
    hl1 = HashableList([1, 2, 3])
    hl2 = HashableList([1, 2, 3])
    # Hash is identity-based, so two distinct objects differ.
    assert hash(hl1) != hash(hl2)


def test_hashable_list_equality_is_identity_based():
    """Two instances with the same contents must NOT be equal."""
    hl1 = HashableList([1, 2, 3])
    hl2 = HashableList([1, 2, 3])
    assert hl1 != hl2


def test_hashable_list_instance_equals_itself():
    """An instance must be equal to itself."""
    hl = HashableList([1, 2, 3])
    assert hl == hl


def test_hashable_list_can_be_used_in_set():
    """Two distinct HashableLists with equal contents must coexist in a set."""
    hl1 = HashableList([1, 2, 3])
    hl2 = HashableList([1, 2, 3])
    s = {hl1, hl2}
    assert len(s) == 2


def test_hashable_list_still_behaves_like_a_list():
    """HashableList must preserve normal list behaviour."""
    hl = HashableList([10, 20, 30])
    assert len(hl) == 3
    assert hl[0] == 10
    assert list(hl) == [10, 20, 30]
    hl.append(40)
    assert hl[-1] == 40


def test_hashable_list_can_wrap_need_objects():
    """A Need stored inside a HashableList should be retrievable."""
    g = FixedNeedsGenerator(UserNeed(1))
    hl = HashableList([g])
    assert hl[0] is g


# ===========================================================================
# RequireAll - error paths (no Flask context required)
# ===========================================================================


def test_require_all_raises_value_error_without_policy():
    """needs() must raise ValueError when no permission_policy key is present in context."""
    gen = RequireAll(FixedNeedsGenerator(UserNeed(1)))
    with pytest.raises(ValueError, match="Permission policy class is not set up in context"):
        gen.needs()


def test_require_all_raises_value_error_with_other_context_keys():
    """needs() must raise ValueError even when other keys are present but not 'permission_policy'."""
    gen = RequireAll(FixedNeedsGenerator(UserNeed(1)))
    with pytest.raises(ValueError, match="Permission policy class is not set up in context"):
        gen.needs(record={}, identity=None)


def test_require_all_raises_type_error_for_plain_policy():
    """needs() must raise TypeError when policy is a plain RecordPermissionPolicy."""
    gen = RequireAll(FixedNeedsGenerator(UserNeed(1)))
    wrong_policy = RecordPermissionPolicy("read")
    with pytest.raises(
        TypeError,
        match="Permission policy class is not a BooleanPermissionPolicyMixin",
    ):
        gen.needs(permission_policy=wrong_policy)


# ===========================================================================
# RequireAll - repr / str (no Flask context required)
# ===========================================================================


def test_require_all_repr_single_inner_generator():
    g = FixedNeedsGenerator(UserNeed(1))
    gen = RequireAll(g)
    expected = f"RequireAll({g!r})"
    assert repr(gen) == expected


def test_require_all_str_equals_repr():
    g = FixedNeedsGenerator(UserNeed(1))
    gen = RequireAll(g)
    assert str(gen) == repr(gen)


def test_require_all_repr_multiple_inner_generators():
    g1 = FixedNeedsGenerator(UserNeed(1))
    g2 = FixedNeedsGenerator(UserNeed(2))
    gen = RequireAll(g1, g2)
    expected = f"RequireAll({g1!r}, {g2!r})"
    assert repr(gen) == expected


# ===========================================================================
# RequireAll - needs() with valid policy (no Flask context needed
# because we only call gen.needs() directly, not policy.needs)
# ===========================================================================


def test_require_all_needs_returns_single_composite_need():
    """needs() must return exactly one Need with method='composite'."""
    g1 = FixedNeedsGenerator(UserNeed(1))
    gen = RequireAll(g1)

    class MyPolicy(_CompositeTestPolicy):
        can_test = (gen,)

    policy = MyPolicy("test")
    result = gen.needs(permission_policy=policy)
    assert len(result) == 1
    assert result[0].method == "composite"


def test_require_all_needs_value_is_hashable_list():
    """The value of the composite Need must be a HashableList."""
    g1 = FixedNeedsGenerator(UserNeed(1))
    gen = RequireAll(g1)

    class MyPolicy(_CompositeTestPolicy):
        can_test = (gen,)

    policy = MyPolicy("test")
    need = gen.needs(permission_policy=policy)[0]
    assert isinstance(need.value, HashableList)


def test_require_all_needs_value_contains_inner_generators():
    """The HashableList in the composite Need must contain the inner generators."""
    g1 = FixedNeedsGenerator(UserNeed(1))
    g2 = FixedNeedsGenerator(UserNeed(2))
    gen = RequireAll(g1, g2)

    class MyPolicy(_CompositeTestPolicy):
        can_test = (gen,)

    policy = MyPolicy("test")
    need = gen.needs(permission_policy=policy)[0]
    assert list(need.value) == [g1, g2]


def test_require_all_composite_need_is_hashable():
    """The returned Need must be hashable (required for use in frozensets)."""
    g1 = FixedNeedsGenerator(UserNeed(1))
    gen = RequireAll(g1)

    class MyPolicy(_CompositeTestPolicy):
        can_test = (gen,)

    policy = MyPolicy("test")
    need = gen.needs(permission_policy=policy)[0]
    assert isinstance(hash(need), int)
    assert need in frozenset([need])  # noqa FURB171


def test_require_all_each_call_creates_new_hashable_list():
    """Two calls to needs() must return distinct HashableLists (different objects)."""
    g1 = FixedNeedsGenerator(UserNeed(1))
    gen = RequireAll(g1)

    class MyPolicy(_CompositeTestPolicy):
        can_test = (gen,)

    policy = MyPolicy("test")
    hl1 = gen.needs(permission_policy=policy)[0].value
    hl2 = gen.needs(permission_policy=policy)[0].value
    # Different objects even though contents are the same
    assert hl1 is not hl2
    assert hl1 != hl2


# ===========================================================================
# BooleanPermissionPolicyMixin.allows() - requires Flask + DB
# ===========================================================================


def test_composite_mixin_allows_when_regular_needs_match(app, db):
    """When a regular (non-composite) generator matches, allows() returns True."""
    g = FixedNeedsGenerator(UserNeed(1))

    class MyPolicy(_CompositeTestPolicy):
        can_test = (g,)

    policy = MyPolicy("test")
    assert policy.allows(_identity(1)) is True


def test_composite_mixin_denies_when_regular_needs_do_not_match(app, db):
    """When no generator matches and there is no composite generator, denies."""
    g = FixedNeedsGenerator(UserNeed(1))

    class MyPolicy(_CompositeTestPolicy):
        can_test = (g,)

    policy = MyPolicy("test")
    assert policy.allows(_identity(2)) is False


def test_composite_mixin_allows_single_inner_generator_matching(app, db):
    """Composite with one inner generator: identity satisfying that need is allowed."""
    g = FixedNeedsGenerator(UserNeed(1))
    gen = RequireAll(g)

    class MyPolicy(_CompositeTestPolicy):
        can_test = (gen,)

    policy = MyPolicy("test")
    assert policy.allows(_identity(1)) is True


def test_composite_mixin_denies_single_inner_generator_not_matching(app, db):
    """Composite with one inner generator: identity without the need is denied."""
    g = FixedNeedsGenerator(UserNeed(1))
    gen = RequireAll(g)

    class MyPolicy(_CompositeTestPolicy):
        can_test = (gen,)

    policy = MyPolicy("test")
    assert policy.allows(_identity(2)) is False


def test_composite_mixin_and_logic_allows_when_all_inner_generators_match(app, db):
    """AND composite: identity satisfying all inner generators is allowed."""
    role_need = Need("role", "editor")
    g1 = FixedNeedsGenerator(UserNeed(1))
    g2 = FixedNeedsGenerator(role_need)
    gen = RequireAll(g1, g2)

    class MyPolicy(_CompositeTestPolicy):
        can_test = (gen,)

    policy = MyPolicy("test")
    assert policy.allows(_identity(1, role_need)) is True


def test_composite_mixin_and_logic_denies_when_first_inner_generator_does_not_match(app, db):
    """AND composite: identity missing the first generator's need is denied."""
    role_need = Need("role", "editor")
    g1 = FixedNeedsGenerator(UserNeed(1))
    g2 = FixedNeedsGenerator(role_need)
    gen = RequireAll(g1, g2)

    class MyPolicy(_CompositeTestPolicy):
        can_test = (gen,)

    policy = MyPolicy("test")
    # user 2 has the role but is not user 1
    assert policy.allows(_identity(2, role_need)) is False


def test_composite_mixin_and_logic_denies_when_second_inner_generator_does_not_match(app, db):
    """AND composite: identity missing the second generator's need is denied."""
    role_need = Need("role", "editor")
    g1 = FixedNeedsGenerator(UserNeed(1))
    g2 = FixedNeedsGenerator(role_need)
    gen = RequireAll(g1, g2)

    class MyPolicy(_CompositeTestPolicy):
        can_test = (gen,)

    policy = MyPolicy("test")
    # user 1 but without the editor role
    assert policy.allows(_identity(1)) is False


def test_composite_mixin_and_logic_three_inner_generators_all_match(app, db):
    """AND composite with three inner generators: all three must be satisfied."""
    role_a = Need("role", "a")
    role_b = Need("role", "b")
    g1 = FixedNeedsGenerator(UserNeed(1))
    g2 = FixedNeedsGenerator(role_a)
    g3 = FixedNeedsGenerator(role_b)
    gen = RequireAll(g1, g2, g3)

    class MyPolicy(_CompositeTestPolicy):
        can_test = (gen,)

    policy_allow = MyPolicy("test")
    assert policy_allow.allows(_identity(1, role_a, role_b)) is True

    policy_deny_missing_b = MyPolicy("test")
    assert policy_deny_missing_b.allows(_identity(1, role_a)) is False

    policy_deny_missing_a = MyPolicy("test")
    assert policy_deny_missing_a.allows(_identity(1, role_b)) is False


def test_composite_mixin_excludes_deny_even_when_needs_match(app, db):
    """An excluded identity is denied even if its needs match the composite."""
    ban = Need("role", "banned")
    g = FixedExcludesGenerator(needs=[UserNeed(1)], excludes=[ban])
    gen = RequireAll(g)

    class MyPolicy(_CompositeTestPolicy):
        can_test = (gen,)

    policy = MyPolicy("test")
    # user 1 is also banned
    assert policy.allows(_identity(1, ban)) is False


def test_composite_mixin_allows_when_excluded_need_not_present(app, db):
    """Exclude need not present in identity does not prevent access."""
    ban = Need("role", "banned")
    g = FixedExcludesGenerator(needs=[UserNeed(1)], excludes=[ban])
    gen = RequireAll(g)

    class MyPolicy(_CompositeTestPolicy):
        can_test = (gen,)

    policy = MyPolicy("test")
    # user 1 is NOT banned
    assert policy.allows(_identity(1)) is True


def test_composite_mixin_excludes_in_second_inner_generator_deny(app, db):
    """Exclude fired by a later inner generator in the AND chain still denies."""
    ban = Need("role", "banned")
    g1 = FixedNeedsGenerator(UserNeed(1))  # only needs
    g2 = FixedExcludesGenerator(needs=[Need("role", "editor")], excludes=[ban])
    gen = RequireAll(g1, g2)

    class MyPolicy(_CompositeTestPolicy):
        can_test = (gen,)

    policy = MyPolicy("test")
    editor = Need("role", "editor")
    # user 1 + editor role + banned → g2's need matches but it also excludes
    assert policy.allows(_identity(1, editor, ban)) is False


def test_composite_mixin_empty_inner_generator_prevents_satisfaction(app, db):
    """A generator returning no needs in a composite can never be satisfied.

    An empty ``needs()`` result is treated as 'not satisfied', causing the
    composite to break and move on to the next composite need (of which there
    is none), resulting in denial.
    """
    g_empty = EmptyGenerator()
    g_normal = FixedNeedsGenerator(UserNeed(1))
    gen = RequireAll(g_empty, g_normal)

    class MyPolicy(_CompositeTestPolicy):
        can_test = (gen,)

    policy = MyPolicy("test")
    assert policy.allows(_identity(1)) is False


def test_composite_mixin_or_semantics_first_composite_matches(app, db):
    """Multiple RequireAll generators behave with OR semantics: first match wins."""
    g1 = FixedNeedsGenerator(UserNeed(1))
    g2 = FixedNeedsGenerator(UserNeed(2))
    gen1 = RequireAll(g1)
    gen2 = RequireAll(g2)

    class MyPolicy(_CompositeTestPolicy):
        can_test = (gen1, gen2)

    policy = MyPolicy("test")
    assert policy.allows(_identity(1)) is True


def test_composite_mixin_or_semantics_second_composite_matches(app, db):
    """Multiple RequireAll generators: second one satisfying the identity is enough."""
    g1 = FixedNeedsGenerator(UserNeed(1))
    g2 = FixedNeedsGenerator(UserNeed(2))
    gen1 = RequireAll(g1)
    gen2 = RequireAll(g2)

    class MyPolicy(_CompositeTestPolicy):
        can_test = (gen1, gen2)

    policy = MyPolicy("test")
    assert policy.allows(_identity(2)) is True


def test_composite_mixin_or_semantics_neither_composite_matches(app, db):
    """Multiple RequireAll generators: identity satisfying none of them is denied."""
    g1 = FixedNeedsGenerator(UserNeed(1))
    g2 = FixedNeedsGenerator(UserNeed(2))
    gen1 = RequireAll(g1)
    gen2 = RequireAll(g2)

    class MyPolicy(_CompositeTestPolicy):
        can_test = (gen1, gen2)

    policy = MyPolicy("test")
    assert policy.allows(_identity(99)) is False


def test_composite_mixin_mixed_regular_and_composite_generators(app, db):
    """A policy with both regular and composite generators works correctly.

    Regular generators use OR semantics among themselves; composite generators
    add further OR alternatives handled by the mixin.
    """
    regular_gen = FixedNeedsGenerator(UserNeed(10))
    composite_inner = FixedNeedsGenerator(UserNeed(20))
    composite_gen = RequireAll(composite_inner)

    class MyPolicy(_CompositeTestPolicy):
        can_test = (regular_gen, composite_gen)

    # user 10 is satisfied by the regular generator (super().allows)
    assert MyPolicy("test").allows(_identity(10)) is True

    # user 20 is satisfied by the composite generator (mixin logic)
    assert MyPolicy("test").allows(_identity(20)) is True

    # user 99 satisfies neither
    assert MyPolicy("test").allows(_identity(99)) is False


def test_composite_mixin_and_logic_combining_user_and_role_needs(app, db):
    """Real-world-like scenario: user must have a specific ID *and* a role."""
    admin_role = Need("role", "admin")
    g_user = FixedNeedsGenerator(UserNeed(42))
    g_role = FixedNeedsGenerator(admin_role)
    gen = RequireAll(g_user, g_role)

    class MyPolicy(_CompositeTestPolicy):
        can_test = (gen,)

    # user 42 with admin role → allowed
    assert MyPolicy("test").allows(_identity(42, admin_role)) is True

    # user 42 without admin role → denied
    assert MyPolicy("test").allows(_identity(42)) is False

    # another user with admin role → denied (not user 42)
    assert MyPolicy("test").allows(_identity(7, admin_role)) is False

    # anonymous-ish user, no match at all → denied
    assert MyPolicy("test").allows(_identity(99)) is False


def test_composite_mixin_no_composite_generators_falls_back_to_super(app, db):
    """Without any RequireAll generator the mixin delegates entirely to super."""
    g = FixedNeedsGenerator(UserNeed(5))

    class MyPolicy(_CompositeTestPolicy):
        can_test = (g,)

    # super().allows handles user 5
    assert MyPolicy("test").allows(_identity(5)) is True
    # super().allows denies everyone else
    assert MyPolicy("test").allows(_identity(6)) is False
