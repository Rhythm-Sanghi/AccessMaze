import pytest
from pydantic import ValidationError

from accessmaze.models import Journey, Step
from accessmaze.templates import template


@pytest.mark.parametrize("kind", ["accessible", "broken", "errors", "recovery", "branch", "slow"])
def test_templates_validate(kind):
    assert Journey.model_validate_json(template(kind).model_dump_json()) == template(kind)


@pytest.mark.parametrize(
    "patch",
    [
        {"schema_version": 2},
        {"target": "file:///etc/passwd"},
        {"target": "https://user:secret@example.com/"},
        {"target": "https://example.com/?token=x"},
        {"target": "http://localhost:8000"},
        {"max_seconds": 10000},
        {"steps": [{"id": "x", "action": "navigate"}]},
        {"arbitrary_code": "evil"},
    ],
)
def test_imports_reject_unsafe_or_unbounded_definitions(patch):
    data = template().model_dump()
    data.update(patch)
    with pytest.raises(ValidationError):
        Journey.model_validate(data)


def test_effectful_actions_must_be_declared():
    with pytest.raises(ValidationError):
        Step(id="x", action="activate", target={"role": "button", "name": "Submit"})
    with pytest.raises(ValidationError):
        Step(id="x", action="press", value="Enter")
