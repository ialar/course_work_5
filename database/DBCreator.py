from src.config import db_config
from src.utils import get_emp_data, get_vac_data, join_data, create_db, fill_db

# Выбранные работодатели
EMPLOYER_IDS = \
    {
        'getmatch': 864086,
        'Quiet Media': 4422327,
        'Carbon Soft': 1204987,
        'NodaSoft': 561525,
        'Midhard games': 1225626,
        'InfiNet Wireless': 810277,
        'modesco': 1185071,
        'CarX Technologies': 1630641,
        'Проммайнер': 9006938,
        'Decart IT-production': 1918903,
    }


def run_db_creation() -> None:
    """Создает БД и заполняет ее собранными с HeadHunter данными."""
    emp_data = get_emp_data(EMPLOYER_IDS)
    vac_data = get_vac_data(EMPLOYER_IDS)
    data = join_data(emp_data, vac_data)

    database_name = 'head_hunter'
    create_db(database_name, db_config)
    fill_db(data, database_name, db_config)
