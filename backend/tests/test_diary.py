"""Fixed-clock CU09 domain regressions; no HTTP, database or PDF claim."""

import unittest
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from unittest.mock import Mock

from app.diary import (
    BUENOS_AIRES,
    DiaryReport,
    Interruption,
    ReportPeriod,
    generate_report,
    validate_for_save,
)


def local(value: str) -> datetime:
    """Build synthetic Buenos Aires fixture dates, without parsing production input."""
    return datetime.fromisoformat(value).replace(tzinfo=BUENOS_AIRES)


class DiaryFixture(unittest.TestCase):
    """Provide one synthetic preauthorized domicile and deterministic clocks."""

    def cut(
        self,
        start: str,
        end: str | None = None,
        *,
        record_id: str = "synthetic-cut",
        domicile_id: str = "synthetic-domicile",
    ) -> Interruption:
        return Interruption(
            id=record_id,
            domicile_id=domicile_id,
            start_at=local(start),
            end_at=local(end) if end is not None else None,
        )

    def report(
        self,
        *records: Interruption,
        start: str = "2026-11-01T00:00",
        end: str = "2026-11-02T00:00",
        now: str = "2026-11-07T12:00",
    ) -> DiaryReport:
        return generate_report(
            domicile_id="synthetic-domicile",
            interruptions=records,
            period=ReportPeriod(local(start), local(end)),
            clock=lambda: local(now),
        )


class CutValidationTests(DiaryFixture):
    """Exercise the pure validation portion of CU09-S01/S02/S10."""

    def test_closed_record_allows_missing_optional_text(self) -> None:
        record = self.cut("2026-11-01T10:00", "2026-11-01T12:00")
        self.assertIs(validate_for_save(record, now=local("2026-11-07T12:00")), record)
        self.assertIsNone(record.observations)
        self.assertIsNone(record.complaint_number)
        self.assertEqual(record.status, "closed")

    def test_open_record_remains_open(self) -> None:
        record = self.cut("2026-11-01T10:00")
        self.assertIs(validate_for_save(record, now=local("2026-11-07T12:00")), record)
        self.assertIsNone(record.end_at)
        self.assertEqual(record.status, "ongoing")

    def test_future_start_and_end_are_rejected(self) -> None:
        for record in (
            self.cut("2026-11-07T12:01"),
            self.cut("2026-11-07T10:00", "2026-11-07T12:01"),
        ):
            with self.subTest(record=record):
                with self.assertRaises(ValueError):
                    validate_for_save(record, now=local("2026-11-07T12:00"))

    def test_now_is_inclusive_and_not_silently_rounded_for_mutations(self) -> None:
        record = self.cut("2026-11-07T10:00", "2026-11-07T12:00")
        for now in ("2026-11-07T12:00", "2026-11-07T12:00:59.999999"):
            with self.subTest(now=now):
                self.assertIs(validate_for_save(record, now=local(now)), record)

    def test_equal_or_earlier_end_is_rejected(self) -> None:
        for end in ("2026-11-01T10:00", "2026-11-01T09:59", "2026-10-31T23:59"):
            with self.subTest(end=end):
                with self.assertRaises(ValueError):
                    self.cut("2026-11-01T10:00", end)

    def test_naive_record_dates_and_validation_clock_are_rejected(self) -> None:
        record = self.cut("2026-11-01T10:00", "2026-11-01T11:00")
        naive = datetime(2026, 11, 1, 10)
        for replacement in ({"start_at": naive}, {"end_at": naive}):
            with self.subTest(replacement=replacement):
                with self.assertRaises(ValueError):
                    replace(record, **replacement)
        with self.assertRaises(ValueError):
            validate_for_save(record, now=naive)

    def test_record_subminute_precision_is_rejected_in_each_date(self) -> None:
        record = self.cut("2026-11-01T10:00", "2026-11-01T11:00")
        for field in ("start_at", "end_at"):
            for delta in (timedelta(seconds=1), timedelta(microseconds=1)):
                with self.subTest(field=field, delta=delta):
                    with self.assertRaises(ValueError):
                        replace(record, **{field: local("2026-11-01T10:00") + delta})

    def test_aware_input_is_converted_to_named_buenos_aires_zone(self) -> None:
        record = Interruption(
            id="utc-cut",
            domicile_id="synthetic-domicile",
            start_at=datetime(2026, 11, 1, 13, 5, tzinfo=UTC),
            end_at=datetime(2026, 11, 1, 14, 10, tzinfo=UTC),
        )
        self.assertIs(record.start_at.tzinfo, BUENOS_AIRES)
        self.assertEqual(record.start_at, local("2026-11-01T10:05"))
        self.assertEqual(record.end_at, local("2026-11-01T11:10"))
        self.assertIs(
            validate_for_save(record, now=datetime(2026, 11, 1, 14, 10, tzinfo=UTC)),
            record,
        )

    def test_date_order_uses_instants_not_supplied_wall_clock_strings(self) -> None:
        start = datetime(2026, 11, 1, 10, tzinfo=timezone(timedelta(hours=-3)))
        # The apparent earlier wall time is actually 30 minutes after the start.
        record = Interruption(
            id="offset-cut",
            domicile_id="synthetic-domicile",
            start_at=start,
            end_at=datetime(2026, 11, 1, 9, 30, tzinfo=timezone(timedelta(hours=-4))),
        )
        self.assertEqual(record.end_at, local("2026-11-01T10:30"))
        with self.assertRaises(ValueError):
            replace(
                record,
                end_at=datetime(2026, 11, 1, 10, 30, tzinfo=timezone(timedelta(hours=-2))),
            )

    def test_historical_offset_is_not_assumed_to_be_minus_three(self) -> None:
        record = Interruption(
            id="historical-cut",
            domicile_id="synthetic-domicile",
            start_at=datetime(2008, 1, 1, 12, tzinfo=UTC),
            end_at=datetime(2008, 1, 1, 13, tzinfo=UTC),
        )
        self.assertEqual(record.start_at.utcoffset(), timedelta(hours=-2))
        self.assertEqual(record.start_at.hour, 10)
        self.assertEqual(self.report(
            record, start="2008-01-01T00:00", end="2008-01-02T00:00"
        ).total_minutes, 60)

    def test_pre_1970_dates_are_rejected_and_the_exact_boundary_is_accepted(self) -> None:
        # The approved floor removes historical second-level offsets rather than
        # rounding them; 1970-01-01 00:00 Buenos Aires is still inclusive.
        for record_start in (
            local("1969-12-31T23:59"),
            datetime(1970, 1, 1, 2, 59, tzinfo=UTC),
        ):
            with self.subTest(record_start=record_start):
                with self.assertRaises(ValueError) as raised:
                    Interruption(
                        "pre-1970-cut",
                        "synthetic-domicile",
                        record_start,
                        local("1970-01-01T01:00"),
                    )
                self.assertIn("1970-01-01", str(raised.exception))
        with self.assertRaises(ValueError):
            ReportPeriod(local("1969-12-31T23:59"), local("1970-01-01T00:00"))
        boundary = self.cut("1970-01-01T00:00", "1970-01-01T01:00")
        self.assertEqual(boundary.start_at, local("1970-01-01T00:00"))
        # The same floor instant expressed with another aware offset is accepted.
        offset_floor = datetime(
            1969, 12, 31, 23, 0, tzinfo=timezone(timedelta(hours=-4))
        )
        accepted = Interruption(
            "offset-floor-cut",
            "synthetic-domicile",
            offset_floor,
            local("1970-01-01T01:00"),
        )
        self.assertEqual(accepted.start_at, local("1970-01-01T00:00"))
        report = self.report(
            boundary, start="1970-01-01T00:00", end="1970-01-02T00:00"
        )
        self.assertEqual(report.total_minutes, 60)

    def test_subminute_after_timezone_conversion_is_rejected(self) -> None:
        record = self.cut("2026-11-01T10:00")
        with self.assertRaises(ValueError):
            replace(
                record,
                start_at=datetime(
                    2026, 11, 1, 10, tzinfo=timezone(-timedelta(hours=3, seconds=1))
                ),
            )

    def test_nonexistent_historical_wall_time_is_not_silently_shifted(self) -> None:
        # Buenos Aires skipped midnight to 01:00 when DST began on this date.
        with self.assertRaises(ValueError):
            self.cut("2008-10-19T00:30")

    def test_invalid_proposed_replacement_cannot_change_existing_record(self) -> None:
        original = self.cut("2026-11-01T10:00", "2026-11-01T11:00")
        with self.assertRaises(ValueError):
            replace(original, end_at=local("2026-11-01T10:00"))
        proposed = replace(original, end_at=local("2026-11-07T12:01"))
        with self.assertRaises(ValueError):
            validate_for_save(proposed, now=local("2026-11-07T12:00"))
        self.assertEqual(original.end_at, local("2026-11-01T11:00"))
        with self.assertRaises(FrozenInstanceError):
            setattr(original, "end_at", None)


class ReportBoundaryTests(DiaryFixture):
    """Validate query precision and a single trusted generation clock."""

    def test_equal_or_reversed_period_is_rejected(self) -> None:
        for end in ("2026-11-01T00:00", "2026-10-31T23:59"):
            with self.subTest(end=end):
                with self.assertRaises(ValueError):
                    ReportPeriod(local("2026-11-01T00:00"), local(end))

    def test_period_requires_aware_minute_boundaries(self) -> None:
        good_start = local("2026-11-01T00:00")
        good_end = local("2026-11-02T00:00")
        for start, end in (
            (good_start.replace(tzinfo=None), good_end),
            (good_start, good_end.replace(tzinfo=None)),
            (good_start.replace(second=1), good_end),
            (good_start, good_end.replace(microsecond=1)),
        ):
            with self.subTest(start=start, end=end):
                with self.assertRaises(ValueError):
                    ReportPeriod(start, end)

    def test_period_order_and_normalization_use_aware_instants(self) -> None:
        period = ReportPeriod(
            datetime(2026, 11, 1, 3, tzinfo=UTC),
            datetime(2026, 11, 2, 3, tzinfo=UTC),
        )
        self.assertEqual(period.start_at, local("2026-11-01T00:00"))
        self.assertIs(period.end_at.tzinfo, BUENOS_AIRES)
        with self.assertRaises(ValueError):
            ReportPeriod(local("2026-11-01T10:00"), datetime(2026, 11, 1, 13, tzinfo=UTC))

    def test_clock_is_called_once_and_floored_once_for_all_rows(self) -> None:
        clock = Mock(return_value=datetime(2026, 11, 1, 16, 30, 59, 999999, tzinfo=UTC))
        records = (
            self.cut("2026-11-01T12:00", record_id="first"),
            self.cut("2026-11-01T13:00", record_id="second"),
        )
        report = generate_report(
            domicile_id="synthetic-domicile",
            interruptions=iter(records),
            period=ReportPeriod(local("2026-11-01T00:00"), local("2026-11-02T00:00")),
            clock=clock,
        )
        clock.assert_called_once_with()
        self.assertEqual(report.generated_at, local("2026-11-01T13:30"))
        self.assertIs(report.generated_at.tzinfo, BUENOS_AIRES)
        self.assertEqual(report.total_minutes, 90)
        self.assertEqual({row.overlap_end_at for row in report.rows}, {report.generated_at})
        self.assertTrue(all(record.end_at is None for record in records))

    def test_naive_report_clock_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            generate_report(
                domicile_id="synthetic-domicile",
                interruptions=(),
                period=ReportPeriod(local("2026-11-01T00:00"), local("2026-11-02T00:00")),
                clock=lambda: datetime(2026, 11, 1, 13),
            )

    def test_future_query_end_is_allowed_without_future_cut_permission(self) -> None:
        record = self.cut("2026-11-01T12:00")
        report = self.report(record, end="2027-01-01T00:00", now="2026-11-01T13:30")
        self.assertEqual(report.total_minutes, 90)
        self.assertEqual(report.rows[0].overlap_end_at, local("2026-11-01T13:30"))

    def test_mixed_domicile_input_is_rejected_even_if_foreign_cut_is_outside(self) -> None:
        own = self.cut("2026-11-01T10:00", "2026-11-01T11:00")
        foreign = self.cut(
            "2026-10-01T10:00", "2026-10-01T11:00", domicile_id="other-domicile"
        )
        with self.assertRaises(ValueError):
            self.report(own, foreign)


class PeriodIntersectionTests(DiaryFixture):
    """CU09-S05/S07/S08/S13: count only positive query intersections."""

    def test_s05_closed_cut_crossing_period_start_counts_only_two_hours(self) -> None:
        record = self.cut("2026-10-31T23:00", "2026-11-01T02:00")
        report = self.report(record, end="2026-12-01T00:00")
        self.assertEqual((report.total_minutes, report.hours, report.minutes), (120, 2, 0))
        self.assertEqual(report.rows[0].overlap_start_at, local("2026-11-01T00:00"))
        self.assertIs(report.rows[0].interruption, record)
        self.assertEqual(record.start_at, local("2026-10-31T23:00"))

    def test_closed_cut_crossing_period_end_is_clipped(self) -> None:
        record = self.cut("2026-11-01T23:00", "2026-11-02T02:00")
        report = self.report(record)
        self.assertEqual(report.total_minutes, 60)
        self.assertEqual(report.rows[0].overlap_end_at, local("2026-11-02T00:00"))
        self.assertEqual(record.end_at, local("2026-11-02T02:00"))

    def test_closed_cut_spanning_both_boundaries_counts_the_period(self) -> None:
        record = self.cut("2026-10-31T23:00", "2026-11-02T02:00")
        report = self.report(record)
        self.assertEqual((report.total_minutes, report.hours, report.minutes), (1440, 24, 0))

    def test_total_hours_do_not_wrap_after_twenty_four_hours(self) -> None:
        record = self.cut("2026-11-01T00:00", "2026-11-02T01:05")
        report = self.report(record, end="2026-11-03T00:00")
        self.assertEqual((report.total_minutes, report.hours, report.minutes), (1505, 25, 5))

    def test_s13_boundary_only_and_wholly_outside_records_are_excluded(self) -> None:
        records = (
            self.cut("2026-10-31T23:00", "2026-11-01T00:00", record_id="left-touch"),
            self.cut("2026-11-02T00:00", "2026-11-02T01:00", record_id="right-touch"),
            self.cut("2026-10-30T10:00", "2026-10-30T11:00", record_id="before"),
            self.cut("2026-11-03T10:00", "2026-11-03T11:00", record_id="after"),
        )
        original_dates = tuple((record.start_at, record.end_at) for record in records)
        report = self.report(*records)
        self.assertEqual(report.rows, ())
        self.assertEqual((report.total_minutes, report.hours, report.minutes), (0, 0, 0))
        self.assertEqual(tuple((record.start_at, record.end_at) for record in records), original_dates)

    def test_s07_generation_caps_ongoing_at_five_hours_without_closure(self) -> None:
        record = self.cut("2026-11-01T10:00")
        report = self.report(record, now="2026-11-01T15:00")
        self.assertEqual((report.total_minutes, report.hours, report.minutes), (300, 5, 0))
        self.assertEqual(report.rows[0].overlap_end_at, local("2026-11-01T15:00"))
        self.assertEqual(record.status, "ongoing")
        self.assertIsNone(record.end_at)

    def test_s08_period_end_caps_ongoing_before_generation(self) -> None:
        record = self.cut("2026-11-01T22:00")
        report = self.report(record, now="2026-11-02T03:00")
        self.assertEqual((report.total_minutes, report.hours, report.minutes), (120, 2, 0))
        self.assertEqual(report.rows[0].overlap_end_at, local("2026-11-02T00:00"))
        self.assertIsNone(record.end_at)

    def test_ongoing_start_before_period_is_clipped(self) -> None:
        record = self.cut("2026-10-31T22:00")
        report = self.report(record, now="2026-11-01T01:15")
        self.assertEqual(report.total_minutes, 75)
        self.assertEqual(report.rows[0].overlap_start_at, local("2026-11-01T00:00"))

    def test_ongoing_generation_before_or_at_period_start_has_no_positive_overlap(self) -> None:
        record = self.cut("2026-10-31T22:00")
        for now in ("2026-10-31T23:59", "2026-11-01T00:00"):
            with self.subTest(now=now):
                report = self.report(record, now=now)
                self.assertEqual((report.total_minutes, report.rows), (0, ()))
        self.assertIsNone(record.end_at)

    def test_historical_generation_does_not_revalidate_stored_cut_as_a_mutation(self) -> None:
        closed = self.cut("2026-11-01T10:00", "2026-11-01T12:00", record_id="closed")
        ongoing = self.cut("2026-11-01T13:00", record_id="ongoing")
        validate_for_save(closed, now=local("2026-11-07T12:00"))
        validate_for_save(ongoing, now=local("2026-11-07T12:00"))
        report = self.report(closed, ongoing, now="2026-11-01T11:00")
        self.assertEqual(report.total_minutes, 120)
        self.assertEqual(tuple(row.interruption for row in report.rows), (closed,))
        self.assertEqual(closed.end_at, local("2026-11-01T12:00"))
        self.assertIsNone(ongoing.end_at)

    def test_ongoing_start_at_generation_is_excluded(self) -> None:
        record = self.cut("2026-11-01T13:30")
        report = self.report(record, now="2026-11-01T13:30:59")
        self.assertEqual((report.total_minutes, report.rows), (0, ()))

    def test_empty_input_has_empty_rows_and_zero_total(self) -> None:
        report = self.report()
        self.assertEqual((report.total_minutes, report.hours, report.minutes), (0, 0, 0))
        self.assertEqual(report.rows, ())


class UnionAndRowsTests(DiaryFixture):
    """CU09-S04/S14 and the shared data/order portion of S06/S15."""

    def test_s04_overlaps_retain_both_rows_and_total_three_not_four_hours(self) -> None:
        earlier = replace(
            self.cut("2026-11-01T10:00", "2026-11-01T12:00", record_id="earlier"),
            observations="Synthetic note",
            complaint_number="TEST-001",
        )
        later = self.cut("2026-11-01T11:00", "2026-11-01T13:00", record_id="later")
        report = self.report(earlier, later)
        self.assertEqual((report.total_minutes, report.hours, report.minutes), (180, 3, 0))
        self.assertEqual(tuple(row.interruption for row in report.rows), (later, earlier))
        self.assertEqual(report.rows[1].interruption.observations, "Synthetic note")
        self.assertEqual(report.rows[1].interruption.complaint_number, "TEST-001")
        self.assertEqual(earlier.end_at, local("2026-11-01T12:00"))
        self.assertEqual(later.end_at, local("2026-11-01T13:00"))

    def test_s14_minute_overlaps_total_sixty_five_minutes(self) -> None:
        first = self.cut("2026-11-01T10:05", "2026-11-01T10:50", record_id="first")
        second = self.cut("2026-11-01T10:35", "2026-11-01T11:10", record_id="second")
        report = self.report(first, second)
        self.assertEqual((report.total_minutes, report.hours, report.minutes), (65, 1, 5))
        self.assertEqual(report.rows[1].interruption.start_at.minute, 5)
        self.assertEqual(report.rows[0].interruption.end_at, local("2026-11-01T11:10"))

    def test_disjoint_nested_touching_identical_and_transitive_intervals(self) -> None:
        cases = (
            ("disjoint", (("10:00", "10:20"), ("11:00", "11:25")), 45),
            ("nested", (("10:00", "13:00"), ("11:00", "12:00")), 180),
            ("touching", (("10:00", "11:00"), ("11:00", "12:00")), 120),
            ("identical", (("10:00", "11:00"), ("10:00", "11:00")), 60),
            ("transitive", (("10:00", "11:00"), ("11:30", "13:00"), ("10:30", "12:00")), 180),
        )
        for name, intervals, expected in cases:
            with self.subTest(case=name):
                records = tuple(
                    self.cut(f"2026-11-01T{start}", f"2026-11-01T{end}", record_id=str(index))
                    for index, (start, end) in enumerate(intervals)
                )
                report = self.report(*records)
                reversed_report = self.report(*reversed(records))
                self.assertEqual(report.total_minutes, expected)
                self.assertEqual(reversed_report.total_minutes, expected)
                self.assertEqual(len(report.rows), len(records))

    def test_union_is_computed_after_clipping(self) -> None:
        records = (
            self.cut("2026-10-31T23:00", "2026-11-01T01:00", record_id="left"),
            self.cut("2026-11-01T00:30", "2026-11-01T02:00", record_id="middle"),
            self.cut("2026-11-01T01:30", "2026-11-01T04:00", record_id="right"),
        )
        report = self.report(*records, end="2026-11-01T03:00")
        self.assertEqual(report.total_minutes, 180)
        self.assertEqual(len(report.rows), 3)

    def test_s15_mixed_rows_are_descending_and_retain_original_open_end(self) -> None:
        closed = self.cut("2026-11-01T10:00", "2026-11-01T11:00", record_id="closed")
        ongoing = self.cut("2026-11-01T12:00", record_id="ongoing")
        report = self.report(closed, ongoing, now="2026-11-01T13:30")
        self.assertEqual((report.total_minutes, report.hours, report.minutes), (150, 2, 30))
        self.assertEqual(tuple(row.interruption for row in report.rows), (ongoing, closed))
        self.assertEqual(tuple(row.interruption.status for row in report.rows), ("ongoing", "closed"))
        self.assertIsNone(report.rows[0].interruption.end_at)
        self.assertEqual(report.rows[0].overlap_end_at, local("2026-11-01T13:30"))

    def test_row_order_uses_original_start_not_equal_clipped_start(self) -> None:
        earlier = self.cut("2026-10-31T22:00", "2026-11-01T02:00", record_id="earlier")
        later = self.cut("2026-10-31T23:00", "2026-11-01T01:00", record_id="later")
        report = self.report(earlier, later)
        self.assertEqual(tuple(row.interruption for row in report.rows), (later, earlier))
        self.assertEqual(report.rows[0].overlap_start_at, report.rows[1].overlap_start_at)

    def test_optional_unicode_and_empty_text_are_retained_without_new_limits(self) -> None:
        record = replace(
            self.cut("2026-11-01T10:00", "2026-11-01T11:00"),
            observations="Synthetic: interrupción ⚡\n" + "x" * 10000,
            complaint_number="",
        )
        row = self.report(record).rows[0]
        self.assertEqual(row.interruption.observations, record.observations)
        self.assertEqual(row.interruption.complaint_number, "")

    def test_report_rows_and_period_are_immutable(self) -> None:
        report = self.report(self.cut("2026-11-01T10:00"))
        for value, field, replacement in (
            (report, "total_minutes", 0),
            (report.period, "start_at", local("2026-11-01T01:00")),
            (report.rows[0], "overlap_end_at", local("2026-11-01T12:00")),
        ):
            with self.subTest(field=field):
                with self.assertRaises(FrozenInstanceError):
                    setattr(value, field, replacement)

    def test_historical_dst_crossing_uses_elapsed_time_not_same_zone_wall_subtraction(self) -> None:
        record = self.cut("2008-10-18T23:30", "2008-10-19T01:30")
        report = self.report(
            record, start="2008-10-18T00:00", end="2008-10-20T00:00"
        )
        self.assertEqual(report.total_minutes, 60)

    def test_ambiguous_historical_hour_uses_fold_to_compare_and_count_instants(self) -> None:
        # DST ended by repeating 23:00 on the previous local calendar day.
        start = local("2008-03-15T23:30").replace(fold=0)
        end = local("2008-03-15T23:30").replace(fold=1)
        record = Interruption("fold-cut", "synthetic-domicile", start, end)
        report = self.report(
            record, start="2008-03-15T00:00", end="2008-03-17T00:00"
        )
        self.assertEqual(report.total_minutes, 60)
        self.assertEqual(record.start_at.fold, 0)
        self.assertEqual(record.end_at.fold if record.end_at is not None else None, 1)
        with self.assertRaises(ValueError):
            replace(record, start_at=end, end_at=start)


if __name__ == "__main__":
    unittest.main()
