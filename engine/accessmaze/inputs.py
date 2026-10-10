"""Run-only values and user-selected file buffers; never paths or persisted credentials."""

import base64
import hashlib
import hmac
import json

from accessmaze.models import RuntimeInputs


class RunInputs:
    def __init__(self, journey, raw=None, key=None):
        import secrets

        data = RuntimeInputs.model_validate(raw or {})
        text_keys = {s.value_from for s in journey.steps if s.value_from and s.action != "upload"}
        file_keys = {s.value_from for s in journey.steps if s.action == "upload"}
        if text_keys != set(data.values) or file_keys != set(data.files):
            raise ValueError(
                "Provide exactly the runtime text and file inputs referenced by the journey"
            )
        if any(not value or len(value) > 10000 for value in data.values.values()):
            raise ValueError("Runtime values must contain 1–10000 characters")
        self.values = data.values
        self.files = {}
        total = 0
        for name, item in data.files.items():
            try:
                content = base64.b64decode(item.base64, validate=True)
            except ValueError as exc:
                raise ValueError("Invalid upload buffer") from exc
            total += len(content)
            if total > 4 * 1024**2:
                raise ValueError("Combined upload limit is 4 MiB per run")
            self.files[name] = {
                "name": item.name,
                "mimeType": "application/octet-stream",
                "buffer": content,
            }
        self.signature = None
        literals = {
            s.id: s.value
            for s in journey.steps
            if s.action in {"fill", "assert_value"} and not s.value_from
        }
        if text_keys or file_keys or literals:
            payload = json.dumps(
                {"runtime": data.model_dump(), "literals": literals}, sort_keys=True
            ).encode()
            self.signature = hmac.new(
                key or secrets.token_bytes(32), payload, hashlib.sha256
            ).hexdigest()

    @property
    def secrets(self):
        return [*self.values.values(), *[f["name"] for f in self.files.values()]]

    def value(self, step):
        return self.values[step.value_from] if step.value_from else step.value
