from typing import Any, Optional


def build_task_result(
    status: str,
    entity_id: Optional[str] = None,
    data: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Create a serializable task result for Celery tasks.

    The returned dict can be displayed by Flower and contains the execution status,
    the id of the processed entity and additional task specific data.
    """
    result: dict[str, Any] = {"status": status}
    if entity_id is not None:
        result["entity_id"] = entity_id
    if data:
        result["data"] = data
    return result
