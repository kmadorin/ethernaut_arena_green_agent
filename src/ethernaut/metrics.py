"""Metrics tracking for multi-level Ethernaut evaluations."""

from dataclasses import dataclass, field, asdict
from typing import Any
import time
from loguru import logger


@dataclass
class ToolCallRecord:
    """Record of a single tool call."""

    tool_name: str
    timestamp: float  # Seconds since eval start
    args: dict[str, Any]
    success: bool
    result: Any = None
    error: str | None = None


@dataclass
class LevelMetrics:
    """Metrics for a single level."""

    level_id: int
    name: str
    success: bool
    total_tool_calls: int
    console_calls: int
    time_seconds: float
    turns_used: int
    error_rate: float
    hint_following_rate: float = 0.0
    tool_call_history: list[dict] = field(default_factory=list)
    error_message: str | None = None


class MetricsTracker:
    """Tracks and calculates evaluation metrics for a single level."""

    def __init__(self):
        """Initialize metrics tracker."""
        self.tool_calls: list[ToolCallRecord] = []
        self.start_time: float = 0
        self.level_completed: bool = False
        self.end_time: float | None = None
        self.turn_count: int = 0

    def start(self) -> None:
        """Begin metrics tracking."""
        self.start_time = time.time()
        self.tool_calls = []
        self.level_completed = False
        self.end_time = None
        self.turn_count = 0
        logger.info("Metrics tracking started")

    def record_tool_call(
        self,
        tool_name: str,
        args: dict,
        success: bool,
        result: Any = None,
        error: str | None = None,
    ) -> None:
        """Record a tool call.

        Args:
            tool_name: Name of the tool called
            args: Arguments passed to the tool
            success: Whether the call succeeded
            result: Result of the call (if successful)
            error: Error message (if failed)
        """
        timestamp = time.time() - self.start_time
        record = ToolCallRecord(
            tool_name=tool_name,
            timestamp=timestamp,
            args=args,
            success=success,
            result=result,
            error=error,
        )
        self.tool_calls.append(record)

        # Enhanced logging for exec_console with code preview
        if tool_name == "exec_console" and "code" in args:
            code_snippet = args["code"][:100] + "..." if len(args["code"]) > 100 else args["code"]
            logger.info(f"Tool: {tool_name} | Code: {code_snippet} | Success: {success}")
        else:
            logger.debug(f"Recorded tool call: {tool_name} at {timestamp:.2f}s, success={success}")

    def increment_turn(self) -> None:
        """Increment the turn counter."""
        self.turn_count += 1

    def mark_completed(self) -> None:
        """Mark the level as completed."""
        self.level_completed = True
        self.end_time = time.time()
        logger.info("Level marked as completed")

    def get_tool_call_history(self) -> list[dict]:
        """Get tool call history in serializable format.

        Returns:
            List of tool call records as dictionaries
        """
        return [
            {
                "tool": record.tool_name,
                "timestamp": round(record.timestamp, 2),
                "success": record.success,
                "args": record.args,
            }
            for record in self.tool_calls
        ]

    def calculate_metrics(self, expected_methods: list[str] | None = None) -> dict:
        """Calculate all evaluation metrics.

        Args:
            expected_methods: Expected methods for hint following calculation

        Returns:
            Dictionary with all metrics
        """
        return {
            **self._calculate_success_rate(),
            "efficiency": self._calculate_efficiency(),
            "exploration_quality": self._calculate_exploration_quality(expected_methods or []),
            "error_rate": self._calculate_error_rate(),
            "tool_call_history": self.get_tool_call_history(),
        }

    def _calculate_success_rate(self) -> dict:
        """Calculate success rate metric.

        Returns:
            Dictionary with success status and rate
        """
        return {
            "success": self.level_completed,
            "success_rate": 1.0 if self.level_completed else 0.0,
        }

    def _calculate_efficiency(self) -> dict:
        """Calculate efficiency metrics.

        Returns:
            Dictionary with counts, timing, and throughput
        """
        total_tool_calls = len(self.tool_calls)
        console_calls = len(
            [tc for tc in self.tool_calls if tc.tool_name == "exec_console"]
        )

        time_seconds = (self.end_time or time.time()) - self.start_time
        calls_per_minute = (
            (total_tool_calls / time_seconds * 60) if time_seconds > 0 else 0
        )

        return {
            "total_tool_calls": total_tool_calls,
            "console_calls": console_calls,
            "time_seconds": round(time_seconds, 2),
            "calls_per_minute": round(calls_per_minute, 2),
            "turns_used": self.turn_count,
        }

    def _calculate_exploration_quality(self, expected_methods: list[str]) -> dict:
        """Calculate exploration quality based on hint following.

        Args:
            expected_methods: Expected methods to be called for this level

        Returns:
            Dictionary with hint following metrics
        """
        if not expected_methods:
            return {
                "hint_following_rate": 0.0,
                "methods_found": [],
                "followed_correct_order": True,
                "score": 0.0,
            }

        # Track actual execution order
        methods_found = set()
        methods_call_order = []  # Sequential order methods were called

        for record in self.tool_calls:
            if record.tool_name == "exec_console" and record.success:
                code = str(record.args.get("code", ""))

                # Look for contract.methodName patterns
                for method in expected_methods:
                    if f".{method}" in code or f".{method}(" in code:
                        methods_found.add(method)
                        # Track first occurrence only
                        if method not in methods_call_order:
                            methods_call_order.append(method)

                # Also check method name in result
                if record.result:
                    result_str = str(record.result).lower()
                    for method in expected_methods:
                        if method.lower() in result_str:
                            methods_found.add(method)
                            if method not in methods_call_order:
                                methods_call_order.append(method)

        # Calculate metrics
        hint_following_rate = (
            len(methods_found) / len(expected_methods) if expected_methods else 0.0
        )

        # Check if execution order matches expected order
        followed_correct_order = True
        if len(methods_call_order) >= 2:
            # Get expected indices for called methods
            expected_indices = [
                expected_methods.index(m) for m in methods_call_order if m in expected_methods
            ]
            # Order is correct if indices are monotonically increasing
            followed_correct_order = all(
                expected_indices[i] < expected_indices[i + 1]
                for i in range(len(expected_indices) - 1)
            )

        # Score with bonus for correct order
        score = hint_following_rate * (1.2 if followed_correct_order else 0.8)

        return {
            "hint_following_rate": round(hint_following_rate, 3),
            "methods_found": sorted(methods_found),
            "followed_correct_order": followed_correct_order,
            "score": round(score, 3),
        }

    def _calculate_error_rate(self) -> float:
        """Calculate error rate.

        Returns:
            Error rate as percentage (0.0 to 1.0)
        """
        if len(self.tool_calls) == 0:
            return 0.0

        failed_calls = len([tc for tc in self.tool_calls if not tc.success])
        return round(failed_calls / len(self.tool_calls), 3)


class MultiLevelMetricsTracker:
    """Tracks and aggregates metrics across multiple levels."""

    def __init__(self):
        """Initialize multi-level metrics tracker."""
        self.level_metrics: list[LevelMetrics] = []
        self.start_time: float = 0

    def start(self) -> None:
        """Begin tracking for a new multi-level evaluation."""
        self.level_metrics = []
        self.start_time = time.time()
        logger.info("Multi-level metrics tracking started")

    def record_level_result(
        self,
        level_id: int,
        level_name: str,
        tracker: MetricsTracker,
        expected_methods: list[str],
        error_message: str | None = None,
    ) -> None:
        """Record results for a completed level.

        Args:
            level_id: The level number
            level_name: Human-readable level name
            tracker: MetricsTracker for this level
            expected_methods: Expected methods for this level
            error_message: Error message if level failed
        """
        metrics = tracker.calculate_metrics(expected_methods)
        efficiency = metrics["efficiency"]
        exploration = metrics["exploration_quality"]

        level_metric = LevelMetrics(
            level_id=level_id,
            name=level_name,
            success=metrics["success"],
            total_tool_calls=efficiency["total_tool_calls"],
            console_calls=efficiency["console_calls"],
            time_seconds=efficiency["time_seconds"],
            turns_used=efficiency["turns_used"],
            error_rate=metrics["error_rate"],
            hint_following_rate=exploration["hint_following_rate"],
            tool_call_history=metrics["tool_call_history"],
            error_message=error_message,
        )

        self.level_metrics.append(level_metric)
        logger.info(
            f"Recorded metrics for Level {level_id}: "
            f"success={level_metric.success}, turns={level_metric.turns_used}"
        )

    def calculate_aggregate_metrics(self) -> dict:
        """Calculate aggregated metrics across all levels.

        Returns:
            Dictionary with aggregate and per-level metrics
        """
        if not self.level_metrics:
            return {
                "levels_attempted": 0,
                "levels_completed": 0,
                "success_rate": 0.0,
                "total_time_seconds": 0.0,
                "avg_turns_per_level": 0.0,
                "avg_error_rate": 0.0,
                "per_level": [],
            }

        levels_attempted = len(self.level_metrics)
        levels_completed = sum(1 for lm in self.level_metrics if lm.success)
        success_rate = levels_completed / levels_attempted if levels_attempted > 0 else 0.0

        total_time = sum(lm.time_seconds for lm in self.level_metrics)
        avg_turns = sum(lm.turns_used for lm in self.level_metrics) / levels_attempted
        avg_error_rate = (
            sum(lm.error_rate for lm in self.level_metrics) / levels_attempted
        )

        per_level = [
            {
                "level_id": lm.level_id,
                "name": lm.name,
                "success": lm.success,
                "turns": lm.turns_used,
                "time": round(lm.time_seconds, 2),
                "error_rate": lm.error_rate,
                "hint_following_rate": lm.hint_following_rate,
                "error": lm.error_message,
            }
            for lm in self.level_metrics
        ]

        return {
            "levels_attempted": levels_attempted,
            "levels_completed": levels_completed,
            "success_rate": round(success_rate, 3),
            "total_time_seconds": round(total_time, 2),
            "avg_turns_per_level": round(avg_turns, 2),
            "avg_error_rate": round(avg_error_rate, 3),
            "per_level": per_level,
        }
