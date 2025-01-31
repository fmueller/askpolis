from typing import Optional

from askpolis.data_fetcher import FetchedDataRepository
from askpolis.data_fetcher.abgeordnetenwatch.client import AbgeordnetenwatchClient
from askpolis.logging import get_logger

logger = get_logger(__name__)


class AbgeordnetenwatchDataFetcher:
    def __init__(self, repository: FetchedDataRepository, client: Optional[AbgeordnetenwatchClient] = None) -> None:
        self._client = client or AbgeordnetenwatchClient()
        self._repository = repository
        self.id = "data-fetcher/abgeordnetenwatch/election_programs/v0"

    def fetch_election_programs(self, parliament_id: int) -> None:
        logger.info("Start fetching of election programs...")

        logger.info("Fetching all parliament periods...")
        parliament_periods = self._repository.get_by_data_fetcher_and_entity(
            self.id, f"parliament-periods-{parliament_id}"
        )
        if parliament_periods is None:
            parliament_periods = self._client.get_all_parliament_periods(parliament_id)
            parliament_periods.data_fetcher = self.id
            self._repository.add(parliament_periods)
        else:
            logger.info("Already fetched")

        assert parliament_periods.json_data is not None
        for parliament_period in parliament_periods.json_data:
            if parliament_period["type"] == "election":
                parliament_period_id = parliament_period["id"]
                logger.info_with_attrs(
                    "Fetching election programs for parliament period...", {"id": parliament_period_id}
                )
                election_programs = self._repository.get_by_data_fetcher_and_entity(
                    self.id, f"election-programs-{parliament_period_id}"
                )
                if election_programs is None:
                    election_programs = self._client.get_all_election_programs(parliament_period_id)
                    election_programs.data_fetcher = self.id
                    self._repository.add(election_programs)
                else:
                    logger.info("Already fetched")

                assert election_programs.json_data is not None
                for election_program in election_programs.json_data:
                    entity = (
                        f"election-program-{election_program['id']}-"
                        f"parliament-period-{parliament_period_id}-"
                        f"party-{election_program['party']['id']}"
                    )
                    election_program_file = self._repository.get_by_data_fetcher_and_entity(self.id, entity)
                    if election_program_file is None:
                        file_to_download = election_program["file"]
                        if file_to_download is None:
                            logger.warning_with_attrs(
                                "No election program file to download", {"id": election_program["id"]}
                            )
                            continue

                        logger.info_with_attrs("Downloading election program file...", {"file": file_to_download})
                        election_program_file = self._client.get_election_program(entity, file_to_download)
                        election_program_file.data_fetcher = self.id
                        self._repository.add(election_program_file)
                    else:
                        logger.info_with_attrs("Already downloaded", {"file": election_program_file.source})

        logger.info("Finished fetching of election programs.")
