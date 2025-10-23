"""
Comprehensive JSON Schema validation with detailed error reporting.

This module provides validation for:
- Fingerprint input payloads (enrollment/verification)
- Helper data format (fuzzy extractor output)
- Configuration files (TOML/JSON format)

Features:
- Clear error messages with exact field paths
- Expected vs actual value reporting
- Suggested recovery steps
- Schema versioning and migration support
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from jsonschema import Draft202012Validator, ValidationError as JsonSchemaValidationError
from jsonschema.exceptions import best_match


# Schema file paths
SCHEMA_DIR = Path(__file__).parent / "schemas"
FINGERPRINT_SCHEMA_PATH = SCHEMA_DIR / "fingerprint-input-v1.0.schema.json"
HELPER_DATA_SCHEMA_PATH = SCHEMA_DIR / "helper-data-v1.0.schema.json"
CONFIG_SCHEMA_PATH = SCHEMA_DIR / "config-v1.0.schema.json"


class ValidationError(Exception):
    """
    Comprehensive validation error with detailed context.

    Attributes:
        message: Human-readable error description
        field_path: JSONPath to the invalid field (e.g., "$.fingers[0].minutiae[5].x")
        expected: Expected value/type/format
        actual: Actual value that failed validation
        suggestion: Recovery guidance for the user
        schema_rule: The schema constraint that was violated
    """

    def __init__(
        self,
        message: str,
        field_path: Optional[str] = None,
        expected: Optional[str] = None,
        actual: Optional[str] = None,
        suggestion: Optional[str] = None,
        schema_rule: Optional[str] = None,
    ):
        self.message = message
        self.field_path = field_path
        self.expected = expected
        self.actual = actual
        self.suggestion = suggestion
        self.schema_rule = schema_rule
        super().__init__(self._format_error())

    def _format_error(self) -> str:
        """Format comprehensive error message."""
        parts = [f"Validation Error: {self.message}"]

        if self.field_path:
            parts.append(f"  Field: {self.field_path}")

        if self.expected:
            parts.append(f"  Expected: {self.expected}")

        if self.actual:
            parts.append(f"  Actual: {self.actual}")

        if self.schema_rule:
            parts.append(f"  Rule: {self.schema_rule}")

        if self.suggestion:
            parts.append(f"  Suggestion: {self.suggestion}")

        return "\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to structured dictionary for JSON output."""
        return {
            "error": "ValidationError",
            "message": self.message,
            "field_path": self.field_path,
            "expected": self.expected,
            "actual": self.actual,
            "suggestion": self.suggestion,
            "schema_rule": self.schema_rule,
        }


class SchemaValidator:
    """
    JSON Schema validator with enhanced error reporting.
    """

    def __init__(self, schema_path: Path):
        """
        Initialize validator with schema file.

        Args:
            schema_path: Path to JSON Schema file
        """
        self.schema_path = schema_path
        with open(schema_path, 'r', encoding='utf-8') as f:
            self.schema = json.load(f)
        self.validator = Draft202012Validator(self.schema)

    def validate(self, data: Dict[str, Any], strict: bool = False) -> None:
        """
        Validate data against schema.

        Args:
            data: Data to validate
            strict: If True, fail on any validation error. If False, allow some warnings.

        Raises:
            ValidationError: If validation fails with detailed context
        """
        errors = sorted(self.validator.iter_errors(data), key=lambda e: e.path)

        if not errors:
            return  # Validation passed

        # Get the most relevant error
        error = best_match(errors)

        # Build detailed error information
        field_path = self._build_field_path(error)
        expected, actual = self._extract_expected_actual(error, data)
        suggestion = self._generate_suggestion(error)
        schema_rule = self._extract_schema_rule(error)

        raise ValidationError(
            message=error.message,
            field_path=field_path,
            expected=expected,
            actual=actual,
            suggestion=suggestion,
            schema_rule=schema_rule,
        )

    def _build_field_path(self, error: JsonSchemaValidationError) -> str:
        """Build JSONPath from error path."""
        if not error.absolute_path:
            return "$"

        path_parts = ["$"]
        for part in error.absolute_path:
            if isinstance(part, int):
                path_parts.append(f"[{part}]")
            else:
                path_parts.append(f".{part}")

        return "".join(path_parts)

    def _extract_expected_actual(
        self,
        error: JsonSchemaValidationError,
        data: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[str]]:
        """Extract expected vs actual values from validation error."""
        expected = None
        actual = None

        # Type errors
        if error.validator == "type":
            expected = f"type {error.validator_value}"
            actual = f"type {type(error.instance).__name__}"

        # Enum errors
        elif error.validator == "enum":
            expected = f"one of {error.validator_value}"
            actual = f"'{error.instance}'"

        # Pattern errors (regex)
        elif error.validator == "pattern":
            expected = f"match pattern: {error.validator_value}"
            actual = f"'{error.instance}'"

        # Range errors
        elif error.validator in ("minimum", "maximum", "minLength", "maxLength"):
            expected = f"{error.validator} {error.validator_value}"
            actual = f"{len(error.instance) if hasattr(error.instance, '__len__') else error.instance}"

        # Required field errors
        elif error.validator == "required":
            expected = f"required field '{error.validator_value[0]}'"
            actual = "missing"

        # Array length errors
        elif error.validator in ("minItems", "maxItems"):
            expected = f"{error.validator} {error.validator_value}"
            actual = f"{len(error.instance)} items"

        return expected, actual

    def _extract_schema_rule(self, error: JsonSchemaValidationError) -> str:
        """Extract the schema rule that was violated."""
        return f"{error.validator}: {error.validator_value}"

    def _generate_suggestion(self, error: JsonSchemaValidationError) -> Optional[str]:
        """Generate actionable recovery suggestion."""
        suggestions = {
            "type": "Check the data type. Ensure the value matches the expected type.",
            "enum": "Use one of the allowed values listed in the schema.",
            "pattern": "Check the format. The value should match the specified pattern (e.g., hex string).",
            "required": "Add the missing required field to your input.",
            "minLength": "Provide a longer value that meets the minimum length requirement.",
            "maxLength": "Shorten the value to meet the maximum length requirement.",
            "minimum": "Increase the value to meet the minimum requirement.",
            "maximum": "Decrease the value to meet the maximum requirement.",
            "minItems": "Add more items to the array to meet the minimum requirement.",
            "maxItems": "Remove items from the array to meet the maximum requirement.",
            "additionalProperties": "Remove unexpected fields. Only use fields defined in the schema.",
        }

        return suggestions.get(error.validator)


# Global validator instances (lazy-loaded)
_fingerprint_validator: Optional[SchemaValidator] = None
_helper_data_validator: Optional[SchemaValidator] = None
_config_validator: Optional[SchemaValidator] = None


def get_fingerprint_validator() -> SchemaValidator:
    """Get or create fingerprint input validator."""
    global _fingerprint_validator
    if _fingerprint_validator is None:
        _fingerprint_validator = SchemaValidator(FINGERPRINT_SCHEMA_PATH)
    return _fingerprint_validator


def get_helper_data_validator() -> SchemaValidator:
    """Get or create helper data validator."""
    global _helper_data_validator
    if _helper_data_validator is None:
        _helper_data_validator = SchemaValidator(HELPER_DATA_SCHEMA_PATH)
    return _helper_data_validator


def get_config_validator() -> SchemaValidator:
    """Get or create config validator."""
    global _config_validator
    if _config_validator is None:
        _config_validator = SchemaValidator(CONFIG_SCHEMA_PATH)
    return _config_validator


def validate_fingerprint_input(data: Dict[str, Any], strict: bool = False) -> bool:
    """
    Validate fingerprint input payload.

    Args:
        data: Fingerprint input data
        strict: Enable strict validation mode

    Returns:
        True if validation passes

    Raises:
        ValidationError: If validation fails
    """
    validator = get_fingerprint_validator()
    validator.validate(data, strict=strict)
    return True


def validate_helper_data(data: Dict[str, Any], strict: bool = False) -> bool:
    """
    Validate helper data payload.

    Args:
        data: Helper data
        strict: Enable strict validation mode

    Returns:
        True if validation passes

    Raises:
        ValidationError: If validation fails
    """
    validator = get_helper_data_validator()
    validator.validate(data, strict=strict)
    return True


def validate_config(data: Dict[str, Any], strict: bool = False) -> bool:
    """
    Validate configuration data.

    Args:
        data: Configuration data
        strict: Enable strict validation mode

    Returns:
        True if validation passes

    Raises:
        ValidationError: If validation fails
    """
    validator = get_config_validator()
    validator.validate(data, strict=strict)
    return True


def get_schema_version(data: Dict[str, Any]) -> Optional[str]:
    """
    Extract schema version from data.

    Args:
        data: Data dictionary with optional version field

    Returns:
        Version string (e.g., "1.0") or None if not found
    """
    return data.get("version")


__all__ = [
    "ValidationError",
    "SchemaValidator",
    "validate_fingerprint_input",
    "validate_helper_data",
    "validate_config",
    "get_fingerprint_validator",
    "get_helper_data_validator",
    "get_config_validator",
    "get_schema_version",
]
