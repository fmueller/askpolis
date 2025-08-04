from askpolis.qa.models import Answer


def test_answer_relationships_use_selectin() -> None:
    assert Answer.contents.property.lazy == "selectin"
    assert Answer.citations.property.lazy == "selectin"
