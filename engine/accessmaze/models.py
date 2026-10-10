from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Target(StrictModel):
    by: Literal["role", "label"] = "role"
    role: Literal[
        "button",
        "link",
        "textbox",
        "checkbox",
        "combobox",
        "heading",
        "status",
        "alert",
        "dialog",
        "radio",
        "spinbutton",
    ]
    name: str = Field(min_length=1, max_length=200)


class Step(StrictModel):
    id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    action: Literal[
        "navigate",
        "fill",
        "activate",
        "press",
        "assert_visible",
        "assert_value",
        "assert_errors",
        "assert_modal",
        "assert_focus",
        "offline",
        "online",
        "wait",
        "audit",
        "upload",
    ]
    target: Target | None = None
    value: str = Field(default="", max_length=2000)
    optional: bool = False
    effect: bool = False
    value_from: str | None = Field(default=None, pattern=r"^[a-zA-Z][a-zA-Z0-9_-]{0,63}$")
    file_label: str = Field(default="", max_length=200)

    @model_validator(mode="after")
    def validate_action(self):
        if self.value_from and self.action not in {"fill", "assert_value", "upload"}:
            raise ValueError("Runtime inputs are supported for fill, assert_value and upload")
        if self.value_from and self.value:
            raise ValueError("Runtime inputs cannot contain a saved literal value")
        if self.action == "upload" and (
            not self.value_from or not self.file_label or not self.effect
        ):
            raise ValueError("Upload requires a file label, runtime input and effect declaration")
        if (
            self.action
            in {
                "fill",
                "activate",
                "assert_visible",
                "assert_value",
                "assert_modal",
                "assert_focus",
            }
            and not self.target
        ):
            raise ValueError(f"{self.action} requires a semantic target")
        if self.action == "press" and self.value not in {
            "Tab",
            "Shift+Tab",
            "Enter",
            "Space",
            "Escape",
            "ArrowDown",
            "ArrowUp",
            "ArrowLeft",
            "ArrowRight",
            "Home",
            "End",
        }:
            raise ValueError("Unsupported keyboard key")
        if self.action == "wait" and (not self.value.isdigit() or int(self.value) > 10000):
            raise ValueError("Wait must be milliseconds between 0 and 10000")
        if self.action == "activate" and not self.effect:
            raise ValueError(
                "Activation must explicitly declare a potentially state-changing effect"
            )
        if self.action == "press" and self.value in {"Enter", "Space"} and not self.effect:
            raise ValueError("Enter/Space must declare a potentially state-changing effect")
        return self


class RuntimeFile(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    base64: str = Field(max_length=6 * 1024**2)

    @model_validator(mode="after")
    def filename_only(self):
        if any(c in self.name for c in "/\\:\x00\r\n") or self.name in {".", ".."}:
            raise ValueError("Upload name must be a filename without a path")
        return self


class RuntimeInputs(StrictModel):
    values: dict[str, str] = Field(default_factory=dict, max_length=100)
    files: dict[str, RuntimeFile] = Field(default_factory=dict, max_length=20)


class Profile(StrictModel):
    action_timeout_ms: int = Field(default=10000, ge=1000, le=30000)
    keyboard_only: bool = True
    reduced_motion: bool = False
    viewport_width: int = Field(default=1280, ge=320, le=3840)
    viewport_height: int = Field(default=800, ge=240, le=2160)
    network_latency_ms: int = Field(default=0, ge=0, le=3000)


class Exploration(StrictModel):
    enabled: bool = False
    max_depth: int = Field(default=2, ge=1, le=4)
    max_actions: int = Field(default=50, ge=1, le=200)


class NetworkPolicy(StrictModel):
    navigation_origins: list[str] = Field(default_factory=list, max_length=16)
    resource_origins: list[str] = Field(default_factory=list, max_length=32)

    @model_validator(mode="after")
    def validate_origins(self):
        from accessmaze.network import canonical_origin

        for field in ("navigation_origins", "resource_origins"):
            values = getattr(self, field)
            normalized = []
            for value in values:
                parsed = urlsplit(value)
                if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
                    raise ValueError("Permissions must be exact HTTP(S) origins without paths")
                normalized.append(canonical_origin(value))
            setattr(self, field, list(dict.fromkeys(normalized)))
        return self


class Privacy(StrictModel):
    capture_page_text: bool = False


class Journey(StrictModel):
    schema_version: Literal[1] = 1
    name: str = Field(min_length=1, max_length=120)
    target: str = Field(max_length=2048)
    steps: list[Step] = Field(min_length=1, max_length=100)
    profile: Profile = Field(default_factory=Profile)
    max_seconds: int = Field(default=60, ge=1, le=300)
    tab_budget: int = Field(default=60, ge=1, le=200)
    allow_local: bool = False
    exploration: Exploration = Field(default_factory=Exploration)
    network: NetworkPolicy = Field(default_factory=NetworkPolicy)
    privacy: Privacy = Field(default_factory=Privacy)

    @model_validator(mode="after")
    def validate_journey(self):
        parsed = urlsplit(self.target)
        if self.target not in {
            "fixture://accessible",
            "fixture://broken",
            "fixture://errors",
            "fixture://recovery",
            "fixture://modal",
            "fixture://conditional",
            "fixture://branch",
            "fixture://slow",
        }:
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                raise ValueError("Target must be an HTTP(S) URL or a bundled fixture")
            if parsed.username or parsed.password or parsed.query or parsed.fragment:
                raise ValueError(
                    "Credentials, query strings and fragments are not allowed in targets"
                )
            if not self.allow_local and parsed.hostname in {"localhost", "127.0.0.1", "::1"}:
                raise ValueError("Local targets require explicit local-network authorization")
        if len({step.id for step in self.steps}) != len(self.steps):
            raise ValueError("Step IDs must be unique")
        if self.steps[0].action != "navigate":
            raise ValueError("The first step must navigate to the configured target")
        if not any(step.action.startswith("assert_") and not step.optional for step in self.steps):
            raise ValueError("A journey requires at least one mandatory completion assertion")
        for step in self.steps:
            if step.action == "navigate" and step.value not in {"", "/"}:
                raise ValueError(
                    "Navigation opens only the configured target; use links for transitions"
                )
        return self


class ProjectInput(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    journey: Journey


class Request(StrictModel):
    version: Literal[1]
    id: str = Field(min_length=1, max_length=64)
    method: Literal[
        "health",
        "project.list",
        "project.save",
        "project.delete",
        "project.archive",
        "run.start",
        "run.get",
        "run.list",
        "run.cancel",
        "run.pause",
        "run.resume",
        "run.approve",
        "run.compare",
        "report.export",
        "evidence.read",
        "storage.backup",
        "storage.prune",
        "recorder.start",
        "recorder.get",
        "recorder.stop",
        "recorder.assert",
    ]
    params: dict = Field(default_factory=dict)
