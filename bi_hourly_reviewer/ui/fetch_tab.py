"""
Fetch Tab.

Responsibilities:
    - Let the user configure the review time window.
    - Start date + hour on the same row, both selectable.
    - Time frame (hours) is adjustable; end time is auto-computed.
    - Run the fetch pipeline in a background thread.
    - Display progress log in real time.
    - Emit results to the main window when done.
"""

from datetime import datetime, timedelta

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QDateEdit,
    QPushButton,
    QTextBrowser,
    QProgressBar,
    QGroupBox,
    QFormLayout,
    QSizePolicy,
)
from PyQt5.QtCore import (
    Qt,
    QThread,
    pyqtSignal,
    QDate,
)
from PyQt5.QtGui import QFont

from config import DEFAULT_REVIEW_HOURS
from ui.styles import COLORS, FONT_FAMILY_MONO, SPACING_MD, SPACING_LG, SPACING_XL


# =============================================================================
# Custom step input widget — replaces QSpinBox with clean +/- buttons
# =============================================================================

class StepInput(QWidget):
    """
    A numeric input with large, clickable minus/plus buttons.
    Much more usable than QSpinBox's tiny arrows.
    """

    valueChanged = pyqtSignal(int)

    def __init__(
        self,
        value: int = 0,
        minimum: int = 0,
        maximum: int = 99,
        suffix: str = "",
        wrap: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self._value = value
        self._min = minimum
        self._max = maximum
        self._suffix = suffix
        self._wrap = wrap
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        btn_style = (
            f"QPushButton {{"
            f"  background-color: {COLORS['bg_tertiary']};"
            f"  color: {COLORS['text_primary']};"
            f"  border: 1px solid {COLORS['border']};"
            f"  font-size: 14pt;"
            f"  font-weight: bold;"
            f"  padding: 0px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {COLORS['border']};"
            f"}}"
            f"QPushButton:pressed {{"
            f"  background-color: {COLORS['accent_blue']};"
            f"}}"
        )

        # Minus button
        self.minus_btn = QPushButton("−")
        self.minus_btn.setFixedSize(36, 32)
        self.minus_btn.setStyleSheet(
            btn_style + f"QPushButton {{ border-radius: 4px 0px 0px 4px; border-right: none; }}"
        )
        self.minus_btn.clicked.connect(self._decrement)
        layout.addWidget(self.minus_btn)

        # Value display
        self.value_label = QLabel()
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setMinimumWidth(80)
        self.value_label.setFixedHeight(32)
        self.value_label.setFont(QFont(FONT_FAMILY_MONO, 10))
        self.value_label.setStyleSheet(
            f"background-color: {COLORS['bg_tertiary']};"
            f"color: {COLORS['text_primary']};"
            f"border-top: 1px solid {COLORS['border']};"
            f"border-bottom: 1px solid {COLORS['border']};"
            f"padding: 0 8px;"
        )
        layout.addWidget(self.value_label)

        # Plus button
        self.plus_btn = QPushButton("+")
        self.plus_btn.setFixedSize(36, 32)
        self.plus_btn.setStyleSheet(
            btn_style + f"QPushButton {{ border-radius: 0px 4px 4px 0px; border-left: none; }}"
        )
        self.plus_btn.clicked.connect(self._increment)
        layout.addWidget(self.plus_btn)

        self._update_display()

    def _increment(self):
        if self._value < self._max:
            self._value += 1
        elif self._wrap:
            self._value = self._min
        self._update_display()
        self.valueChanged.emit(self._value)

    def _decrement(self):
        if self._value > self._min:
            self._value -= 1
        elif self._wrap:
            self._value = self._max
        self._update_display()
        self.valueChanged.emit(self._value)

    def _update_display(self):
        self.value_label.setText(f"{self._value}{self._suffix}")

    def value(self) -> int:
        return self._value

    def setValue(self, val: int):
        self._value = max(self._min, min(self._max, val))
        self._update_display()


# =============================================================================
# Fetch Worker
# =============================================================================

class FetchWorker(QThread):
    """
    Background thread for running the fetch pipeline.
    Keeps the UI responsive during long fetches.
    """
    progress = pyqtSignal(str)
    cell_complete = pyqtSignal(dict)
    finished_result = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, end_dt: datetime, hours: int, parent=None):
        super().__init__(parent)
        self.end_dt = end_dt
        self.hours = hours

    def run(self):
        try:
            from core.fetch_pipeline import run_fetch
            results = run_fetch(
                end_dt=self.end_dt,
                hours=self.hours,
                on_progress=self._on_progress,
                on_cell_complete=self._on_cell_complete,
            )
            self.finished_result.emit(results)
        except Exception as e:
            self.error_occurred.emit(str(e))

    def _on_progress(self, msg: str):
        self.progress.emit(msg)

    def _on_cell_complete(self, result: dict):
        self.cell_complete.emit(result)


# =============================================================================
# Fetch Tab
# =============================================================================

class FetchTab(QWidget):
    """Fetch configuration and execution tab."""

    fetch_complete = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Build the fetch tab layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_XL, SPACING_XL, SPACING_XL, SPACING_XL)
        layout.setSpacing(SPACING_LG)

        # ---- Configuration Section ----
        config_group = QGroupBox("Review Configuration")
        config_inner = QVBoxLayout(config_group)
        config_inner.setContentsMargins(SPACING_LG, SPACING_XL, SPACING_LG, SPACING_LG)
        config_inner.setSpacing(SPACING_MD)

        # Row 1: Review Start — date + hour on same line
        start_row = QHBoxLayout()
        start_row.setSpacing(SPACING_MD)

        start_label = QLabel("Review Start:")
        start_label.setFixedWidth(100)
        start_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        start_row.addWidget(start_label)

        self.date_edit = QDateEdit()
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setFixedHeight(32)
        self.date_edit.setStyleSheet(
            f"QDateEdit {{"
            f"  background-color: {COLORS['bg_tertiary']};"
            f"  color: {COLORS['text_primary']};"
            f"  border: 1px solid {COLORS['border']};"
            f"  border-radius: 4px;"
            f"  padding: 4px 10px;"
            f"  font-family: '{FONT_FAMILY_MONO}';"
            f"}}"
            f"QDateEdit:focus {{ border-color: {COLORS['border_focus']}; }}"
            f"QDateEdit::drop-down {{"
            f"  subcontrol-origin: padding;"
            f"  subcontrol-position: center right;"
            f"  width: 24px;"
            f"  border: none;"
            f"}}"
            f"QDateEdit::down-arrow {{"
            f"  image: none;"
            f"  width: 0; height: 0;"
            f"  border-left: 5px solid transparent;"
            f"  border-right: 5px solid transparent;"
            f"  border-top: 5px solid {COLORS['text_secondary']};"
            f"}}"
        )
        self.date_edit.setFixedWidth(160)
        start_row.addWidget(self.date_edit)

        self.start_hour_input = StepInput(
            value=0, minimum=0, maximum=23,
            suffix=":00", wrap=True,
        )
        start_row.addWidget(self.start_hour_input)
        start_row.addStretch()

        config_inner.addLayout(start_row)

        # Row 2: Time Frame
        frame_row = QHBoxLayout()
        frame_row.setSpacing(SPACING_MD)

        frame_label = QLabel("Time Frame:")
        frame_label.setFixedWidth(100)
        frame_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        frame_row.addWidget(frame_label)

        self.hours_input = StepInput(
            value=DEFAULT_REVIEW_HOURS, minimum=1, maximum=24,
            suffix=" hrs",
        )
        frame_row.addWidget(self.hours_input)
        frame_row.addStretch()

        config_inner.addLayout(frame_row)

        # Row 3: Computed end time (read-only)
        end_row = QHBoxLayout()
        end_row.setSpacing(SPACING_MD)

        end_label = QLabel("Review End:")
        end_label.setFixedWidth(100)
        end_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        end_row.addWidget(end_label)

        self.end_time_label = QLabel()
        self.end_time_label.setStyleSheet(
            f"color: {COLORS['text_primary']}; "
            f"font-family: '{FONT_FAMILY_MONO}';"
            f"font-size: 10pt; "
            f"font-weight: 600;"
        )
        end_row.addWidget(self.end_time_label)
        end_row.addStretch()

        config_inner.addLayout(end_row)

        layout.addWidget(config_group)

        # ---- Action Buttons ----
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(SPACING_MD)

        btn_layout.addStretch()

        self.fetch_btn = QPushButton("Fetch Images")
        self.fetch_btn.setFixedWidth(160)
        btn_layout.addWidget(self.fetch_btn)

        layout.addLayout(btn_layout)

        # ---- Progress Bar ----
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)
        layout.addWidget(self.progress_bar)

        # ---- Log Area ----
        log_label = QLabel("Fetch Log")
        log_label.setObjectName("sectionHeader")
        layout.addWidget(log_label)

        self.log_browser = QTextBrowser()
        self.log_browser.setOpenExternalLinks(False)
        self.log_browser.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.log_browser)

        # Initialize to current date/hour
        self._set_to_now()

    def _connect_signals(self):
        """Connect UI signals to handlers."""
        self.fetch_btn.clicked.connect(self._on_fetch_clicked)
        self.date_edit.dateChanged.connect(self._update_end_time)
        self.start_hour_input.valueChanged.connect(self._update_end_time)
        self.hours_input.valueChanged.connect(self._update_end_time)

    def _set_to_now(self):
        """Set date and start hour to the current time."""
        now = datetime.now()
        self.date_edit.setDate(QDate(now.year, now.month, now.day))
        self.start_hour_input.setValue(now.hour)
        self._update_end_time()

    def _update_end_time(self):
        """Compute and display the end time from start + time frame."""
        end_dt = self._get_end_datetime()
        self.end_time_label.setText(end_dt.strftime("%Y-%m-%d  %H:%M"))

    def _get_start_datetime(self) -> datetime:
        """Build the start datetime from current UI values."""
        qdate = self.date_edit.date()
        start_hour = self.start_hour_input.value()
        return datetime(qdate.year(), qdate.month(), qdate.day(), start_hour, 0, 0)

    def _get_end_datetime(self) -> datetime:
        """Compute the end datetime from start + time frame."""
        return self._get_start_datetime() + timedelta(hours=self.hours_input.value())

    def _on_fetch_clicked(self):
        """Start the fetch pipeline in a background thread."""
        if self._worker and self._worker.isRunning():
            return

        end_dt = self._get_end_datetime()
        hours = self.hours_input.value()

        self.fetch_btn.setEnabled(False)
        self.fetch_btn.setText("Fetching...")
        self.progress_bar.setVisible(True)
        self.log_browser.clear()
        self._log("Starting fetch...")

        self._worker = FetchWorker(end_dt, hours)
        self._worker.progress.connect(self._log)
        self._worker.cell_complete.connect(self._on_cell_complete)
        self._worker.finished_result.connect(self._on_fetch_finished)
        self._worker.error_occurred.connect(self._on_fetch_error)
        self._worker.start()

    def _log(self, msg: str):
        """Append a message to the log browser."""
        self.log_browser.append(msg)
        scrollbar = self.log_browser.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _on_cell_complete(self, result: dict):
        """Handle individual cell fetch completion."""
        pass

    def _on_fetch_finished(self, results: dict):
        """Handle fetch pipeline completion."""
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("Fetch Images")
        self.progress_bar.setVisible(False)

        fetched = results.get("fetched", 0)
        failed = results.get("failed", 0)
        total = results.get("total_defects", 0)
        self._log(f"\n{'='*50}")
        self._log(f"DONE — {fetched} fetched, {failed} failed, {total} total defects")

        self.fetch_complete.emit(results)

    def _on_fetch_error(self, error_msg: str):
        """Handle fetch pipeline error."""
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("Fetch Images")
        self.progress_bar.setVisible(False)
        self._log(f"\nERROR: {error_msg}")