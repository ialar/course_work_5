from database.DBCreator import run_db_creation
from src.utils import run_user_commands


def main():
    run_db_creation()
    run_user_commands()


if __name__ == '__main__':
    main()
