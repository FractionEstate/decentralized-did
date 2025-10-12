"""
Logging and output utilities for CLI.

Provides structured logging with multiple levels (quiet, normal, verbose, debug)
and colored output support.
"""

from __future__ import annotations

import sys
from datetime import datetime
from enum import IntEnum
from typing import Any, Dict, Optional, TextIO


class LogLevel(IntEnum):
    """Log level enumeration."""

    QUIET = 0    # Errors only
    NORMAL = 1   # Normal output (milestones)
    VERBOSE = 2  # Verbose output (details)
    DEBUG = 3    # Debug output (everything)


class CLILogger:
    """
    CLI logger with structured output and color support.

    Supports multiple log levels, colored output, JSON mode, and timestamps.
    """

    def __init__(
        self,
        level: LogLevel = LogLevel.NORMAL,
        use_color: bool = True,
        json_mode: bool = False,
        show_timestamp: bool = False,
        output: TextIO = sys.stdout,
        error_output: TextIO = sys.stderr,
    ):
        """
        Initialize CLI logger.

        Args:
            level: Logging level
            use_color: Enable colored output
            json_mode: Output structured JSON instead of text
            show_timestamp: Show timestamps in output
            output: Standard output stream
            error_output: Error output stream
        """
        self.level = level
        self.use_color = use_color and output.isatty()
        self.json_mode = json_mode
        self.show_timestamp = show_timestamp
        self.output = output
        self.error_output = error_output
        self._start_time = datetime.now()

    # ANSI color codes
    COLORS = {
        "reset": "\033[0m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "bold": "\033[1m",
        "dim": "\033[2m",
    }

    def _colorize(self, text: str, color: str) -> str:
        """Apply color to text if color is enabled."""
        if not self.use_color:
            return text
        return f"{self.COLORS.get(color, '')}{text}{self.COLORS['reset']}"

    def _format_message(
        self,
        message: str,
        level: str,
        color: str,
        data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format message with optional timestamp and data."""
        if self.json_mode:
            import json
            output = {
                "timestamp": datetime.now().isoformat(),
                "level": level,
                "message": message,
            }
            if data:
                output["data"] = data
            return json.dumps(output)

        parts = []

        if self.show_timestamp:
            timestamp = datetime.now().strftime("%H:%M:%S")
            parts.append(self._colorize(f"[{timestamp}]", "dim"))

        level_label = self._colorize(f"[{level}]", color)
        parts.append(level_label)
        parts.append(message)

        if data:
            data_str = " ".join(f"{k}={v}" for k, v in data.items())
            parts.append(self._colorize(f"({data_str})", "dim"))

        return " ".join(parts)

    def error(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log error message (always shown)."""
        formatted = self._format_message(message, "ERROR", "red", data)
        print(formatted, file=self.error_output)

    def warning(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log warning message (shown at NORMAL and above)."""
        if self.level >= LogLevel.NORMAL:
            formatted = self._format_message(message, "WARN", "yellow", data)
            print(formatted, file=self.output)

    def info(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log info message (shown at NORMAL and above)."""
        if self.level >= LogLevel.NORMAL:
            formatted = self._format_message(message, "INFO", "blue", data)
            print(formatted, file=self.output)

    def success(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log success message (shown at NORMAL and above)."""
        if self.level >= LogLevel.NORMAL:
            formatted = self._format_message(message, "OK", "green", data)
            print(formatted, file=self.output)

    def verbose(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log verbose message (shown at VERBOSE and above)."""
        if self.level >= LogLevel.VERBOSE:
            formatted = self._format_message(message, "VERBOSE", "cyan", data)
            print(formatted, file=self.output)

    def debug(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log debug message (shown at DEBUG level)."""
        if self.level >= LogLevel.DEBUG:
            formatted = self._format_message(message, "DEBUG", "magenta", data)
            print(formatted, file=self.output)

    def step(self, message: str) -> None:
        """Log a major step/milestone (shown at NORMAL and above)."""
        if self.level >= LogLevel.NORMAL:
            if self.json_mode:
                self.info(message)
            else:
                header = self._colorize("▶", "green")
                print(f"\n{header} {self._colorize(message, 'bold')}",
                      file=self.output)

    def elapsed(self) -> float:
        """Get elapsed time since logger creation in seconds."""
        return (datetime.now() - self._start_time).total_seconds()

    def print(self, message: str) -> None:
        """Print plain message without formatting (respects quiet mode)."""
        if self.level > LogLevel.QUIET:
            print(message, file=self.output)

    def print_json(self, data: Dict[str, Any]) -> None:
        """Print JSON data (always shown)."""
        import json
        print(json.dumps(data, indent=2), file=self.output)


def create_logger(
    quiet: bool = False,
    verbose: bool = False,
    debug: bool = False,
    json_output: bool = False,
    no_color: bool = False,
    show_timestamp: bool = False,
) -> CLILogger:
    """
    Create CLI logger from common CLI flags.

    Args:
        quiet: Suppress all output except errors
        verbose: Enable verbose output
        debug: Enable debug output
        json_output: Output structured JSON
        no_color: Disable colored output
        show_timestamp: Show timestamps

    Returns:
        Configured CLILogger instance
    """
    # Determine log level
    if debug:
        level = LogLevel.DEBUG
    elif verbose:
        level = LogLevel.VERBOSE
    elif quiet:
        level = LogLevel.QUIET
    else:
        level = LogLevel.NORMAL

    return CLILogger(
        level=level,
        use_color=not no_color,
        json_mode=json_output,
        show_timestamp=show_timestamp or debug,
    )
