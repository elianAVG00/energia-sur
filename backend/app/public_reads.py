"""Pure freshness/state helpers shared by the CU01/CU02 APIs and assistant tools."""

from datetime import datetime

FRESH_SECONDS = 15 * 60
STALE_SECONDS = 60 * 60
SCHEDULED_LIMITATIONS = (
    "dates_not_published",
    "reason_not_published",
    "proximity_not_available",
)


def freshness(source_last_modified: datetime | None, now: datetime) -> str:
    if source_last_modified is None:
        return "unavailable"
    age = (now - source_last_modified).total_seconds()
    if age <= FRESH_SECONDS:
        return "fresh"
    if age <= STALE_SECONDS:
        return "stale"
    return "unavailable"


def outage_state(
    freshness_value: str, coverage: str, has_rows: bool, source_status: str,
) -> str:
    if coverage == "out_of_coverage":
        return "out_of_coverage"
    if freshness_value == "unavailable":
        return "unavailable"
    if freshness_value == "stale":
        return "stale"
    if has_rows:
        return "reported"
    if source_status == "degraded" and coverage == "covered":
        return "unavailable"
    if coverage == "covered":
        return "no_reports"
    return "coverage_unverified"


def scheduled_state(
    freshness_value: str, coverage: str, has_rows: bool, source_status: str,
) -> str:
    if coverage == "out_of_coverage":
        return "out_of_coverage"
    if freshness_value == "unavailable":
        return "unavailable"
    if freshness_value == "stale":
        return "stale"
    if has_rows:
        return "works_reported"
    if source_status == "degraded" and coverage == "covered":
        return "unavailable"
    if coverage == "covered":
        return "no_works"
    return "coverage_unverified"


def scheduled_limitations(comunicados_present: bool) -> list[str]:
    values = list(SCHEDULED_LIMITATIONS)
    if comunicados_present:
        values.append("announced_works_not_displayed")
    return values
