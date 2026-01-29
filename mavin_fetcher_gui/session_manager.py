from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal

from .session_state import SessionState


class SessionManager(QObject):
    changed = pyqtSignal(object)  # emits SessionState

    def __init__(self, initial: SessionState | None = None):
        super().__init__()
        self._state = initial or SessionState()

    @property
    def state(self) -> SessionState:
        return self._state

    def set_state(self, s: SessionState) -> None:
        self._state = s
        self.changed.emit(self._state)

    def update(self, **kwargs) -> None:
        # Create a new state object (keeps it predictable)
        s = SessionState(**{**self._state.__dict__, **kwargs})
        self.set_state(s)
