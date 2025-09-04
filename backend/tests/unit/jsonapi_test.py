import json
from typing import Union

from pydantic import BaseModel

from askpolis.jsonapi import jsonapi_response


class Attr(BaseModel):
    name: str


def test_jsonapi_response() -> None:
    resp = jsonapi_response("things", "1", Attr(name="foo"))
    assert resp.status_code == 200
    body: Union[bytes, bytearray] = resp.body if isinstance(resp.body, (bytes, bytearray)) else bytes(resp.body)
    assert json.loads(body) == {"data": {"type": "things", "id": "1", "attributes": {"name": "foo"}}}
