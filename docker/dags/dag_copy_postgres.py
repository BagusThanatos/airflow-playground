import psycopg2

from airflow.operators.python_operator import PythonOperator
from airflow.models import DAG
from datetime import datetime, timedelta


args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2022, 7, 20, 0, 0),
    'retries': 2,
    'retry_delay': timedelta(seconds=30)
}

dag = DAG(
    dag_id='copy_postgres',
    schedule_interval='15 * * * *', # make it every hour
    max_active_runs=1,
    default_args=args
)

def run_copy_postgres(**kwargs):
    # This credential is better put in env variables, or other mechanisms
    connection_string_one = 'postgresql://one:one@postgres_one/one'
    select_query_one = 'select * from foo'
    connection_string_two = 'postgresql://two:two@postgres_two/two'
    with psycopg2.connect(connection_string_one) as conn, conn.cursor() as cursor:
        cursor.execute(select_query_one)
        data = list(cursor.fetchall())
    create_table_query = 'create table if not exists foo(foo1 varchar, foo2 int)'
    insert_query = 'insert into foo(foo1, foo2) values %s'
    with psycopg2.connect(connection_string_two) as conn, conn.cursor() as cursor:
        cursor.execute(create_table_query)
        psycopg2.extras.execute_values(cursor, insert_query, data, template=None, page_size=50)

    print(data)

def init_postgres(**kwargs):
    connection_string = 'postgresql://one:one@postgres_one/one'
    create_table_query = 'create table if not exists foo(foo1 varchar, foo2 int)'
    insert_query = 'insert into foo(foo1, foo2) values(\'value1\', 1)'
    with psycopg2.connect(connection_string) as conn, conn.cursor() as cursor:
        cursor.execute(create_table_query)
        cursor.execute(insert_query)


task_init_postgres = PythonOperator(task_id='task_init_postgres',
                                        python_callable=init_postgres,
                                        dag=dag,
                                        provide_context=True)

task_run_copy_postgres = PythonOperator(task_id='task_run_copy_postgres',
                                        python_callable=run_copy_postgres,
                                        dag=dag,
                                        provide_context=True)


task_init_postgres >> task_run_copy_postgres