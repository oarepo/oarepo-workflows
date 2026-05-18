from typing import TYPE_CHECKING, Any

from flask_principal import Identity, Need
from invenio_records_permissions.generators import (
    Generator,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from invenio_records_permissions import RecordPermissionPolicy
else:
    RecordPermissionPolicy = object


class HashableList(list):
    """A list subclass that is hashable by object identity rather than by value.

    Invenio's ``BasePermissionPolicy.needs`` property collects all generator
    needs into a ``frozenset``.  To store a composite ``Need`` whose ``value``
    field is a list of generators, that value must itself be hashable.  Plain
    Python lists are not hashable, so this wrapper is used instead.

    Identity-based semantics (``__hash__``, ``__eq__``, ``__ne__``) are
    intentional: two ``HashableList`` instances that hold the same generators
    are still treated as distinct objects.  This ensures that every call to
    ``CompositeAndGenerator.needs()`` produces a unique ``Need`` in the
    policy's ``explicit_needs`` set, regardless of whether the generator list
    contents happen to compare equal.

    .. note::
        ``list`` defines its own ``__ne__`` using value comparison, so
        overriding only ``__eq__`` would leave ``!=`` inconsistent with
        ``==``.  Both operators are therefore overridden together.
    """

    def __hash__(self) -> int:
        """Return a hash based on object identity, not contents."""
        return hash(id(self))

    def __eq__(self, other: Any) -> bool:
        """Return ``True`` only when *other* is the exact same object."""
        return self is other

    def __ne__(self, other: Any) -> bool:
        """Return ``True`` unless *other* is the exact same object."""
        return self is not other


class CompositeAndGenerator(Generator):
    """A generator that requires **all** of its inner generators to be satisfied.

    Standard invenio generators are combined with **OR** semantics inside a
    permission policy: granting access as soon as *any* generator produces a
    need that matches the identity.  ``CompositeAndGenerator`` provides **AND**
    semantics: every inner generator must independently produce at least one
    need that matches the identity before access is granted.

    Because OR-vs-AND cannot be expressed through the plain ``needs`` /
    ``excludes`` API, this generator encodes its inner generator list as a
    single opaque ``Need(method="composite", value=HashableList([...]))``.
    The actual AND evaluation is then carried out by
    :class:`CompositePermissionPolicyMixin` inside its ``allows()`` override.

    Multiple ``CompositeAndGenerator`` instances in the same ``can_*`` list are
    evaluated with **OR** semantics between them (the standard invenio
    behaviour): access is granted if *any* of those composites is fully
    satisfied.

    Example usage::

        class MyPolicy(CompositePermissionPolicyMixin, RecordPermissionPolicy):
            # User must be owner *and* hold the "reviewer" role.
            can_review = [
                CompositeAndGenerator(RecordOwners(), ReviewerRole()),
            ]

    .. important::
        The permission policy that hosts this generator **must** inherit from
        :class:`CompositePermissionPolicyMixin` and must inject ``policy=self``
        into the ``over`` context (see that class for details).  Failing to do
        so will cause ``needs()`` to raise ``ValueError`` or ``TypeError``.
    """

    def __init__(self, *generators: Generator):
        """Initialise with one or more inner generators.

        :param generators: The generators that must *all* be satisfied for
            access to be granted.  Providing zero generators results in a
            composite that is vacuously always satisfied (the ``for`` loop
            finishes without a ``break``, triggering the ``else`` branch in
            ``CompositePermissionPolicyMixin.allows``).
        """
        self.generators = generators

    def needs(self, **context: Any) -> "Sequence[Need]":
        """Return a single composite ``Need`` wrapping the inner generators.

        The AND evaluation cannot be expressed as a flat set of needs (which
        invenio combines with OR), so this method does *not* return the inner
        generators' needs directly.  Instead it encodes the entire generator
        list as a single ``Need(method="composite", value=HashableList([...]))``
        sentinel.  :class:`CompositePermissionPolicyMixin` recognises that
        sentinel in ``allows()`` and carries out the actual AND check there.

        A fresh :class:`HashableList` is created on every call so that each
        invocation yields a distinct (by identity) ``Need`` object — this
        matters when ``self.needs`` is accessed multiple times on the same
        policy instance, as invenio accumulates needs into a set.

        :param context: The keyword arguments forwarded by the policy's
            ``needs`` property (i.e. ``self.over``).  Must contain a ``policy``
            key whose value is an instance of
            :class:`CompositePermissionPolicyMixin`.
        :raises ValueError: If ``context`` contains no ``"policy"`` key.
        :raises TypeError: If the ``"policy"`` value is not an instance of
            :class:`CompositePermissionPolicyMixin`.
        :returns: A one-element list containing the composite ``Need``.
        """
        if "policy" not in context:
            raise ValueError("Permission policy class is not set up in context")
        if not isinstance(context["policy"], CompositePermissionPolicyMixin):
            raise TypeError(
                "Permission policy class is not a CompositePermissionPolicyMixin"
            )
        # Wrap the generator tuple in a HashableList so the resulting Need is
        # hashable and can live inside the frozenset returned by
        # BasePermissionPolicy.needs.
        return [Need("composite", HashableList(self.generators))]

    def __repr__(self) -> str:
        """Return a developer-friendly representation of this generator."""
        return f"CompositeAndGenerator({', '.join(repr(generator) for generator in self.generators)})"

    def __str__(self) -> str:
        """Return the string form of this generator (same as ``repr``)."""
        return repr(self)


class CompositePermissionPolicyMixin(RecordPermissionPolicy):
    """Permission-policy mixin that evaluates :class:`CompositeAndGenerator` needs.

    Invenio's built-in ``Permission.allows()`` collects all needs into a flat
    set and grants access if the identity matches *any* of them (OR semantics).
    Composite needs — produced by :class:`CompositeAndGenerator` — require AND
    semantics that cannot be expressed in that flat model, so this mixin
    overrides ``allows()`` with a two-phase check:

    1. **Regular phase** — delegates to ``super().allows(identity)``.  If the
       identity is already allowed by a non-composite generator (or is a
       superuser), return ``True`` immediately.

    2. **Composite phase** — iterates over all composite ``Need`` objects in
       ``self.needs`` (those with ``method == "composite"``).  For each one it
       applies AND logic across its inner generators:

       * For each inner generator, collect its ``needs()`` and ``excludes()``
         using ``self.over`` as context.
       * If the inner generator's needs are empty, *or* none of them match the
         identity's ``provides`` set → this composite is **not satisfied**;
         skip to the next composite (``break``).
       * If the inner generator's excludes match *any* need in the identity's
         ``provides`` set → return ``False`` immediately and conservatively
         deny access, regardless of other composites.
       * If every inner generator's needs are matched and none produced an
         exclude hit → return ``True`` (the composite is fully satisfied).

       If no composite is satisfied and no exclude was triggered, return
       ``False``.

    **OR semantics between composites**: multiple ``CompositeAndGenerator``
    instances in the same ``can_*`` list each produce their own composite
    ``Need``.  The loop tries all of them; the first fully-satisfied one grants
    access.

    **Setup requirement**: The policy's ``over`` context dict must contain a
    ``"policy"`` key pointing to the policy instance itself *before* ``needs``
    is first accessed.  Concrete subclasses should set this in ``__init__``::

        class MyPolicy(CompositePermissionPolicyMixin, RecordPermissionPolicy):
            def __init__(self, action, **over):
                super().__init__(action, **over)
                self.over["policy"] = self

    This is already handled by both :class:`~oarepo_workflows.services.permissions
    .workflow_permissions.DefaultWorkflowPermissions` and
    :class:`~oarepo_workflows.services.permissions.record_permission_policy
    .WorkflowRecordPermissionPolicyMixin`.
    """

    def allows(self, identity: Identity) -> bool:
        """Return whether *identity* is permitted by this policy.

        Extends ``Permission.allows`` with AND-composite evaluation for any
        :class:`CompositeAndGenerator` generators present in the active
        ``can_*`` list.

        :param identity: The Flask-Principal identity to check.
        :returns: ``True`` if access is granted, ``False`` otherwise.
        """
        ret = super().allows(identity)
        if ret:
            return True

        for need in self.needs:
            if need.method != "composite":
                continue
            generators = need.value
            for generator in generators:
                generator_needs = set(generator.needs(**self.over))
                generator_excludes = set(generator.excludes(**self.over))

                if not generator_needs or not generator_needs.intersection(
                    identity.provides
                ):
                    # This inner generator's needs are not met — the whole
                    # composite is unsatisfied; move on to the next composite.
                    break

                if generator_excludes and generator_excludes.intersection(
                    identity.provides
                ):
                    # An explicit exclusion applies.  Deny immediately and
                    # conservatively — do not check further composites.
                    return False
            else:
                # The for-loop completed without a break, meaning every inner
                # generator matched.  The composite as a whole is satisfied.
                return True

        # Either there were no composite generators, or none of them were
        # fully satisfied by this identity.
        return False
