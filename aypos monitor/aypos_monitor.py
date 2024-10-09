import sys
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
                             QLabel, QLineEdit, QFormLayout, QStackedWidget, QHBoxLayout, QTableWidget, QTableWidgetItem)
from PyQt5.QtCore import QTimer
import subprocess
import seaborn as sns
#import migrate  # Import migrate module
import asyncio
# from .environmental_temperature1.environmental_temperature_15min import *
import threading
from migration_advices.migrate_it import *
from environmental_temperature.environmental_temperature_15min import main_e
from migration_advices.migration_advices import main_m
from preventive_maintenance.preventive_maintenance_15min import main_p
from environmental_temperature.ac_sender import main_ac_sender


class Application(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aypos Monitor")
        self.setGeometry(100, 100, 800, 600)

        # File paths for all features
        self.env_temp_file_path = 'C:\\Users\\B_L_C\\Desktop\\aypos_monitor\\environmental_temperature\\current_output.csv'
        self.preventive_file_path = 'C:\\Users\\B_L_C\\Desktop\\aypos_monitor\\preventive_maintenance\\current_output.csv'
        self.migration_advice_file_path = 'C:\\Users\\B_L_C\\Desktop\\aypos_monitor\\migration_advices\\migration_advices.csv'
        self.gain_output_file_path = 'C:\\Users\\B_L_C\\Desktop\\aypos_monitor\\migration_advices\\gain_output.csv'

        # Initialize lists and flags
        self.x, self.y = [], []
        self.x_preventive, self.y_preventive = [], []
        self.flag = None
        self.flag_preventive = None

        # To store the Popen processes for killing them later
        self.env_temp_process = None
        self.preventive_process = None
        self.migration_process = None

        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout(self.central_widget)

        # Sidebar for navigation
        self.sidebar = QWidget()
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.layout.addWidget(self.sidebar)

        # Navigation buttons
        self.home_button = QPushButton("Home")
        self.home_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        self.sidebar_layout.addWidget(self.home_button)

        self.env_temp_button = QPushButton("Environmental Temperature")
        self.env_temp_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        self.sidebar_layout.addWidget(self.env_temp_button)

        self.preventive_button = QPushButton("Preventive Maintenance")
        self.preventive_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        self.sidebar_layout.addWidget(self.preventive_button)

        self.migration_button = QPushButton("Migration Advice")
        self.migration_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))
        self.sidebar_layout.addWidget(self.migration_button)

        # Stacked widget for tab content
        self.stacked_widget = QStackedWidget()
        self.layout.addWidget(self.stacked_widget)

        # Create tabs
        self.home_tab = QWidget()
        self.env_temp_tab = QWidget()
        self.preventive_tab = QWidget()
        self.migration_tab = QWidget()

        self.stacked_widget.addWidget(self.home_tab)
        self.stacked_widget.addWidget(self.env_temp_tab)
        self.stacked_widget.addWidget(self.preventive_tab)
        self.stacked_widget.addWidget(self.migration_tab)

        # Create content for tabs
        self.create_home_tab()
        self.create_env_temp_tab()
        self.create_preventive_tab()
        self.create_migration_tab()

        # Update the plots periodically
        self.update_plot()
        self.update_preventive_plot()

        self.df = None

    def create_home_tab(self):
        home_layout = QVBoxLayout()
        self.home_tab.setLayout(home_layout)

        form_layout = QFormLayout()

        # Environmental temperature user inputs
        form_layout.addRow(QLabel("Environmental Temperature Section:"), QLabel(""))
        self.time_unit_edit = QLineEdit('1')
        self.steps_edit = QLineEdit('15')
        self.model_type_edit = QLineEdit('lstm')

        form_layout.addRow(QLabel("Script Time Unit:"), self.time_unit_edit)
        form_layout.addRow(QLabel("Number of Steps:"), self.steps_edit)
        form_layout.addRow(QLabel("Model Type:"), self.model_type_edit)

        # Preventive maintenance user inputs
        form_layout.addRow(QLabel("Preventive Maintenance Section:"), QLabel(""))
        self.preventive_time_unit_edit = QLineEdit('1')
        self.preventive_steps_edit = QLineEdit('15')
        self.preventive_model_type_edit = QLineEdit('lstm')

        form_layout.addRow(QLabel("Preventive Script Time Unit:"), self.preventive_time_unit_edit)
        form_layout.addRow(QLabel("Preventive Number of Steps:"), self.preventive_steps_edit)
        form_layout.addRow(QLabel("Preventive Model Type:"), self.preventive_model_type_edit)

        # Migration advice user inputs
        form_layout.addRow(QLabel("Migration Advice Section:"), QLabel(""))
        self.migration_time_unit_edit = QLineEdit('20')
        self.migration_model_type_edit = QLineEdit('xgboost')

        form_layout.addRow(QLabel("Migration Script Time Unit (20-90):"), self.migration_time_unit_edit)
        form_layout.addRow(QLabel("Migration Model Type (xgboost/multi reg):"), self.migration_model_type_edit)

        home_layout.addLayout(form_layout)

        # Start Monitoring button
        start_button = QPushButton("Start Monitoring")
        start_button.clicked.connect(self.start_monitoring)
        home_layout.addWidget(start_button)

        self.stop_button = QPushButton("Stop Monitoring")
        self.stop_button.clicked.connect(self.stop_monitoring)
        self.stop_button.setVisible(False)  # Initially hidden
        home_layout.addWidget(self.stop_button)

    def create_env_temp_tab(self):
        env_temp_layout = QVBoxLayout()
        self.env_temp_tab.setLayout(env_temp_layout)

        self.figure, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvas(self.figure)
        env_temp_layout.addWidget(self.canvas)

        self.flag_label = QLabel("Flag: ")
        env_temp_layout.addWidget(self.flag_label)

        approve_button = QPushButton("Approve Decision")
        approve_button.clicked.connect(self.approve_decision)
        env_temp_layout.addWidget(approve_button)

    def create_preventive_tab(self):
        preventive_layout = QVBoxLayout()
        self.preventive_tab.setLayout(preventive_layout)

        self.figure_preventive, self.ax_preventive = plt.subplots(figsize=(6, 4))
        self.canvas_preventive = FigureCanvas(self.figure_preventive)
        preventive_layout.addWidget(self.canvas_preventive)

        self.flag_label_preventive = QLabel("Flag: ")
        preventive_layout.addWidget(self.flag_label_preventive)

        approve_button_preventive = QPushButton("Approve Preventive Maintenance Decision")
        approve_button_preventive.clicked.connect(self.approve_preventive_decision)
        preventive_layout.addWidget(approve_button_preventive)

    def create_migration_tab(self):
        migration_layout = QVBoxLayout()
        self.migration_tab.setLayout(migration_layout)

        # Create migration advice table widget
        self.migration_advice_table = QTableWidget()
        migration_layout.addWidget(self.migration_advice_table)

        # Create gain output table widget
        self.gain_output_table = QTableWidget()
        migration_layout.addWidget(self.gain_output_table)

        # Approve Migration button
        approve_migration_button = QPushButton("Approve Migration")
        approve_migration_button.clicked.connect(self.approve_migration)
        migration_layout.addWidget(approve_migration_button)

        # Update migration advice and gain output tables periodically
        self.update_migration_advice()
        self.update_gain_output()

    def start_monitoring(self):
        # Environmental temperature monitoring
        env_inputs = {
            'number_of_steps': self.steps_edit.text(),
            'script_time_unit': self.time_unit_edit.text(),
            'model_type': self.model_type_edit.text()
        }

        # asyncio.create_task()
        th_e = threading.Thread(target=main_e, args=(env_inputs,))
        th_e.start()
        """subprocess.Popen([
            'python',
            'C:\\Users\\B_L_C\\Desktop\\aypos_monitor\\environmental_temperature\\environmental_temperature_15min.py',
            json.dumps(env_inputs)
        ])"""

        # Preventive maintenance monitoring
        preventive_inputs = {
            'number_of_steps': self.preventive_steps_edit.text(),
            'script_time_unit': self.preventive_time_unit_edit.text(),
            'model_type': self.preventive_model_type_edit.text()
        }
        th_p = threading.Thread(target=main_p, args=(preventive_inputs,))
        th_p.start()

        """subprocess.Popen([
            'python',
            'C:\\Users\\B_L_C\\Desktop\\aypos_monitor\\preventive_maintenance\\preventive_maintenance_15min.py',
            json.dumps(preventive_inputs)
        ])"""

        # Migration advice monitoring
        migration_inputs = {
            'script_time_unit': self.migration_time_unit_edit.text(),
            'model_type': self.migration_model_type_edit.text()
        }
        """subprocess.Popen([
            'python',
            'C:\\Users\\B_L_C\\Desktop\\aypos_monitor\\migration_advices\\migration_advices.py',
            json.dumps(migration_inputs)
        ])"""
        th_m = threading.Thread(target=main_m, args=(migration_inputs,))
        th_m.start()

        # Show the stop button
        self.stop_button.setVisible(True)

    def stop_monitoring(self):
        # Terminate the processes
        if self.env_temp_process:
            self.env_temp_process.terminate()
        if self.preventive_process:
            self.preventive_process.terminate()
        if self.migration_process:
            self.migration_process.terminate()

        # Hide the stop button again
        self.stop_button.setVisible(False)

    def update_migration_advice(self):
        if os.path.exists(self.migration_advice_file_path):
            df = pd.read_csv(self.migration_advice_file_path)
            self.df = df

            # req_migrate_one_by_one(df)
            df = df.iloc[:, 1:]
            self.migration_advice_table.setRowCount(df.shape[0])
            self.migration_advice_table.setColumnCount(df.shape[1])
            self.migration_advice_table.setHorizontalHeaderLabels(df.columns)

            for i in range(df.shape[0]):
                for j in range(df.shape[1]):
                    self.migration_advice_table.setItem(i, j, QTableWidgetItem(str(df.iat[i, j])))

        QTimer.singleShot(1000, self.update_migration_advice)

    def update_gain_output(self):
        if os.path.exists(self.gain_output_file_path):
            df = pd.read_csv(self.gain_output_file_path)
            df = df.iloc[:, 1:]
            self.gain_output_table.setRowCount(df.shape[0])
            self.gain_output_table.setColumnCount(df.shape[1])
            self.gain_output_table.setHorizontalHeaderLabels(df.columns)

            for i in range(df.shape[0]):
                for j in range(df.shape[1]):
                    self.gain_output_table.setItem(i, j, QTableWidgetItem(str(df.iat[i, j])))

        QTimer.singleShot(1000, self.update_gain_output)

    def approve_migration(self):
        # Call the migrate module's apply_changes function
        #migrate.apply_changes()
        print("Migration changes approved!")
        migrate_th = threading.Thread(target=req_migrate_one_by_one, args=(self.df,))
        migrate_th.start()
        del self.df

    def update_plot(self):
        if os.path.exists(self.env_temp_file_path):
            df = pd.read_csv(self.env_temp_file_path)

            if 'env_temp_cur' in df.columns and 'now_timestamp' in df.columns and 'flag' in df.columns:
                self.x = pd.to_datetime(df['now_timestamp'])
                self.y = df['env_temp_cur']

                x_future = pd.to_datetime(df['future_timestamp'])
                y_future = df['env_temp_15min']

                # Update plot
                self.ax.clear()

                # Use Seaborn to plot
                sns.lineplot(x=self.x, y=self.y, marker='o', linestyle='-', label='Current Temperature', ax=self.ax)
                sns.lineplot(x=x_future, y=y_future, marker='x', linestyle='--', label='Future Temperature', ax=self.ax)

                self.ax.set_xlabel('Timestamp')
                self.ax.set_ylabel('Temperature')
                self.ax.set_title('Environmental Temperature Over Time')
                self.ax.legend()
                # self.ax.set_ylim(0, None)  # Y-axis starts at 0

                self.canvas.draw()

                # Update flag label
                self.flag = df['flag'].iloc[-1]
                self.flag_label.setText(f"Flag: {self.flag}")

        QTimer.singleShot(1000, self.update_plot)  # Update every second

    def approve_decision(self):
        if self.flag is not None:
            df = pd.DataFrame({'flag': [self.flag['temp']]})
            target_celsius = self.flag['temp']
            main_ac_sender(target_celsius)

            df.to_csv('ac_command.csv', index=False)
            print("Approved Decision saved to ac_command.csv")

    def update_preventive_plot(self):
        if os.path.exists(self.preventive_file_path):
            df = pd.read_csv(self.preventive_file_path)

            # Ensure the required columns are in the DataFrame
            if 'now_timestamp' in df.columns and 'power' in df.columns and 'future_timestamp' in df.columns:
                # Existing values
                self.x_preventive = pd.to_datetime(df['now_timestamp'])
                self.y_preventive = df['power']

                # Future values
                x_future = pd.to_datetime(df['future_timestamp'])
                y_future = df['power_future_15min']
                y_p3 = df['positive_3p']
                y_n3 = df['negative_3p']
                y_p7 = df['positive_7p']
                y_n7 = df['negative_7p']

                # Update the plot
                self.ax_preventive.clear()

                # Plot current power
                sns.lineplot(x=self.x_preventive, y=self.y_preventive, marker='o', linestyle='-', label='Current Power',
                             ax=self.ax_preventive)

                # Plot future power and positive/negative predictions
                sns.lineplot(x=x_future, y=y_future, marker='x', linestyle='--', label='Future Power (15min)',
                             ax=self.ax_preventive)
                sns.lineplot(x=x_future, y=y_p3, marker='^', linestyle='--', label='Positive 3p', ax=self.ax_preventive)
                sns.lineplot(x=x_future, y=y_n3, marker='v', linestyle='--', label='Negative 3p', ax=self.ax_preventive)
                sns.lineplot(x=x_future, y=y_p7, marker='^', linestyle='--', label='Positive 7p', ax=self.ax_preventive)
                sns.lineplot(x=x_future, y=y_n7, marker='v', linestyle='--', label='Negative 7p', ax=self.ax_preventive)

                # Set plot labels and title
                self.ax_preventive.set_xlabel('Timestamp')
                self.ax_preventive.set_ylabel('Power')
                self.ax_preventive.set_title('Preventive Maintenance Power Forecast')

                # Set y-axis to start from 0
                # self.ax_preventive.set_ylim(0, None)

                # Add legend
                self.ax_preventive.legend()

                # Redraw the canvas
                self.canvas_preventive.draw()

                # Update flag label with the latest flag value
                self.flag_preventive = df['flag'].iloc[-1]
                self.flag_label_preventive.setText(f"Flag: {self.flag_preventive}")

        # Schedule the plot to update every second
        QTimer.singleShot(1000, self.update_preventive_plot)

    def approve_preventive_decision(self):
        if self.flag_preventive is not None:
            df = pd.DataFrame({'flag': [self.flag_preventive]})
            df.to_csv('preventive_ac_command.csv', index=False)
            print("Approved Preventive Maintenance Decision saved to preventive_ac_command.csv")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Application()
    window.show()
    sys.exit(app.exec_())
