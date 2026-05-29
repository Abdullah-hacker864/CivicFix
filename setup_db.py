import sqlite3

connection = sqlite3.connect('civicfix.db')
cursor = connection.cursor()

cursor.execute('DROP TABLE IF EXISTS Reports')
cursor.execute('''
    CREATE TABLE Reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_comment TEXT,
        user_image TEXT,       
        lat REAL,
        lon REAL,
        status TEXT,           
        assigned_worker TEXT,
        worker_comment TEXT,   
        worker_image TEXT,     
        admin_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

cursor.execute('DROP TABLE IF EXISTS Users')
cursor.execute('''
    CREATE TABLE Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
''')

# Seed Default Login Credentials
cursor.execute("INSERT INTO Users (username, password, role) VALUES ('admin', 'admin123', 'admin')")
cursor.execute("INSERT INTO Users (username, password, role) VALUES ('Worker1', 'pass1', 'worker')")
cursor.execute("INSERT INTO Users (username, password, role) VALUES ('Worker2', 'pass2', 'worker')")
cursor.execute("INSERT INTO Users (username, password, role) VALUES ('Worker3', 'pass3', 'worker')")

connection.commit()
connection.close()
print("Database upgraded with Users table and default credentials!")