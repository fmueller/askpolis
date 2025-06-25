import re
from datetime import date, datetime
from typing import Any, Optional

import uuid_utils.compat as uuid
from celery import shared_task

from askpolis.core import Document, ElectionProgram, Parliament, ParliamentPeriod, Party
from askpolis.core.models import DocumentType, Page, PageVersion
from askpolis.core.pdf_reader import PdfReader
from askpolis.core.repositories import (
    DocumentRepository,
    ElectionProgramRepository,
    PageRepository,
    PageVersionRepository,
    ParliamentPeriodRepository,
    ParliamentRepository,
    PartyRepository,
)
from askpolis.data_fetcher import FetchedData, FetchedDataRepository
from askpolis.data_fetcher.abgeordnetenwatch import DATA_FETCHER_ID
from askpolis.db import get_db
from askpolis.logging import get_logger

logger = get_logger(__name__)

date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@shared_task(name="transform_fetched_data_to_core_models")
def transform_fetched_data_to_core_models() -> None:
    session = next(get_db())
    try:
        fetched_data_repository = FetchedDataRepository(session)
        parliaments = fetched_data_repository.get_by_data_fetcher_and_entity(
            DATA_FETCHER_ID, FetchedData.get_entity_for_list_of_parliaments()
        )
        if parliaments is None:
            logger.warning("No parliaments found")
            return
        if parliaments.json_data is None:
            logger.warning("No parliaments json_data found")
            return

        parliament_repository = ParliamentRepository(session)
        party_repository = PartyRepository(session)
        parliament_period_repository = ParliamentPeriodRepository(session)
        election_program_repository = ElectionProgramRepository(session)

        for parliament_json in parliaments.json_data:
            parliament_id = parliament_json["id"]
            parliament = parliament_repository.get_by_name(parliament_json["label_external_long"])

            if parliament is None:
                logger.info_with_attrs(
                    "Creating new parliament", {"parliament_name": parliament_json["label_external_long"]}
                )
                parliament = Parliament(parliament_json["label_external_long"], parliament_json["label"])
                parliament_repository.save(parliament)

            parliament_periods = fetched_data_repository.get_by_data_fetcher_and_entity(
                DATA_FETCHER_ID, FetchedData.get_entity_for_list_of_parliament_periods(parliament_id)
            )
            if parliament_periods is None:
                logger.warning_with_attrs("No parliament periods found", {"parliament_id": parliament_id})
                continue
            if parliament_periods.json_data is None:
                logger.warning_with_attrs("No parliament periods json_data found", {"parliament_id": parliament_id})
                continue

            for parliament_period_json in parliament_periods.json_data:
                if _validate_parliament_period_json(parliament_period_json) is False:
                    logger.warning_with_attrs(
                        "Invalid parliament period",
                        {"entity": FetchedData.get_entity_for_list_of_parliament_periods(parliament_id)},
                    )
                    continue

                parliament_period_id = parliament_period_json["id"]
                parliament_period = parliament_period_repository.get_by_type_and_date_period(
                    parliament,
                    parliament_period_json["type"],
                    _parse_date(parliament_period_json["start_date_period"]),
                    _parse_date(parliament_period_json["end_date_period"]),
                )

                if parliament_period is None:
                    logger.info_with_attrs(
                        "Creating new parliament period",
                        {
                            "parliament_id": parliament_id,
                            "type": parliament_period_json["type"],
                            "start_date": parliament_period_json["start_date_period"],
                            "end_date": parliament_period_json["end_date_period"],
                        },
                    )
                    parliament_period = _try_parse_parliament_period(parliament, parliament_period_json)
                    if parliament_period is None:
                        logger.warning("Failed to parse parliament period")
                        continue
                    parliament_period_repository.save(parliament_period)

                election_programs = fetched_data_repository.get_by_data_fetcher_and_entity(
                    DATA_FETCHER_ID, FetchedData.get_entity_for_list_of_election_programs(parliament_period_id)
                )
                if election_programs is None:
                    logger.warning_with_attrs(
                        "No election programs found", {"parliament_period_id": parliament_period_id}
                    )
                    continue
                if election_programs.json_data is None:
                    logger.warning_with_attrs(
                        "No election programs json_data found", {"parliament_period_id": parliament_period_id}
                    )
                    continue

                for election_program_json in election_programs.json_data:
                    party_id = election_program_json["party"]["id"]
                    party_json = fetched_data_repository.get_by_data_fetcher_and_entity(
                        DATA_FETCHER_ID, FetchedData.get_entity_for_party(party_id)
                    )

                    if party_json is None:
                        logger.warning_with_attrs("No party found", {"party_id": party_id})
                        continue
                    if party_json.json_data is None:
                        logger.warning_with_attrs("No party json data found", {"party_id": party_id})
                        continue

                    name = party_json.json_with_data_field["data"]["full_name"]
                    party = party_repository.get_by_name(name)
                    if party is None:
                        logger.info_with_attrs("Creating new party", {"party_name": name})
                        party = Party(name, party_json.json_with_data_field["data"]["short_name"])
                        party_repository.save(party)

                    election_program = election_program_repository.get(party, parliament_period)
                    if election_program is None:
                        fetched_program = fetched_data_repository.get_by_data_fetcher_and_entity(
                            DATA_FETCHER_ID, FetchedData.get_entity_for_election_program(party_id, parliament_period_id)
                        )
                        if fetched_program is None:
                            logger.warning_with_attrs(
                                "No election program found",
                                {
                                    "party_id": party_id,
                                    "parliament_period_id": parliament_period_id,
                                },
                            )
                            continue
                        if fetched_program.file_data is None:
                            logger.warning_with_attrs(
                                "No election program file data found",
                                {
                                    "party_id": party_id,
                                    "parliament_period_id": parliament_period_id,
                                },
                            )
                            continue

                        logger.info_with_attrs(
                            "Creating new election program",
                            {
                                "party_id": party_id,
                                "parliament_period_id": parliament_period_id,
                            },
                        )
                        election_program = ElectionProgram(
                            parliament_period,
                            party,
                            "default",
                            fetched_program.source or "no filename provided",
                            fetched_program.file_data,
                        )
                        election_program_repository.save(election_program)

    finally:
        session.close()


@shared_task(name="read_and_parse_election_programs_to_documents")
def read_and_parse_election_programs_to_documents() -> None:
    session = next(get_db())
    try:
        election_program_repository = ElectionProgramRepository(session)
        document_repository = DocumentRepository(session)
        page_repository = PageRepository(session)
        page_version_repository = PageVersionRepository(session)

        election_programs = election_program_repository.get_all_without_referenced_document()
        for election_program in election_programs:
            if election_program.file_data is None:
                logger.warning_with_attrs(
                    "No file data found",
                    {
                        "party_id": election_program.party_id,
                        "parliament_period_id": election_program.parliament_period_id,
                    },
                )
                continue

            document = document_repository.get_by_references(
                election_program.party_id, election_program.parliament_period_id
            )
            if document is None:
                logger.info_with_attrs(
                    "Creating new document",
                    {
                        "party_id": election_program.party_id,
                        "parliament_period_id": election_program.parliament_period_id,
                    },
                )

                pdf_reader = PdfReader(election_program.file_data)
                pdf_document = pdf_reader.to_markdown()
                if pdf_document is None:
                    logger.warning_with_attrs(
                        "Failed to parse PDF to markdown",
                        {
                            "party_id": election_program.party_id,
                            "parliament_period_id": election_program.parliament_period_id,
                        },
                    )
                    continue

                logger.info_with_attrs(
                    "Read and parsed a new document",
                    {
                        "party_id": election_program.party_id,
                        "parliament_period_id": election_program.parliament_period_id,
                        "pages": len(pdf_document.pages),
                    },
                )
                document = Document(
                    name=election_program.file_name
                    if election_program.file_name is not None
                    else f"no filename provided-{uuid.uuid7()}",
                    document_type=DocumentType.ELECTION_PROGRAM,
                    reference_id_1=election_program.party_id,
                    reference_id_2=election_program.parliament_period_id,
                )
                document_repository.save(document)
                pages = [
                    Page(
                        document_id=document.id,
                        page_number=pdf_page.page_number,
                        content=pdf_page.content,
                        page_metadata=pdf_page.metadata,
                    )
                    for pdf_page in pdf_document.pages
                ]
                page_repository.save_all(pages)
                page_versions = [
                    PageVersion(
                        page_id=page.id,
                        version="raw",
                        content=pdf_page.raw_content,
                    )
                    for page, pdf_page in zip(pages, pdf_document.pages)
                ]
                page_version_repository.save_all(page_versions)
    finally:
        session.close()


def _try_parse_parliament_period(parliament: Parliament, json: dict[str, Any]) -> Optional[ParliamentPeriod]:
    if _validate_parliament_period_json(json) is False:
        return None

    return ParliamentPeriod(
        parliament,
        json["label"],
        json["type"],
        _parse_date(json["start_date_period"]),
        _parse_date(json["end_date_period"]),
        _try_parse_date(json.get("election_date")),
    )


def _validate_parliament_period_json(json: dict[str, Any]) -> bool:
    if _contains_fields(json, ["label", "type", "start_date_period", "end_date_period"]) is False:
        logger.warning("Missing required fields for parliament period")
        return False

    start_date = _try_parse_date(json["start_date_period"])
    if start_date is None:
        logger.warning_with_attrs("Invalid start date", {"date_value": json["start_date_period"]})
        return False

    end_date = _try_parse_date(json["end_date_period"])
    if end_date is None:
        logger.warning_with_attrs("Invalid end date", {"date_value": json["end_date_period"]})
        return False

    if (
        "election_date" in json
        and json.get("election_date") is not None
        and _try_parse_date(json.get("election_date")) is None
    ):
        logger.warning_with_attrs("Invalid election date", {"date_value": json.get("election_date")})
        return False

    return True


def _parse_date(value: str) -> date:
    parsed_date = _try_parse_date(value)
    if parsed_date is None:
        raise ValueError(f"Invalid date: {value}")
    return parsed_date


def _try_parse_date(value: Optional[str]) -> Optional[date]:
    if value is None:
        return None
    try:
        if not date_pattern.match(value):
            return None
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _contains_fields(json_dict: dict[str, Any], required_fields: list[str]) -> bool:
    return all(field in json_dict for field in required_fields)
