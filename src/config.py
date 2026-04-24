import logging
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _parse_log_level(value: str) -> int:
    """
    Converts a log level string (e.g. 'DEBUG', 'INFO') to a logging constant.
    Falls back to INFO for unrecognised values.
    """
    numeric = getattr(logging, value.upper(), None)
    if not isinstance(numeric, int):
        print(f"[config] Unknown LOG_LEVEL '{value}', defaulting to INFO.")
        return logging.INFO
    return numeric


class Config:
    """
    A configuration class for managing environment variables and validating file paths.
    """

    EMAIL: str = os.getenv("EMAIL", "")
    PASSWORD: str = os.getenv("PASSWORD", "")
    FIREFOX_PATH: Path = Path(os.getenv("FIREFOX_PATH", ""))
    GECKO_DRIVER_PATH: Path = Path(os.getenv("GECKO_PATH", ""))
    ARTIST_FILE_PATH: Path = Path(
        os.getenv("ARTISTS_FILE_PATH", PROJECT_ROOT / "artists.json")
    )
    EXAMPLE_FILE_PATH: Path = PROJECT_ROOT / "artists.example.json"
    OUTPUT_FOLDER: Path = Path(os.getenv("OUTPUT_FOLDER", PROJECT_ROOT / "output"))
    LOG_LEVEL: int = _parse_log_level(os.getenv("LOG_LEVEL", "INFO"))

    @staticmethod
    def validate():
        """
        Validates the configuration settings and ensures necessary files and folders exist.
        """
        Config._validate_env_vars()
        Config._validate_paths()
        Config.ensure_artists_file()
        Config.ensure_output_folder()

    @staticmethod
    def _validate_env_vars():
        if not Config.EMAIL or not Config.PASSWORD:
            raise ValueError("Both EMAIL and PASSWORD must be set in the .env file.")

    @staticmethod
    def _validate_paths():
        if not Config.FIREFOX_PATH.exists():
            raise FileNotFoundError(
                f"FIREFOX_PATH does not exist: {Config.FIREFOX_PATH}"
            )
        if not Config.GECKO_DRIVER_PATH.exists():
            raise FileNotFoundError(
                f"GECKO_DRIVER_PATH does not exist: {Config.GECKO_DRIVER_PATH}"
            )
        if not Config.EXAMPLE_FILE_PATH.exists():
            raise FileNotFoundError(
                f"EXAMPLE_FILE_PATH does not exist: {Config.EXAMPLE_FILE_PATH}"
            )

    @staticmethod
    def ensure_artists_file():
        """
        Ensures artists.json exists. If not, creates it from artists.example.json.
        """
        from src.logger import get_logger

        logger = get_logger(__name__)

        if not Config.ARTIST_FILE_PATH.exists():
            data = Config.EXAMPLE_FILE_PATH.read_text(encoding="utf-8")
            Config.ARTIST_FILE_PATH.write_text(data, encoding="utf-8")
            logger.warning(
                "%s not found. Created a copy from %s — please update it with your artist information.",
                Config.ARTIST_FILE_PATH,
                Config.EXAMPLE_FILE_PATH,
            )

    @staticmethod
    def ensure_output_folder():
        Config.OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
