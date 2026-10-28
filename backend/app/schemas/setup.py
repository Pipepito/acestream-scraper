"""Public wizard contract. No credentials, commands or deployment paths."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictFloat, StrictInt, StrictStr

RuntimeValue = StrictBool | StrictInt | StrictFloat | StrictStr


class RuntimeOption(BaseModel):
    name: str
    group: str
    label: str
    kind: str
    default: RuntimeValue
    help: str
    minimum: float | None = None
    maximum: float | None = None


class SetupState(BaseModel):
    version: Literal[1] = 1
    setup_complete: bool
    revision: str
    runtime: dict[str, RuntimeValue]
    options: list[RuntimeOption]
    unavailable: dict[str, str]
    restart_required: bool
    api_protected: bool


class SetupUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    expected_revision: str = Field(min_length=64, max_length=64)
    runtime: dict[str, RuntimeValue] = Field(max_length=100)
    setup_complete: bool = True
