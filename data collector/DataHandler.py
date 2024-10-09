import smtplib, ssl, os, sqlite3


class Log:

    def __init__(self, step=0, is_success=True, last_log=""):
        self.step = step
        self.is_success = is_success
        self.last_log = last_log

    def reset_log(self, step):
        self.step = step
        self.is_success = True
        self.last_log = ""


class DatabaseHandler:

    def __init__(self, another_mail=None):

        self.another_mail = another_mail
        self._query_create_table_reg = """
                CREATE TABLE IF NOT EXISTS "DataRegression" (
                	"id"	INTEGER NOT NULL UNIQUE,
                	"past_power"	FLOAT NOT NULL,
                	"cur_power"	FLOAT NOT NULL,
                	"prop_power"	FLOAT NOT NULL,
                	"prop_ratio"	FLOAT NOT NULL,
                	"actual_ratio"	FLOAT NOT NULL,
                	"val_ratio"	FLOAT NOT NULL,
                	"val_difference"	FLOAT NOT NULL,
                	PRIMARY KEY("id" AUTOINCREMENT)
        );"""

        self._query_create_table_log = """
        CREATE TABLE IF NOT EXISTS "DataSteps" (
        	"id"	INTEGER NOT NULL UNIQUE,
        	"step"	INTEGER NOT NULL,
        	"is_success"	BOOLEAN,
        	"last_log" TEXT,
        	PRIMARY KEY("id" AUTOINCREMENT)
        );"""

        self._get_last_query = """SELECT * FROM "DataSteps" ORDER BY id DESC LIMIT 1;"""

        self._save_query_log = """
        INSERT INTO "DataSteps" (step, is_success, last_log) VALUES (?, ?, ?)
        """
        self._save_query_reg = """
        INSERT INTO "DataRegression" (past_power, cur_power, prop_power, prop_ratio, actual_ratio, val_ratio, val_difference) VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        self.log = Log()

        self.email_subject = "error at data collector"
        self.email_body = ""

        appdata_path = os.getenv('APPDATA')

        if appdata_path is None:
            appdata_path = os.getenv('LOCALAPPDATA')

        # create path for db
        db_path = os.path.join(appdata_path, 'saver', 'gains.db')

        # create db directory
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # connect database
        self._conn = sqlite3.connect(db_path)
        self._cursor = self._conn.cursor()

        self._cursor.execute(self._query_create_table_log)
        self._cursor.execute(self._query_create_table_reg)

        # create table if not exist
        self._conn.commit()

    def shape_log_text(self, last_log):
        self.log.last_log = last_log

    def shape_log_step(self, step):
        self.log.step = step

    def shape_log_success(self, is_success):
        self.log.is_success = is_success

    def save_regs_to_db(self, past_power, cur_power, prop_power, prop_ratio, actual_ratio, val_ratio, val_difference):
        print("saving")

        self._cursor.execute(self._save_query_reg, (float(past_power), float(cur_power), float(prop_power),
                                                    float(prop_ratio), float(actual_ratio), float(val_ratio),
                                                    float(val_difference)))
        # save data to database
        self._conn.commit()

    def save_log_to_db(self):

        if not self.log.last_log:
            message = "An error occured i stopped"
        else:
            message = self.log.last_log

        if not self.log.is_success:
            self.email_body = "error at" + message

            self.send_email("sadikemreduzgun@gmail.com")
            if self.another_mail:
                self.send_email(self.another_mail)
                self.send_email("mbalci@blc-css.com")

        self._cursor.execute(self._save_query_log, (self.log.step, self.log.is_success, self.log.last_log))
        # save data to database
        self._conn.commit()
        self.log.reset_log(self.log.step)

    def get_last_data(self):
        self._cursor.execute(self._get_last_query)
        return self._cursor.fetchone()

    def send_email(self, to_email, email_text=None):
        try:
            self._email_configure("sed3718@gmail.com", to_email, email_text)
        except:
            pass

    def _email_configure(self, sender_email, receiver_email, email_text=None):

        smtp_server = "smtp.gmail.com"
        port = 587  # For starttls

        password = "wdhv fagw pyuv nxjc"
        # Create a secure SSL context
        context = ssl.create_default_context()

        if email_text:
            email = email_text

        else:
            email = self.email_body

        message = f"""\
Subject: Error at data collector
        
{email}
"""

        # Try to log in to server and send email
        try:
            server = smtplib.SMTP(smtp_server, port)
            server.ehlo()  # Can be omitted
            server.starttls(context=context)  # Secure the connection
            server.ehlo()  # Can be omitted
            server.login(sender_email, password)
            # TODO: Send email here
            server.sendmail(sender_email, receiver_email, message)
            server.quit()
            print("Email sent!")

        except Exception as e:
            # Print any error messages to stdout
            print(e)
