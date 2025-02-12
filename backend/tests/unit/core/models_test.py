import datetime
import time

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

    time.sleep(0.1)  # not ideal, but we need to wait for the time to change
    other_election_program = ElectionProgram(
        parliament_period=parliament_period,
        party=party,
        label="default-version",
        file_name="election_program.pdf",
        file_data=b"PDF data",
    )

    assert election_program.updated_at is not None
    assert other_election_program.updated_at is not None
    assert election_program.updated_at != other_election_program.updated_at
