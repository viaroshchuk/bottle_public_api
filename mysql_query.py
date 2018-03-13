# TODO: Add sql injection check
import pymysql.cursors
import config
import logging


def exec_sql(sql_query):
    logging.info("SQL query: {}".format(sql_query))
    connection = pymysql.connect(
        host=config.db_host,
        user=config.db_user,
        password=config.db_pass,
        db=config.db_name,
        charset=config.db_charset,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )
    with connection.cursor() as cursor:
        try:
            return cursor.execute(sql_query), cursor.fetchall()
        except:
            logging.error("Error while executing query: {}".format(sql_query))
            return None
        finally:
            connection.close()
