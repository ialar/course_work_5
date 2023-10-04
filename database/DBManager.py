import psycopg2

from src.config import db_config


class DBManager:

    def __init__(self):
        with psycopg2.connect(dbname='head_hunter', **db_config) as conn:
            self.connection = conn
        self.cursor = self.connection.cursor()

    def get_companies_and_vacancies_count(self):
        """Получает список всех компаний и количество вакансий у каждой компании."""
        self.cursor.execute('SELECT company_name, COUNT(*) FROM vacancies GROUP BY company_name')
        companies_list = self.cursor.fetchall()
        return companies_list

    def get_all_vacancies(self):
        """Получает список всех вакансий с указанием названия компании,
        названия вакансии, зарплаты и ссылки на вакансию."""
        self.cursor.execute('SELECT company_name, title, salary_from, salary_to, vacancy_url FROM vacancies')
        vacancies_list = self.cursor.fetchall()
        return vacancies_list

    def get_avg_salary(self):
        """Получает среднюю зарплату по вакансиям (с точностью до сотых)."""
        self.cursor.execute('SELECT ROUND(AVG((salary_from + salary_to)/2), 2) FROM vacancies')
        avg_salary = self.cursor.fetchone()[0]
        return avg_salary

    def get_vacancies_with_higher_salary(self):
        """Получает список всех вакансий, у которых минимальная зарплата вакансии
        выше средней по всем вакансиям (порядок по возрастанию зарплат)."""
        self.cursor.execute('SELECT company_name, title, salary_from, vacancy_url '
                            'FROM vacancies '
                            'WHERE salary_from >= (SELECT ROUND(AVG((salary_from + salary_to)/2)) FROM vacancies) '
                            'ORDER BY salary_from')
        vacancies_higher_salary_list = self.cursor.fetchall()
        return vacancies_higher_salary_list

    def get_vacancies_with_keyword(self, keyword):
        """Получает список всех вакансий,
        в названии которых содержатся переданные в метод слова, например 'Python'."""
        self.cursor.execute(f"SELECT company_name, title, salary_from, salary_to, vacancy_url "
                            f"FROM vacancies "
                            f"WHERE title LIKE '%{keyword}%'")
        vacancies_list_by_keyword = self.cursor.fetchall()
        return vacancies_list_by_keyword
