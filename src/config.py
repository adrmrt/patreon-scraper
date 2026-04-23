import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Config:
    """
    A configuration class for managing environment variables and validating file paths.

    This class loads essential configurations from a `.env` file and provides a method
    to validate critical settings such as email, password, and paths for Firefox and
    GeckoDriver binaries. It ensures that all required variables are set and the specified
    paths exist in the file system.
    """
    EMAIL: str = os.getenv("EMAIL")
    PASSWORD: str = os.getenv("PASSWORD")
    FIREFOX_PATH: Path = Path(os.getenv("FIREFOX_PATH", ""))
    GECKO_DRIVER_PATH: Path = Path(os.getenv("GECKO_PATH", ""))
    ARTIST_FILE_PATH: Path = Path(
        os.getenv("ARTIST_FILE_PATH", PROJECT_ROOT / "artists.json")
    )
    EXAMPLE_FILE_PATH: Path = PROJECT_ROOT / "artists.example.json"
    OUTPUT_FOLDER: Path = Path(os.getenv("OUTPUT_FOLDER", PROJECT_ROOT / "output"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

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
        """
         Validate essential environment variables.
        """
        if not Config.EMAIL or not Config.PASSWORD:
            raise ValueError("Both EMAIL and PASSWORD must be set in the .env file.")

    @staticmethod
    def _validate_paths():
        """
        Validate file paths and ensure they exist.
        """
        if not Config.FIREFOX_PATH.exists():
            raise FileNotFoundError(f"FIREFOX_PATH does not exist: {Config.FIREFOX_PATH}")

        if not Config.GECKO_DRIVER_PATH.exists():
            raise FileNotFoundError(f"GECKO_DRIVER_PATH does not exist: {Config.GECKO_DRIVER_PATH}")

        if not Config.EXAMPLE_FILE_PATH.exists():
            raise FileNotFoundError(f"EXAMPLE_FILE_PATH does not exist: {Config.EXAMPLE_FILE_PATH}")

    @staticmethod
    def ensure_artists_file():
        """
        Ensure `artists.json` exists. If not, create it by copying `artists-example.json`.
        """
        if not Config.ARTIST_FILE_PATH.exists():
            data = Config.EXAMPLE_FILE_PATH.read_text(encoding="utf-8")
            Config.ARTIST_FILE_PATH.write_text(data, encoding="utf-8")
            print(f"{Config.ARTIST_FILE_PATH} was not found.")
            print(
                f"A copy of {Config.EXAMPLE_FILE_PATH} has been created as "
                f"{Config.ARTIST_FILE_PATH}.")
            print(f"Please update {Config.ARTIST_FILE_PATH} with your artist information.")

    @staticmethod
    def ensure_output_folder():
        """
        Ensure the output folder exists.
        """
        Config.OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
