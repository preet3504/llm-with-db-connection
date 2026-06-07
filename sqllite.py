import sqlite3

sqlite_file = 'user.db'
conn = sqlite3.connect(sqlite_file)
c = conn.cursor()

print("Database created and Successfully Connected to SQLite")

c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)''')

print("Table created successfully")


c.execute("INSERT INTO users (name, age) VALUES ('Alice', 30)")
c.execute("INSERT INTO users (name, age) VALUES ('Bob', 25)")

print("Data inserted successfully")

data = c.execute("SELECT * FROM users")

print("Data retrieved successfully")

for row in data:
    print(row)


conn.commit()
conn.close()