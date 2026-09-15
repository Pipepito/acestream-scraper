"""Portable, versioned extraction recipes. No executable code or credentials."""
import re
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

MAX_SAMPLE_BYTES = 32 * 1024 * 1024
MAX_RECORDS = 1000


class RecipeField(BaseModel):
    model_config = ConfigDict(extra='forbid')
    selector: str = Field('', max_length=256)
    attribute: str = Field('', max_length=80)
    path: str = Field('', max_length=256)
    pattern: str = Field('', max_length=1024)


class ExtractionRecipe(BaseModel):
    model_config = ConfigDict(extra='forbid')
    schema_version: Literal[1] = 1
    name: str = Field('My recipe', min_length=1, max_length=100)
    version: str = Field('1.0.0', pattern=r'^\d+\.\d+\.\d+$')
    mode: Literal['html', 'regex', 'json'] = 'html'
    records: str = Field('', max_length=1024)
    flags: str = Field('is', pattern=r'^[ims]{0,3}$')
    fields: dict[str, RecipeField]

    @model_validator(mode='after')
    def portable_rules(self):
        if not {'name', 'id'} <= self.fields.keys():
            raise ValueError('Choose a channel name and ID field')
        if self.fields.keys() - {'name', 'id', 'group', 'logo', 'epg_id'}:
            raise ValueError('Unknown channel field')
        if self.mode != 'json' and not self.records.strip():
            raise ValueError('Choose a repeating record')
        patterns = [f.pattern for f in self.fields.values() if f.pattern]
        if self.mode == 'regex':
            patterns.append(self.records)
        for pattern in patterns:
            # Deliberately common Python/JS subset. Capturing group 1 is the value.
            if re.search(r'\(\?(?!:|=|!)|\\(?:[1-9]|[AbBZzGKNpPk]|u|U|x)', pattern):
                raise ValueError('Use portable regex: plain captures, noncapturing groups and lookahead; no named groups or backreferences')
            try:
                re.compile(pattern)
            except (re.error, RecursionError):
                raise ValueError('Invalid regular expression') from None
        for field in self.fields.values():
            for path in [field.path] + ([self.records] if self.mode == 'json' else []):
                if path and not re.fullmatch(r'[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)*', path):
                    raise ValueError('JSON paths use dot-separated keys or array indices')
        return self


class RecipePreviewRequest(BaseModel):
    recipe: ExtractionRecipe
    sample: str = Field(max_length=MAX_SAMPLE_BYTES)


class RecipeFetchRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)
    url_type: Literal['auto', 'regular', 'zeronet', 'ipfs'] = 'auto'


class RecipeSample(BaseModel):
    sample: str


class ExtractedChannel(BaseModel):
    channel_id: str
    name: str
    metadata: dict[str, str] = Field(default_factory=dict)


class RecipeIssue(BaseModel):
    record: int
    message: str


class RecipePreview(BaseModel):
    channels: list[ExtractedChannel]
    record_count: int
    invalid_count: int
    duplicate_count: int
    issues: list[RecipeIssue]
