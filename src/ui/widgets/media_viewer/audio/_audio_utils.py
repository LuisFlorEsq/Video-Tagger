from pathlib import Path
from time import perf_counter

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, QUrl, Qt, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QHBoxLayout,
    QSlider,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from src.core.logger import logger
from src.infrastructure.array_media import (
    get_cached_waveform_envelope,
    load_waveform_envelope_cached,
)
from src.ui.styles import AppTheme, btn_primary
from src.ui.widgets.media_viewer.signal._signal_plot import WaveformWidget


class _WaveformLoadSignals(QObject):
    """
    Defines PySide6 Signals for communicating asynchronous task results.

    Signals:
        finished(str, int, object, bool, float, float): Emitted when the processing finishes
            - file_path (str): Path of the processed audio file
            - token (int): Validation token to match the UI load request state
            - envelope (np.ndarray): The computed float32 waveform data
            - cache_hit (bool): True if fetched from memory, False if decoded
            - decode_ms (float): Time spent decoding raw streams in miliseconds
            - elapsed_ms (float): Total operation execution time in miliseconds
    """

    finished = Signal(str, int, object, bool, float, float)


class _WaveformLoadTask(QRunnable):
    """
    A runnable worker to load and compute audio waveform in a background thread.

    Inherits from QRunnable to be managed and executed by a QThreadPool infrastructure.
    """

    def __init__(self, file_path: Path, token: int, target_bins: int) -> None:
        """
        Initializes the background waveform processing task

        Args:
            file_path (Path): Path to the target media/signal file
            token (int): Unique execution token for handling concurrent state drift
            target_bins (int): Desired horizontal resolution points for the widget
        """
        super().__init__()
        self.file_path = Path(file_path)
        self.token = token
        self.target_bins = target_bins
        self.signals = _WaveformLoadSignals()

    def run(self) -> None:
        """
        Executes the computionaly intensive decoding and downsampling

        Note:
            Runs completely inside a secondary Worker Thread from QThreadPool
            Emits the 'finished' signal safely back to the GUI thread upon completion
        """
        start = perf_counter()
        envelope, cache_hit = load_waveform_envelope_cached(
            self.file_path,
            target_bins=self.target_bins,
        )
        elapsed_ms = (perf_counter() - start) * 1000.0
        decode_ms = 0.0 if cache_hit else elapsed_ms
        self.signals.finished.emit(
            str(self.file_path),
            self.token,
            envelope,
            cache_hit,
            decode_ms,
            elapsed_ms,
        )


class AudioPlayerWidget(QWidget):
    """
    Self-contained custom UI component for audio playback and waveform visualization

    Integrates PySide6 Multimedia capabilities with multi-threaded audio envelope
    decoding to avoid freezing the GUI
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._player = QMediaPlayer(self)
        self._audio = QAudioOutput(self)
        self._player.setAudioOutput(self._audio)

        self._load_token = 0
        self._load_started_at = 0.0
        self._current_file_path: str | None = None
        self._media_ready_connected = False
        self._waveform_pool = QThreadPool.globalInstance()
        self._active_waveform_task: _WaveformLoadTask | None = None

        self._init_ui()
        self._connect_signals()

    def _disconnect_media_status_changed(self) -> None:
        if not self._media_ready_connected:
            return
        try:
            self._player.mediaStatusChanged.disconnect(self._on_media_status_changed)
        except RuntimeError:
            pass
        self._media_ready_connected = False

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        self._waveform = WaveformWidget()
        layout.addWidget(self._waveform, stretch=1)

        self._filename_lbl = QLabel("")
        self._filename_lbl.setAlignment(Qt.AlignCenter)
        self._filename_lbl.setStyleSheet(
            f"font-size: {AppTheme.FONT_BASE}; font-weight: bold; "
            f"color: {AppTheme.TEXT_PRIMARY};"
        )
        layout.addWidget(self._filename_lbl)

        timeline = QHBoxLayout()
        self._time_label = QLabel("00:00 / 00:00")
        self._time_label.setStyleSheet(
            f"font-size: {AppTheme.FONT_SM}; color: {AppTheme.TEXT_SECONDARY};"
        )
        self._time_label.setMinimumWidth(100)
        timeline.addWidget(self._time_label)

        self._slider = QSlider(Qt.Horizontal)
        self._slider.setRange(0, 0)
        timeline.addWidget(self._slider)
        layout.addLayout(timeline)

        controls = QHBoxLayout()
        controls.addStretch()

        self._play_btn = QPushButton()
        self._play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self._play_btn.setFixedSize(40, 40)
        self._play_btn.setStyleSheet(btn_primary())

        controls.addWidget(self._play_btn)
        controls.addStretch()
        layout.addLayout(controls)

    def _connect_signals(self) -> None:
        self._player.positionChanged.connect(self._on_position)
        self._player.durationChanged.connect(self._on_duration)
        self._player.playbackStateChanged.connect(self._on_state)
        self._player.errorOccurred.connect(self._on_error)
        self._play_btn.clicked.connect(self.toggle_playback)
        self._slider.sliderReleased.connect(self._on_slider_released)

    def load(self, file_path: str, filename: str) -> None:
        """
        Initialize the asynchronous loading sequence for a media file

        Resets UI states, tracks state changes via incremental tokens, and dispatches
        background tasks to process waveform visual structures.

        Args:
            file_path (str): Absolute filesystem path to the audio file
            filename (str): Name string of the file to display the UI header
        """
        path = Path(file_path)

        self.stop()

        self._load_started_at = perf_counter()
        self._current_file_path = str(path.resolve()) if path.exists() else None
        self._load_token += 1
        token = self._load_token

        logger.debug(
            "AudioPlayerWidget.load | token=%s | file=%s",
            token,
            path,
        )

        if not path.exists():
            self._reset_ui()
            self._filename_lbl.setText(filename)
            return

        self._disconnect_media_status_changed()
        self._reset_ui()
        self._filename_lbl.setText(filename)
        self._load_waveform_async(path, token)

        self._player.mediaStatusChanged.connect(self._on_media_status_changed)
        self._media_ready_connected = True
        self._player.setSource(QUrl.fromLocalFile(str(path.absolute())))

    def _on_media_status_changed(self, status) -> None:
        """Handles internal QMediaPlayer lifecycle status transitions.

        Args:
            status (QMediaPlayer.MediaStatus): The updated playback state from the core.
        """
        if status != QMediaPlayer.LoadedMedia:
            return

        self._disconnect_media_status_changed()

        token = self._load_token
        self._player.play()
        self._player.pause()
        self._player.setPosition(0)

        self._play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        if self._load_started_at:
            elapsed_ms = (perf_counter() - self._load_started_at) * 1000.0
            logger.debug(
                "AudioPlayerWidget.player_ready | token=%s | elapsed_ms=%.1f",
                token,
                elapsed_ms,
            )
        QTimer.singleShot(0, lambda: self._finalize_load(token))

    def _finalize_load(self, token: int) -> None:
        """
        Validates state compliance and finalizes internal setups

        Args:
            token (int): Request validation token checking for asynchronous convergence.
        """
        if token != self._load_token:
            return

    def toggle_playback(self) -> None:
        """
        Switches the current media player state between PlayingState and PausedState
        """
        if self._player.playbackState() == QMediaPlayer.PlayingState:
            self._player.pause()
        else:
            self._player.play()

    def stop(self) -> None:
        """
        Fully halts media playback, cancels state lifecycles, and clears current UI metrics
        """
        self._load_token += 1
        self._disconnect_media_status_changed()

        self._player.pause()
        self._player.stop()
        self._player.setPosition(0)
        self._player.setSource(QUrl())
        self._reset_ui()

        self._current_file_path = None
        self._load_started_at = 0.0
        self._active_waveform_task = None

    def dispose(self) -> None:
        self.stop()

    def _reset_ui(self) -> None:
        """
        Restores internal widgets, labels, sliders and drawing canvas to defatuls.
        """
        self._play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

        self._slider.blockSignals(True)
        self._slider.setRange(0, 0)
        self._slider.setValue(0)
        self._slider.blockSignals(False)

        self._time_label.setText("00:00 / 00:00")
        self._waveform.clear_waveform()
        self._active_waveform_task = None

    def _on_slider_released(self) -> None:
        """
        Synchronizes the backend QMediaPlayer position with user trackin inputs.
        """
        self._player.setPosition(self._slider.value())

    def _on_position(self, pos: int) -> None:
        """
        Updates the slider track bar and timing labels during continuous playback.

        Args:
            pos (int): Current milisecond timeline position of the track.
        """
        if not self._slider.isSliderDown():
            self._slider.blockSignals(True)
            self._slider.setValue(pos)
            self._slider.blockSignals(False)
        duration = self._player.duration()
        if duration > 0:
            self._waveform.set_progress(pos / duration)
        self._time_label.setText(f"{self.fmt(pos)} / {self.fmt(duration)}")

    def _on_duration(self, dur: int) -> None:
        """
        Configures slider constraints based on actual track lengths

        Args:
            dur (int): Full execution length of the current track in miliseconds.
        """
        if dur > 0:
            self._slider.setRange(0, dur)

    def _on_state(self, state) -> None:
        """
        Updates control interface button icons following playback state changes

        Args:
            state (QMediaPlayer.PlaybackState): Active target player state
        """
        playing = state == QMediaPlayer.PlayingState
        self._play_btn.setIcon(
            self.style().standardIcon(
                QStyle.SP_MediaPause if playing else QStyle.SP_MediaPlay
            )
        )

    def _on_error(self, error, error_string: str) -> None:
        """
        Logs and traces operational multimedia exceptions.

        Args:
            error (QMediaPlayer.Error): Exception identifier.
            error_string (str): Human-readable notification description.
        """
        logger.error(
            "AudioPlayerWidget._on_error | error=%s | message=%s", error, error_string
        )

    def _load_waveform_async(self, path: Path, token: int) -> None:
        """
        Dispatches or pulls cache enveopes to pain layout widgets

        Checks first if the entry is resident in cache memory. On failure, spins off
        a `_WaveformLoadTask` on a worker thread to keep the main event loop interactive.

        Args:
            path (Path): Target file location on the local file system
            token (int): Identity tracking metric assigned to the loading execution thread
        """
        cached = get_cached_waveform_envelope(path)
        if cached is not None:
            logger.debug(
                "AudioPlayerWidget.waveform_cache_hit | token=%s | path=%s",
                token,
                path,
            )
            self._apply_waveform_result(
                str(path),
                token,
                cached,
                True,
                0.0,
                0.0,
            )
            return

        logger.debug(
            "AudioPlayerWidget.waveform_cache_miss | token=%s | path=%s",
            token,
            path,
        )
        self._waveform.set_loading("Loading waveform...")
        task = _WaveformLoadTask(path, token, target_bins=512)
        task.signals.finished.connect(self._apply_waveform_result)
        self._active_waveform_task = task
        self._waveform_pool.start(task)

    def _apply_waveform_result(
        self,
        file_path: str,
        token: int,
        envelope,
        cache_hit: bool,
        decode_ms: float,
        elapsed_ms: float,
    ) -> None:
        """Slot invoked on the Main Thread when waveform calculation completes.

        Validates tokens to ensure data alignment, and paints the final envelope
        into the custom WaveformWidget graph if valid.

        Note:
            Executed safely on the Main (GUI) Thread via PySide Signal connection.
        """
        if token != self._load_token or file_path != self._current_file_path:
            return

        if cache_hit:
            logger.debug(
                "AudioPlayerWidget.waveform_cache_apply | token=%s | path=%s",
                token,
                file_path,
            )
        else:
            logger.debug(
                "AudioPlayerWidget.waveform_decoded | token=%s | path=%s | decode_ms=%.1f | total_ms=%.1f",
                token,
                file_path,
                decode_ms,
                elapsed_ms,
            )

        if getattr(envelope, "size", 0) > 0:
            self._waveform.set_waveform(envelope)
            self._waveform.set_progress(0.0)
        else:
            self._waveform.set_message("Waveform unavailable")

        self._active_waveform_task = None

    @staticmethod
    def fmt(ms: int) -> str:
        """
        Formats raw millisecond periods into conventional human-readable intervals.

        Args:
            ms (int): Duration span measured in miliseconds

        Returns:
            str: Time formatted as 'MM:SS'
        """
        s = ms // 1000
        return f"{s // 60:02d}:{s % 60:02d}"
