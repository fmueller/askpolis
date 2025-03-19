from typing import Optional

from askpolis.data_fetcher import FetchedData, FetchedDataRepository
from askpolis.data_fetcher.abgeordnetenwatch.client import AbgeordnetenwatchClient
from askpolis.logging import get_logger

logger = get_logger(__name__)

DATA_FETCHER_ID = "abgeordnetenwatch/election_programs/v1"


class AbgeordnetenwatchDataFetcher:
    def __init__(self, repository: FetchedDataRepository, client: Optional[AbgeordnetenwatchClient] = None) -> None:
        self._client = client or AbgeordnetenwatchClient()
        self._repository = repository

    def fetch_election_programs(self, parliament_id: int) -> None:
        logger.info("Start fetching of election programs...")

        logger.info("Fetching all parliaments...")
        parliaments = self._repository.get_by_data_fetcher_and_entity(
            DATA_FETCHER_ID, FetchedData.get_entity_for_list_of_parliaments()
        )
        if parliaments is None:
            parliaments = self._client.get_all_parliaments()
            parliaments.data_fetcher = DATA_FETCHER_ID
            self._repository.save(parliaments)

        assert parliaments.json_data is not None
        if not any(parliament["id"] == parliament_id for parliament in parliaments.json_data):
            logger.warning_with_attrs("Parliament not found, stop data fetching", {"parliament_id": parliament_id})
            return

        logger.info_with_attrs("Fetching all parliament periods...", {"parliament_id": parliament_id})
        parliament_periods = self._repository.get_by_data_fetcher_and_entity(
            DATA_FETCHER_ID, FetchedData.get_entity_for_list_of_parliament_periods(parliament_id)
        )
        if parliament_periods is None:
            parliament_periods = self._client.get_all_parliament_periods(parliament_id)
            parliament_periods.data_fetcher = DATA_FETCHER_ID
            self._repository.save(parliament_periods)

        assert parliament_periods.json_data is not None
        for parliament_period in parliament_periods.json_data:
            if parliament_period["type"] == "election":
                parliament_period_id = parliament_period["id"]
                logger.info_with_attrs(
                    "Fetching election programs for parliament period...",
                    {"parliament_period_id": parliament_period_id},
                )
                election_programs = self._repository.get_by_data_fetcher_and_entity(
                    DATA_FETCHER_ID, FetchedData.get_entity_for_list_of_election_programs(parliament_period_id)
                )
                if election_programs is None:
                    election_programs = self._client.get_all_election_programs(parliament_period_id)
                    election_programs.data_fetcher = DATA_FETCHER_ID
                    self._repository.save(election_programs)

                assert election_programs.json_data is not None
                for election_program in election_programs.json_data:
                    party_id = election_program["party"]["id"]
                    party = self._repository.get_by_data_fetcher_and_entity(
                        DATA_FETCHER_ID, FetchedData.get_entity_for_party(party_id)
                    )
                    if party is None:
                        logger.info_with_attrs("Fetching party...", {"party_id": party_id})
                        party = self._client.get_party(party_id, election_program["party"]["api_url"])
                        party.data_fetcher = DATA_FETCHER_ID
                        self._repository.save(party)

                    election_program_file = self._repository.get_by_data_fetcher_and_entity(
                        DATA_FETCHER_ID, FetchedData.get_entity_for_election_program(party_id, parliament_period_id)
                    )
                    if election_program_file is None:
                        file_to_download = election_program["file"]
                        if file_to_download is None:
                            logger.warning_with_attrs(
                                "No election program file to download", {"election_program_id": election_program["id"]}
                            )
                            continue

                        logger.info_with_attrs("Downloading election program file...", {"file": file_to_download})
                        election_program_file = self._client.get_election_program(
                            party_id, parliament_period_id, file_to_download
                        )
                        election_program_file.data_fetcher = DATA_FETCHER_ID
                        self._repository.save(election_program_file)

        logger.info("Finished fetching of election programs.")
