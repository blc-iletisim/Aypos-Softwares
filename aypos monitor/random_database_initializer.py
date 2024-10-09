import psycopg2
import random
from faker import Faker

# Initialize Faker for generating random data
fake = Faker()

# PostgreSQL database connection details
DB_HOST = 'localhost'
DB_NAME = 'your_db_name'
DB_USER = 'your_username'
DB_PASSWORD = 'your_password'

# Connect to PostgreSQL
def connect_to_db():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn

# Create random tables with random columns and rows
def create_random_tables(conn):
    cursor = conn.cursor()

    # Generate a random number of tables (between 10 to 15)
    num_tables = random.randint(10, 15)

    for t in range(num_tables):
        table_name = f"table_{t+1}"

        # Generate random number of columns (between 5 to 20)
        num_columns = random.randint(5, 20)

        # Create column definitions
        columns = [f"col_{i+1} {random.choice(['INTEGER', 'FLOAT'])}" for i in range(num_columns)]
        columns_str = ', '.join(columns)

        # Create the table
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (id SERIAL PRIMARY KEY, {columns_str});")
        print(f"Table {table_name} created with {num_columns} columns.")

        # Generate random number of rows (between 20 to 40)
        num_rows = random.randint(20, 40)

        # Insert random data into the table
        for _ in range(num_rows):
            values = [str(random.randint(1, 1000)) if 'INTEGER' in col else str(random.uniform(1.0, 1000.0))
                      for col in columns]
            values_str = ', '.join(values)
            cursor.execute(f"INSERT INTO {table_name} ({', '.join([f'col_{i+1}' for i in range(num_columns)])}) "
                           f"VALUES ({values_str});")

        # Add random foreign key relations (random number from 1 to 5)
        num_relations = random.randint(1, 5)
        add_relations(cursor, table_name, num_relations)

        conn.commit()

def add_relations(cursor, table_name, num_relations):
    for _ in range(num_relations):
        related_table = f"table_{random.randint(1, 15)}"
        if table_name != related_table:
            # Add a relation (foreign key) between two tables
            fk_col = random.choice([f"col_{i+1}" for i in range(5, 20)])  # Select random column
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {fk_col}_fk INTEGER REFERENCES {related_table}(id);")
            print(f"Added relation: {table_name}.{fk_col}_fk -> {related_table}.id")

def main():
    try:
        conn = connect_to_db()
        print("Connected to the database!")
        create_random_tables(conn)
        print("Random database initialization complete!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
