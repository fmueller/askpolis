import os
import re
from datetime import date, datetime
from typing import Any, Optional

from celery import shared_task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from askpolis.core import Parliament, ParliamentPeriod
from askpolis.core.database import ParliamentPeriodRepository, ParliamentRepository
from askpolis.data_fetcher import FetchedData, FetchedDataRepository
from askpolis.data_fetcher.abgeordnetenwatch import DATA_FETCHER_ID
from askpolis.logging import get_logger

logger = get_logger(__name__)

engine = create_engine(os.getenv("DATABASE_URL") or "postgresql+psycopg://postgres@postgres:5432/askpolis-db")
SessionLocal = sessionmaker(bind=engine)

date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@shared_task(name="transform_fetched_data_to_core_models")
def transform_fetched_data_to_core_models() -> None:
    session = SessionLocal()
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
        parliament_period_repository = ParliamentPeriodRepository(session)
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

                for _election_program in election_programs.json_data:
                    logger.info("TODO Creating new election program...")
                    # TODO also create party entities
                    pass
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
