from mysql.connector import (connection)

cnx = connection.MySQLConnection(user='radio', password='xxxx',
                                 host='127.0.0.1',
                                 database='radio')
cnx.close()