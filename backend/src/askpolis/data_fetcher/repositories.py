from typing import Optional

from sqlalchemy.orm import Session

from askpolis.data_fetcher.models import DataFetcherType, FetchedData
from askpolis.logging import get_logger


class FetchedDataRepository:
    _logger = get_logger(__name__)

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, fetched_data: FetchedData) -> None:
        self.session.add(fetched_data)
        self.session.commit()

    def get_all(self) -> list[FetchedData]:
        return self.session.query(FetchedData).all()

    def get_by_data_fetcher_and_entity(self, data_fetcher: str, entity: str) -> Optional[FetchedData]:
        return (
            self.session.query(FetchedData)
            .filter_by(data_fetcher=data_fetcher, entity=entity)
            .order_by(FetchedData.created_at.desc())
            .first()
        )

    def delete_outdated_data(self) -> list[tuple[DataFetcherType, int]]:
        deleted_rows: list[tuple[DataFetcherType, int]] = []
        for data_fetcher_type in DataFetcherType:
            self._logger.info_with_attrs(
                "Deleting outdated data for data fetcher:", {"data_fetcher": data_fetcher_type}
            )
            deleted_rows.append(self._delete_outdated_data_for_data_fetcher(data_fetcher_type))
        return deleted_rows

    def _delete_outdated_data_for_data_fetcher(self, data_fetcher_type: DataFetcherType) -> tuple[DataFetcherType, int]:
        last_fetched_data = (
            self.session.query(FetchedData)
            .filter_by(data_fetcher_type=data_fetcher_type)
            .order_by(FetchedData.created_at.desc())
            .first()
        )

        if last_fetched_data is None:
            self._logger.info_with_attrs("No data to delete for data fetcher:", {"data_fetcher": data_fetcher_type})
            return data_fetcher_type, 0

        rows = (
            self.session.query(FetchedData)
            .filter(
                FetchedData.data_fetcher_type == data_fetcher_type,
                FetchedData.data_fetcher != last_fetched_data.data_fetcher,
            )
            .delete(synchronize_session=False)
        )
        self._logger.info_with_attrs(
            "Deleted rows for data fetcher:", {"data_fetcher": data_fetcher_type, "rows": rows}
        )
        self.session.commit()
        return data_fetcher_type, rows
