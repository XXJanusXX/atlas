from dataclasses import dataclass


@dataclass(frozen=True)
class SessionState:
    execution_mode: str = "paper"
    live_execution_enabled: bool = False


def assert_paper_only(state: SessionState) -> None:
    if state.execution_mode != "paper" or state.live_execution_enabled:
        raise RuntimeError("Safety invariant violated: this build is paper-only.")
