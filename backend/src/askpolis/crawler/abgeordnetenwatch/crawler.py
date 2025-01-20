from typing import Optional

from .. import CrawlerRepository
from .client import AbgeordnetenwatchClient


class AbgeordnetenwatchCrawler:
    def __init__(self, repository: CrawlerRepository, client: Optional[AbgeordnetenwatchClient] = None) -> None:
        self._client = client or AbgeordnetenwatchClient()
        self._repository = repository
        self.id = "abgeordnetenwatch-v0-election_programs"

    def crawl_election_programs(self, parliament_id: int) -> None:
        print("Start crawling of election programs...")

        print("Crawling all parliament periods...")
        parliament_periods = self._repository.get_by_crawler_and_entity(self.id, f"parliament-periods-{parliament_id}")
        if parliament_periods is None:
            parliament_periods = self._client.get_all_parliament_periods(parliament_id)
            parliament_periods.crawler = self.id
            self._repository.add(parliament_periods)
            print(parliament_periods.json_data)
        else:
            print("Already crawled")

        assert parliament_periods.json_data is not None
        for parliament_period in parliament_periods.json_data:
            if parliament_period["type"] == "election":
                parliament_period_id = parliament_period["id"]
                print(f"Crawling election programs for parliament period {parliament_period_id}...")
                election_programs = self._repository.get_by_crawler_and_entity(
                    self.id, f"election-programs-{parliament_period_id}"
                )
                if election_programs is None:
                    election_programs = self._client.get_all_election_programs(parliament_period_id)
                    election_programs.crawler = self.id
                    self._repository.add(election_programs)
                    print(election_programs.json_data)
                else:
                    print("Already crawled")

                assert election_programs.json_data is not None
                for election_program in election_programs.json_data:
                    entity = (
                        f"election-program-{election_program['id']}-"
                        f"parliament-period-{parliament_period_id}-"
                        f"party-{election_program['party']['id']}"
                    )
                    election_program_file = self._repository.get_by_crawler_and_entity(self.id, entity)
                    if election_program_file is None:
                        print(f"Downloading election program file... {election_program['file']}")
                        election_program_file = self._client.get_election_program(entity, election_program["file"])
                        election_program_file.crawler = self.id
                        self._repository.add(election_program_file)
                    else:
                        print(f"Already crawled {election_program_file.source}")

        print("Finished crawling of election programs.")
