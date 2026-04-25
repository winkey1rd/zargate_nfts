import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

GETGEMS_API_BASE_URL = "https://api.getgems.io/public-api"
GETGEMS_API_KEY = os.getenv("GETGEMS_API_KEY")
