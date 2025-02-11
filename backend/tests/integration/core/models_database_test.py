import datetime

from sqlalchemy.orm import Session, sessionmaker

from askpolis.core import ElectionProgram, Parliament, ParliamentPeriod, Party


def test_core_data_model(session_maker: sessionmaker[Session]) -> None:
    with session_maker() as session:
        parliament = Parliament(name="Parliament of Canada", short_name="Canada")
        party = Party(name="Party of Canada", short_name="Canada")
        parliament_period = ParliamentPeriod(
            parliament=parliament,
            label="2025 - 3025",
            period_type="legislature",
            start_date=datetime.date(2025, 1, 1),
            end_date=datetime.date(3025, 1, 1),
        )

        session.add(parliament)
        session.add(party)
        session.add(parliament_period)
        session.commit()

        election_program = ElectionProgram(
            parliament_period=parliament_period,
            party=party,
            label="default-version",
            file_name="election_program.pdf",
            file_data=b"PDF data",
        )
        session.add(election_program)
        session.commit()

    with session_maker() as session:
        parliament = session.query(Parliament).filter(Parliament.short_name == "Canada").one()
        assert parliament.short_name == "Canada"

        party = session.query(Party).filter(Party.short_name == "Canada").one()
        assert party.short_name == "Canada"

        parliament_period = session.query(ParliamentPeriod).filter(ParliamentPeriod.label == "2025 - 3025").one()
        assert parliament_period.label == "2025 - 3025"

        election_program = (
            session.query(ElectionProgram).filter(ElectionProgram.parliament_period_id == parliament_period.id).one()
        )
        assert election_program.file_name == "election_program.pdf"


def test_updated_at_is_properly_updated(session_maker: sessionmaker[Session]) -> None:
    first_last_updated_at = datetime.datetime.now(datetime.timezone.utc)
    with session_maker() as session:
        party = Party(name="Party of Canada", short_name="Canada")
        party.updated_at = first_last_updated_at
        session.add(party)
        session.commit()

    with session_maker() as session:
        party = session.query(Party).filter(Party.short_name == "Canada").one()
        party.updated_at = datetime.datetime.now(datetime.timezone.utc)
        session.commit()

    with session_maker() as session:
        party = session.query(Party).filter(Party.short_name == "Canada").one()
        assert party.updated_at is not None
        assert party.updated_at > first_last_updated_at
