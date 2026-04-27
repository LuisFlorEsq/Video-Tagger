import logging
import sys


def setup_logger(name: str = "labeling_app"):
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Log en consola (útil para desarrollo)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # # Log en archivo (persistente)
        # log_dir = Path("logs")
        # log_dir.mkdir(exist_ok=True)
        # file_handler = logging.FileHandler(log_dir / "app.log", encoding='utf-8')
        # file_handler.setFormatter(formatter)
        # logger.addHandler(file_handler)

    return logger


# Instancia global para importar fácilmente
logger = setup_logger()
