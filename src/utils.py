from typing import Any

import psycopg2
import requests

from database.DBManager import DBManager


def get_emp_data(emp_ids: dict[str, int]) -> list[dict[str, Any]]:
    """
    Возвращает данные по работодателям через HeadHunter API.
    :param emp_ids: Словарь с идентификаторами выбранных компаний.
    :return: Список с данными по компаниям.
    """
    url = 'https://api.hh.ru/employers/'
    emp_data = []

    for emp_id in emp_ids.values():
        response = requests.get(url + str(emp_id)).json()
        emp_data.append(response)
    return emp_data


def get_vac_data(emp_ids: dict[str, int]) -> list[list[dict[str, Any]]]:
    """
    Возвращает данные по вакансиям работодателей через HeadHunter API.
    :param emp_ids: Словарь с идентификаторами выбранных компаний.
    :return: Список с данными по вакансиям компаний.
    """
    url = 'https://api.hh.ru/vacancies'
    params = {'archived': False, 'only_with_salary': True}
    vac_data = []

    for emp_id in emp_ids.values():
        response = requests.get(f'{url}?employer_id={emp_id}', params=params).json()
        vac_data.append(response['items'])
    return vac_data


def join_data(emp_data, vac_data) -> list[tuple[dict[str, Any], list[dict[str, Any]]]]:
    """
    Объединяет полученные данные и возвращает общий список кортежей.
    :param emp_data: Список с данными по компаниям.
    :param vac_data: Список с данными по вакансиям компаний.
    :return: Общий список с данными по компаниям и их вакансиям.
    """
    data = list(zip(emp_data, vac_data))
    return data


def create_db(db_name: str, db_config: dict) -> None:
    """
    Создает базу данных и таблицы для сохранения полученных данных.
    :param db_name: Название создаваемой базы данных.
    :param db_config: Параметры подключения к базе данных.
    """
    conn = psycopg2.connect(**db_config)
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute(f'DROP DATABASE IF EXISTS {db_name}')
    cur.execute(f'CREATE DATABASE {db_name}')
    cur.close()
    conn.close()

    with psycopg2.connect(dbname=db_name, **db_config) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                    CREATE TABLE employers (
                    employer_id SERIAL PRIMARY KEY,
                    company_name VARCHAR NOT NULL,
                    description VARCHAR,
                    city VARCHAR,
                    employer_url TEXT)
                        """)
        with conn.cursor() as cur:
            cur.execute("""
                    CREATE TABLE vacancies (
                    vacancy_id SERIAL PRIMARY KEY,
                    employer_id INTEGER REFERENCES employers(employer_id),
                    title VARCHAR NOT NULL,
                    company_name VARCHAR NOT NULL,
                    salary_from INTEGER,
                    salary_to INTEGER,
                    currency VARCHAR(5),
                    vacancy_url TEXT)
                        """)
    conn.close()


def fill_db(data: list, db_name: str, db_config: dict) -> None:
    """
    Заполняет базу данных собранными данными.
    :param data: Объединенные данные по компаниям и их вакансиям.
    :param db_name: Название созданной базы данных.
    :param db_config: Параметры подключения к базе данных.
    """
    conn = psycopg2.connect(dbname=db_name, **db_config)

    with conn.cursor() as cur:
        for employer in data:
            employer_data = employer[0]
            cur.execute(
                """
                INSERT INTO employers(company_name, description, city, employer_url)
                VALUES (%s, %s, %s, %s)
                RETURNING employer_id
                """,
                (employer_data['name'], employer_data['description'],
                 employer_data['area']['name'], employer_data['alternate_url'])
            )
            employer_id = cur.fetchone()[0]

            vacancies_data = employer[1]
            for vacancy in vacancies_data:
                vacancy_data = vacancy
                cur.execute(
                    """
                    INSERT INTO vacancies 
                    (employer_id, title, company_name, salary_from, salary_to, currency, vacancy_url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (employer_id, vacancy_data['name'], vacancy_data['employer']['name'],
                     vacancy_data['salary']['from'] if vacancy_data['salary']['from'] is not None else
                     vacancy_data['salary']['to'],
                     vacancy_data['salary']['to'] if vacancy_data['salary']['to'] is not None else
                     vacancy_data['salary']['from'],
                     vacancy_data['salary']['currency'], vacancy_data['alternate_url'])
                )
    conn.commit()
    conn.close()


def run_user_commands() -> None:
    """Запускает цикл выбора команд для пользователя."""
    db_manager = DBManager()

    while True:
        print('\n1. Вывести список компаний и количество вакансий у каждой компании'
              '\n2. Вывести список всех вакансий компаний'
              '\n3. Вывести среднюю зарплату по вакансиям'
              '\n4. Вывести список всех вакансий, у которых зарплата выше средней по всем вакансиям'
              '\n5. Вывести список всех вакансий по ключевому слову'
              '\n6. Выйти')
        choice_menu = input('Выберите действие: ')
        if choice_menu == '1':
            data = db_manager.get_companies_and_vacancies_count()
            for i in data:
                print(f'Компания {i[0]}, открытых вакансий - {i[1]}')
        elif choice_menu == '2':
            data = db_manager.get_all_vacancies()
            for i in data:
                print(f'Компания "{i[0]}", вакансия - {i[1]}, з/пл - от {i[2]} до {i[3]}, ссылка - {i[4]}')
        elif choice_menu == '3':
            print(f'{db_manager.get_avg_salary()} руб.')
        elif choice_menu == '4':
            data = db_manager.get_vacancies_with_higher_salary()
            for i in data:
                print(f'Компания "{i[0]}", вакансия - {i[1]}, з/пл - от {i[2]}, ссылка - {i[3]}')
        elif choice_menu == '5':
            vacancy_keyword = input('Введите ключевое слово ')  # Переменная для выбора ключевого слова
            data = db_manager.get_vacancies_with_keyword(vacancy_keyword)
            if not data:
                print('По данному ключевому слову вакансий не обнаружено')
            else:
                for i in data:
                    print(f'Компания "{i[0]}", вакансия - {i[1]}, з/пл - от {i[2]} до {i[3]}, ссылка - {i[4]}')
        elif choice_menu == '6':
            break
        else:
            print('Ошибка ввода')
