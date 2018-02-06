import sqlite3


def find_sql_matches():
    db = sqlite3.connect('Kinepolis.db')
    cursor = db.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for table_name in tables:
        table_name = table_name[0]
        cursor = db.execute("SELECT * from %s" % table_name)
        i=0
        for row in cursor.fetchall():
            i+=1
            if "KINE_CHANGE_EMAIL_URL" in str(row):
                print("Table: " + table_name)
                print("line: " + str(i))
                print(row[0] + " : " + row[1])

find_sql_matches()