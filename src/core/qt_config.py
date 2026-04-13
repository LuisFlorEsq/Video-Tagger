import os
import sys
import logging
from PySide6.QtCore import qInstallMessageHandler, QtMsgType


def suppress_qt_warnings():
    """Suppress Qt multimedia and style warnings."""
    
    # Suppress Qt multimedia FFmpeg warnings via environment variable
    os.environ['QT_LOGGING_RULES'] = (
        'qt.multimedia.ffmpeg*=false;'
        'qt.qpa.fonts=false;'
        'qt.pointer.dispatch=false;'
        'ffmpeg*=false'
    )
    
    # Suppress Python logging from Qt
    logging.getLogger('qt').setLevel(logging.ERROR)
    logging.getLogger('qt.multimedia').setLevel(logging.ERROR)


def install_qt_message_handler(verbose: bool = False):
    """
    Install custom Qt message handler to filter warnings.
    
    Args:
        verbose: If True, show all messages. If False, filter common warnings.
    """
    
    # Messages to suppress (common, non-critical warnings)
    SUPPRESSED_MESSAGES = [
        'AVStream duration',
        'is invalid',
        'Taking it from the metadata',
        'Unknown property cursor',
        'QFont',
        'font',
        'timescale not set',
        'Could not find codec parameters',
        'analyzeduration',
        'probesize',
    ]
    
    def message_handler(msg_type: QtMsgType, context, message: str):
        """Custom message handler to filter Qt warnings."""
        
        # Skip if verbose mode is off and message should be suppressed
        if not verbose:
            for suppressed in SUPPRESSED_MESSAGES:
                if suppressed.lower() in message.lower():
                    return
        
        # Print important messages
        if msg_type == QtMsgType.QtDebugMsg:
            if verbose:
                print(f"[Qt Debug] {message}")
        elif msg_type == QtMsgType.QtInfoMsg:
            if verbose:
                print(f"[Qt Info] {message}")
        elif msg_type == QtMsgType.QtWarningMsg:
            # Only show warnings in verbose mode or if not suppressed
            if verbose:
                print(f"[Qt Warning] {message}")
        elif msg_type == QtMsgType.QtCriticalMsg:
            print(f"[Qt Critical] {message}", file=sys.stderr)
        elif msg_type == QtMsgType.QtFatalMsg:
            print(f"[Qt Fatal] {message}", file=sys.stderr)
    
    qInstallMessageHandler(message_handler)


def configure_qt_application(verbose: bool = False):
    """
    Configure Qt application settings.
    
    Args:
        verbose: If True, show all Qt messages. If False, suppress common warnings.
    """
    
    # Suppress warnings via environment
    suppress_qt_warnings()
    
    # Install custom message handler
    install_qt_message_handler(verbose=verbose)
    
    # Additional Qt settings
    os.environ.setdefault('QT_AUTO_SCREEN_SCALE_FACTOR', '1')
    
    # Disable Qt's default warning output on Windows
    if sys.platform == 'win32':
        os.environ['QT_ENABLE_REGEXP_JIT'] = '0'


def setup_quiet_mode():
    """Quick setup for quiet mode (no warnings)."""
    configure_qt_application(verbose=False)


def setup_verbose_mode():
    """Quick setup for verbose mode (all messages)."""
    configure_qt_application(verbose=True)


def setup_debug_mode():
    """Setup for debugging (show everything)."""
    configure_qt_application(verbose=True)
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )