import datetime

import pytest
import uuid_utils.compat as uuid
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from askpolis.core import (
    Document,
    DocumentRepository,
    DocumentType,
    ElectionProgram,
    Page,
    PageRepository,
    Parliament,
    ParliamentPeriod,
    Party,
)


def test_core_data_model(db_session: Session) -> None:
    parliament = Parliament(name="Parliament of Canada", short_name="Canada")
    party = Party(name="Party of Canada", short_name="Canada")
    parliament_period = ParliamentPeriod(
        parliament=parliament,
        label="2025 - 3025",
        period_type="legislature",
        start_date=datetime.date(2025, 1, 1),
        end_date=datetime.date(3025, 1, 1),
    )

    db_session.add(parliament)
    db_session.add(party)
    db_session.add(parliament_period)

    db_session.flush()

    election_program = ElectionProgram(
        parliament_period=parliament_period,
        party=party,
        label="default-version",
        file_name="election_program.pdf",
        file_data=b"PDF data",
    )
    db_session.add(election_program)

    parliament = db_session.query(Parliament).filter(Parliament.short_name == "Canada").one()
    assert parliament.short_name == "Canada"

    party = db_session.query(Party).filter(Party.short_name == "Canada").one()
    assert party.short_name == "Canada"

    parliament_period = db_session.query(ParliamentPeriod).filter(ParliamentPeriod.label == "2025 - 3025").one()
    assert parliament_period.label == "2025 - 3025"

    election_program = (
        db_session.query(ElectionProgram).filter(ElectionProgram.parliament_period_id == parliament_period.id).one()
    )
    assert election_program.file_name == "election_program.pdf"


def test_updated_at_is_properly_updated(db_session: Session) -> None:
    first_last_updated_at = datetime.datetime.now(datetime.timezone.utc)

    party = Party(name="Party of Canada", short_name="Canada")
    party.updated_at = first_last_updated_at
    db_session.add(party)

    db_session.flush()

    party = db_session.query(Party).filter(Party.short_name == "Canada").one()
    party.updated_at = datetime.datetime.now(datetime.timezone.utc)
    db_session.flush()

    party = db_session.query(Party).filter(Party.short_name == "Canada").one()
    assert party.updated_at is not None
    assert party.updated_at > first_last_updated_at


def test_document_and_page_model(db_session: Session) -> None:
    document = Document(name="test", document_type=DocumentType.ELECTION_PROGRAM)
    page = Page(document_id=document.id, page_number=123, content="some content", page_metadata={"header": "value"})
    db_session.add(document)
    db_session.add(page)

    db_session.flush()

    document_repository = DocumentRepository(db_session)
    document_from_db = document_repository.get_by_name("test")
    assert document_from_db is not None
    assert document_from_db.name == "test"

    page_repository = PageRepository(db_session)
    pages = page_repository.get_by_document_id(document_from_db.id)
    assert len(pages) == 1
    assert pages[0].content == "some content"


def test_document_unique_index_on_reference_ids(db_session: Session) -> None:
    ref_id_1 = uuid.uuid7()
    ref_id_2 = uuid.uuid7()

    document1 = Document(
        name="Document 1", document_type=DocumentType.ELECTION_PROGRAM, reference_id_1=ref_id_1, reference_id_2=ref_id_2
    )
    db_session.add(document1)
    db_session.flush()

    document2 = Document(
        name="Document 2", document_type=DocumentType.ELECTION_PROGRAM, reference_id_1=ref_id_1, reference_id_2=ref_id_2
    )
    db_session.add(document2)

    # Attempt to flush should raise IntegrityError due to a unique constraint violation
    with pytest.raises(IntegrityError):
        db_session.flush()
