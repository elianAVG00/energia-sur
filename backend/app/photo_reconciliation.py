"""Read-only planning for CU05 photo recovery; this module never deletes files."""

import os
import re
import stat
from collections.abc import Iterable
from dataclasses import dataclass

_OBJECT_NAME = re.compile(r"cu05-[0-9a-f]{32}\Z", re.ASCII)
_TEMP_NAME = re.compile(r"\.cu05-[0-9a-f]{32}\.tmp\Z", re.ASCII)


class PhotoRecoveryRequired(Exception):
    """A referenced object is missing or a managed entry is not a regular file."""


@dataclass(frozen=True, slots=True)
class RecoveryPlan:
    """A snapshot of candidates, not permission to remove them."""

    unreferenced_objects: frozenset[str]
    temporary_files: frozenset[str]


def plan_recovery(directory: int, committed_references: Iterable[str]) -> RecoveryPlan:
    """Inventory managed names without following links or changing the volume.

    The caller must hold the PostgreSQL session advisory lock and then the
    stable filesystem lock, and obtain all committed references under those
    locks. This function cannot establish topology, transaction resolution, or
    lock ownership. Its result must not be used for deletion after either lock
    has been released, or without independently meeting those requirements.
    Missing references and non-regular managed entries fail the entire plan.
    """
    references = frozenset(committed_references)
    if any(_OBJECT_NAME.fullmatch(name) is None for name in references):
        raise PhotoRecoveryRequired("Invalid photo reference; recovery is required.")

    objects: set[str] = set()
    temporary: set[str] = set()
    for name in os.listdir(directory):
        is_object = _OBJECT_NAME.fullmatch(name) is not None
        is_temporary = _TEMP_NAME.fullmatch(name) is not None
        if not is_object and not is_temporary:
            continue
        entry = os.stat(name, dir_fd=directory, follow_symlinks=False)
        if not stat.S_ISREG(entry.st_mode):
            raise PhotoRecoveryRequired("Invalid managed photo entry; recovery is required.")
        if is_object:
            objects.add(name)
        else:
            temporary.add(name)

    if not references.issubset(objects):
        raise PhotoRecoveryRequired("Referenced photo is missing; recovery is required.")
    return RecoveryPlan(frozenset(objects - references), frozenset(temporary))
