import os

DEBUG = os.getenv("DEBUG", False)

if DEBUG:
    print("We are in debug")
    from pathlib import Path
    from dotenv import load_dotenv
    env_path = Path(".") / ".env.debug"
    load_dotenv(dotenv_path=env_path)
    from settings_files.development import *  # noqa: F403
else:
    print("We are in production")
    from dotenv import load_dotenv
    load_dotenv(".env")
    from settings_files.product import *  # noqa: F403