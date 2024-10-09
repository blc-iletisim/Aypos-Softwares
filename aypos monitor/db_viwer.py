from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QPushButton
from sqlalchemy import create_engine, MetaData
from sqlalchemy.engine import reflection


class DatabaseSchemaApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Set the main window properties
        self.setWindowTitle('Database Schema Viewer')
        self.setGeometry(100, 100, 800, 600)

        # Create a text edit to display the schema
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)  # Set as read-only

        # Create a button to trigger the schema retrieval
        self.button = QPushButton('Load Database Schema', self)
        self.button.clicked.connect(self.load_schema)

        # Layout to arrange widgets vertically
        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        layout.addWidget(self.button)

        # Create a central widget and set the layout
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def load_schema(self):
        # Replace with your own database URL
        db_url = "sqlite:///your_database.db"  # Example for SQLite
        engine, connection = self.connect_to_database(db_url)

        # Retrieve schema and update the text area
        schema_text = self.get_database_schema(engine)
        self.text_edit.setPlainText(schema_text)

        # Close the database connection
        connection.close()

    def connect_to_database(self, db_url):
        """Establishes a connection to the database."""
        engine = create_engine(db_url)
        connection = engine.connect()
        return engine, connection

    def get_database_schema(self, engine):
        """Retrieve all tables and their relationships and format them."""
        metadata = MetaData(bind=engine)
        tables = self.get_database_tables(engine)

        schema_output = []
        schema_output.append(f"Tables in the database:\n")
        for table in tables:
            schema_output.append(f"- {table}")
            foreign_keys = self.get_table_relations(engine, table)
            if foreign_keys:
                schema_output.append(f"  Foreign keys in {table}:")
                for fk in foreign_keys:
                    schema_output.append(
                        f"    {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
            schema_output.append("\n")

        return "\n".join(schema_output)

    def get_database_tables(self, engine):
        """Retrieves all table names from the database."""
        inspector = reflection.Inspector.from_engine(engine)
        return inspector.get_table_names()

    def get_table_relations(self, engine, table):
        """Retrieves the foreign key relationships for a specific table."""
        inspector = reflection.Inspector.from_engine(engine)
        return inspector.get_foreign_keys(table)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = DatabaseSchemaApp()
    window.show()
    sys.exit(app.exec_())
