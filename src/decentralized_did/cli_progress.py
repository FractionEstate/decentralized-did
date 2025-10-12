"""
Progress indicators for CLI operations.

Provides progress bars and spinners for long-running operations.
"""

from __future__ import annotations

import sys
import time
from contextlib import contextmanager
from typing import Iterator, Optional, TextIO


class ProgressBar:
    """
    Simple progress bar for CLI.

    Shows progress percentage, bar visualization, and optional status text.
    """

    def __init__(
        self,
        total: int,
        width: int = 40,
        prefix: str = "",
        show_percent: bool = True,
        show_count: bool = True,
        output: TextIO = sys.stdout,
    ):
        """
        Initialize progress bar.

        Args:
            total: Total number of items
            width: Width of progress bar in characters
            prefix: Prefix text before progress bar
            show_percent: Show percentage complete
            show_count: Show item count (current/total)
            output: Output stream
        """
        self.total = total
        self.width = width
        self.prefix = prefix
        self.show_percent = show_percent
        self.show_count = show_count
        self.output = output
        self.current = 0
        self._start_time = time.time()

    def update(self, n: int = 1, status: Optional[str] = None) -> None:
        """
        Update progress bar.

        Args:
            n: Number of items completed
            status: Optional status text to show
        """
        self.current += n
        self._render(status)

    def _render(self, status: Optional[str] = None) -> None:
        """Render progress bar to output."""
        if not self.output.isatty():
            return

        # Calculate progress
        progress = self.current / self.total if self.total > 0 else 0
        filled = int(self.width * progress)

        # Build bar
        bar = "█" * filled + "░" * (self.width - filled)

        # Build components
        parts = []

        if self.prefix:
            parts.append(self.prefix)

        parts.append(f"[{bar}]")

        if self.show_percent:
            parts.append(f"{progress * 100:.1f}%")

        if self.show_count:
            parts.append(f"({self.current}/{self.total})")

        if status:
            parts.append(f"- {status}")

        # Render
        line = " ".join(parts)
        self.output.write(f"\r{line}")
        self.output.flush()

    def finish(self, status: str = "Complete") -> None:
        """Finish progress bar with final status."""
        self.current = self.total
        self._render(status)
        if self.output.isatty():
            self.output.write("\n")
            self.output.flush()

    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self._start_time


class Spinner:
    """
    Simple spinner for long-running operations.

    Shows animated spinner with status text.
    """

    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(
        self,
        message: str = "Processing...",
        output: TextIO = sys.stdout,
    ):
        """
        Initialize spinner.

        Args:
            message: Status message to show
            output: Output stream
        """
        self.message = message
        self.output = output
        self.frame = 0
        self._active = False
        self._start_time = time.time()

    def start(self) -> None:
        """Start spinner animation."""
        if self.output.isatty():
            self._active = True
            self._render()

    def update(self, message: Optional[str] = None) -> None:
        """
        Update spinner message.

        Args:
            message: New status message
        """
        if message:
            self.message = message
        if self._active:
            self.frame = (self.frame + 1) % len(self.FRAMES)
            self._render()

    def _render(self) -> None:
        """Render spinner frame to output."""
        if not self.output.isatty():
            return

        frame = self.FRAMES[self.frame]
        elapsed = time.time() - self._start_time

        line = f"\r{frame} {self.message} ({elapsed:.1f}s)"
        self.output.write(line)
        self.output.flush()

    def stop(self, final_message: Optional[str] = None) -> None:
        """
        Stop spinner animation.

        Args:
            final_message: Optional final message to show
        """
        if not self._active:
            return

        self._active = False

        if final_message:
            if self.output.isatty():
                # Clear spinner line
                self.output.write("\r" + " " * 80 + "\r")
                self.output.write(f"✓ {final_message}\n")
            else:
                self.output.write(f"{final_message}\n")
        elif self.output.isatty():
            self.output.write("\n")

        self.output.flush()

    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self._start_time


@contextmanager
def progress_bar(
    total: int,
    prefix: str = "Processing",
    **kwargs
) -> Iterator[ProgressBar]:
    """
    Context manager for progress bar.

    Args:
        total: Total number of items
        prefix: Prefix text
        **kwargs: Additional arguments for ProgressBar

    Yields:
        ProgressBar instance

    Example:
        >>> with progress_bar(100, "Enrolling") as bar:
        ...     for i in range(100):
        ...         # Do work
        ...         bar.update(1, f"Item {i}")
        ...     bar.finish("All done!")
    """
    bar = ProgressBar(total, prefix=prefix, **kwargs)
    try:
        yield bar
    finally:
        if bar.current < bar.total:
            bar.finish("Interrupted")


@contextmanager
def spinner(message: str = "Processing...", **kwargs) -> Iterator[Spinner]:
    """
    Context manager for spinner.

    Args:
        message: Status message
        **kwargs: Additional arguments for Spinner

    Yields:
        Spinner instance

    Example:
        >>> with spinner("Loading data...") as s:
        ...     # Do long-running work
        ...     time.sleep(2)
        ...     s.update("Still loading...")
        ...     time.sleep(2)
        ...     s.stop("Data loaded")
    """
    spin = Spinner(message, **kwargs)
    spin.start()
    try:
        yield spin
    finally:
        spin.stop()
