import os
from dotenv import load_dotenv

load_dotenv()

db_config = {
    'host': os.getenv('POSTGRES_HOST'),
    'user': os.getenv('POSTGRES_USER'),
    'port': os.getenv('POSTGRES_PORT'),
    'password': os.getenv('POSTGRES_PASSWORD')
            }
