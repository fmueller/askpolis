import datetime

from askpolis.core import ElectionProgram, Parliament, ParliamentPeriod, Party


def test_created_at_is_updated_for_election_programs() -> None:
    parliament_period = ParliamentPeriod(
        parliament=Parliament(id=1, name="Austria", short_name="AT"),
        label="1",
        period_type="regular",
        start_date=datetime.date(2020, 1, 1),
        end_date=datetime.date(2024, 12, 31),
    )
    party = Party(name="Party", short_name="P")

    election_program = ElectionProgram(
        parliament_period=parliament_period,
        party=party,
        label="default-version",
        file_name="election_program.pdf",
        file_data=b"PDF data",
    )

    other_election_program = ElectionProgram(
        parliament_period=parliament_period,
        party=party,
        label="default-version",
        file_name="election_program.pdf",
        file_data=b"PDF data",
    )

    assert election_program.last_updated_at is not None
    assert other_election_program.last_updated_at is not None
    assert election_program.last_updated_at != other_election_program.last_updated_at
