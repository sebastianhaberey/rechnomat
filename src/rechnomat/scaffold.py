from collections.abc import Mapping
from datetime import date
from decimal import Decimal
from types import UnionType
from typing import Any, Union, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import FieldInfo


def render_scaffold(model: type[BaseModel], *, overrides: Mapping[str, str] | None = None) -> str:
    """
    Render a YAML scaffold for `model` by introspecting its fields.

    Required fields get a type-appropriate placeholder written directly; optional fields (those with a
    default) are emitted as a commented-out line. Field(description=...) metadata is rendered as a
    trailing `# ...` comment. `overrides` may supply literal string values for top-level field names,
    used verbatim instead of the placeholder (e.g. pre-filling `name:` with a user-supplied value).
    A `list[BaseModel]` field is rendered as a single example item under a `- ` marker.
    """
    lines = _render_model_fields(model, indent=0, overrides=overrides or {})
    return "\n".join(lines) + "\n"


def _render_model_fields(model: type[BaseModel], *, indent: int, overrides: Mapping[str, str]) -> list[str]:
    lines: list[str] = []
    for field_name, field_info in model.model_fields.items():
        lines.extend(_render_field(field_name, field_info, indent=indent, override=overrides.get(field_name)))
    return lines


def _render_field(name: str, field_info: FieldInfo, *, indent: int, override: str | None) -> list[str]:
    prefix = " " * indent
    required = field_info.is_required()
    annotation = field_info.annotation
    comment = f"  # {field_info.description}" if field_info.description else ""
    resolved_type = annotation if required else _unwrap_optional(annotation)

    if isinstance(resolved_type, type) and issubclass(resolved_type, BaseModel):
        if not required:
            raise NotImplementedError(f"Optional nested BaseModel fields are not supported yet: {name!r}")
        if override is not None:
            raise NotImplementedError(f"Overrides for nested model fields are not supported: {name!r}")
        header = f"{prefix}{name}:{comment}"
        nested = _render_model_fields(resolved_type, indent=indent + 2, overrides={})
        return [header, *nested]

    if get_origin(resolved_type) is list:
        if not required:
            raise NotImplementedError(f"Optional list fields are not supported yet: {name!r}")
        if override is not None:
            raise NotImplementedError(f"Overrides for list fields are not supported: {name!r}")
        return _render_list_field(name, resolved_type, indent=indent, comment=comment)

    value = _quote_str(override) if override is not None else _placeholder_for(resolved_type)
    line = f"{prefix}{name}: {value}{comment}"
    return [line] if required else [f"{prefix}# {name}: {value}{comment}"]


def _render_list_field(name: str, list_type: Any, *, indent: int, comment: str) -> list[str]:
    (item_type,) = get_args(list_type)
    if not (isinstance(item_type, type) and issubclass(item_type, BaseModel)):
        raise NotImplementedError(f"No scaffold placeholder implemented for list item type: {item_type!r}")

    prefix = " " * indent
    item_indent = indent + 4
    item_lines = _render_model_fields(item_type, indent=item_indent, overrides={})
    dash_prefix = " " * (indent + 2) + "- "
    item_lines[0] = dash_prefix + item_lines[0][item_indent:]

    return [f"{prefix}{name}:{comment}", *item_lines]


def _unwrap_optional(annotation: Any) -> Any:
    if get_origin(annotation) in (UnionType, Union):
        non_none = [arg for arg in get_args(annotation) if arg is not type(None)]
        if len(non_none) == 1:
            return non_none[0]
    return annotation


def _placeholder_for(annotation: Any) -> str:
    if annotation is str:
        return '""'
    if annotation is int:
        return "0"
    if annotation is Decimal:
        return '"0"'  # quoted so it parses as an exact Decimal, not a binary float
    if annotation is date:
        return date.today().isoformat()
    raise NotImplementedError(f"No scaffold placeholder implemented for annotation: {annotation!r}")


def _quote_str(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
