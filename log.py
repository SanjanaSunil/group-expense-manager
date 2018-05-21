import sqlite3 as sql
import datetime
from flask import session


def log(user, activity):
    if not user:
        user = session['username']

    time = datetime.datetime.now()
    timeFormat = "%c"

    time = time.strftime(timeFormat)
    con = sql.connect("database.db")
    cur = con.cursor()

    activity = time + ": " + activity
    cur.execute("INSERT INTO log (user,log) VALUES (?,?)",
                (user, activity))
    con.commit()
    cur.execute("SELECT lid FROM log WHERE user=='{0}' AND log=='{1}'".format(
        user, activity))
    lid = cur.fetchone()
    con.close()
    return lid


def delLog(lid):
    con = sql.connect("database.db")
    cur = con.cursor()

    cur.execute("DELETE FROM log WHERE lid=={0}".format(lid))

    con.commit()
    con.close()
    return True


def getLog(user):
    con = sql.connect("database.db")
    cur = con.cursor()

    cur.execute("SELECT * FROM log WHERE user=='{0}'".format(user))

    ret = cur.fetchall()
    con.commit()
    con.close()

    print ret
    if len(ret)==0:
        return None
    return ret
