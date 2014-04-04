research
========

NYU Research



##[mysqlconn.py contents]
import MySQLdb

hostname = ""
username = ""
password = ""
database = ""

try:
    conn = MySQLdb.connect(hostname, username, password, database)
    cursor = conn.cursor()

except MySQLdb.Error, e:
    sys.exit(1)