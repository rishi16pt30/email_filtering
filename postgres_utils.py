import psycopg2
from psycopg2.extras import RealDictCursor
from jinja2 import Template


class PostgresDB:
    def __init__(self, host, database, user, password, port=5432):
        self.connection = None
        try:
            self.connection = psycopg2.connect(
                host=host,
                database=database,
                user=user,
                password=password,
                port=port
            )
            self.connection.autocommit = True
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            print("Connected to PostgreSQL")
        except psycopg2.Error as e:
            print(f"Error connecting to PostgreSQL: {e}")

    def execute_query(self, query, params=None):
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except psycopg2.Error as e:
            print(f"Query error: {e}")
            return None

    def execute_non_query(self, query, params=None):
        try:
            self.cursor.execute(query, params)
        except psycopg2.Error as e:
            print(f"Execution error: {e}")

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            print("🔒 PostgreSQL connection closed")

    
    def create_table(self, table_name, db_schema):
        try:
            columns_template = Template("""
                CREATE TABLE IF NOT EXISTS {{ table_name }} (
                    {% for key, value in columns.items() -%}
                        {{ key }} {{ value }}{% if not loop.last %},{% endif %}
                    {% endfor %}
                );
                """)
            create_table_sql_query = columns_template.render(table_name=table_name, columns=db_schema)
            # print(f"Creating table query :  {create_table_sql_query}")
            
            self.execute_non_query(query= create_table_sql_query)
            print(f"Successfully Executed and created table :  {table_name}")
        
        except Exception as e:
            print(e)
            
    
    def insert_data(self, table_name, data):
        
        insert_template = Template("""
            INSERT INTO {{ table_name }} ({{ keys|join(', ') }})
            VALUES ({{ values|join(', ') }})
            ON CONFLICT (unique_mail_id) DO NOTHING;
            """)

        keys = list(data.keys())
        values = [f"%({k})s" for k in keys]  # for psycopg2 param style

        insert_sql_query = insert_template.render(
            table_name=table_name,
            keys=keys,
            values=values
        )
        # print(insert_sql_query)
        self.execute_non_query(query=insert_sql_query, params=data)
    
    def fetch_all_data(self, table_name):
        select_query = f"SELECT * FROM {table_name};"
        return self.execute_query(select_query)

        
    def delete_table(self, table_name):
        delete_query = f"DROP TABLE IF EXISTS {table_name};"
        
        print("delete query ", delete_query)
        self.execute_non_query(delete_query)