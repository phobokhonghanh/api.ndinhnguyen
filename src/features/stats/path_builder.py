import string

from .errors import StatsStorageError


class PathTemplateBuilder:
    def build(
        self,
        template: str,
        allowed_fields: set[str],
        values: dict[str, str],
    ) -> str:
        self._validate_template(template, allowed_fields)
        try:
            return template.format(**values)
        except (KeyError, IndexError, ValueError) as exc:
            raise StatsStorageError from exc

    def _validate_template(self, template: str, allowed_fields: set[str]) -> None:
        formatter = string.Formatter()
        for _, field_name, format_spec, conversion in formatter.parse(template):
            if field_name and field_name not in allowed_fields:
                raise StatsStorageError
            if format_spec or conversion:
                raise StatsStorageError
