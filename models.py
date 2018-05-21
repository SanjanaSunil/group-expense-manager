import sqlite3 as sql
import datetime
from hashlib import md5

# REGISTER

def getProfilePic(user, size):
    con = sql.connect("database.db")
    cur = con.cursor()
    obj = cur.execute("SELECT email FROM users WHERE username='" + user + "'")
    obj = str(obj.fetchone())
    digest = md5(obj.lower().encode('utf-8')).hexdigest()
    return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)



def insertUser(username, password, email):
    con = sql.connect("database.db")
    cur = con.cursor()
    cur.execute("INSERT INTO users (username,password,email) VALUES (?,?,?)",
                (username, password, email))
    con.commit()
    con.close()


def uniq(username):
    con = sql.connect("database.db")
    cur = con.cursor()
    obj = cur.execute("SELECT * FROM users WHERE username='" + username + "'")
    if obj.fetchone():
        return False
    else:
        return True

# LOGIN


def allowLogin(username, password):
    con = sql.connect("database.db")
    cur = con.cursor()
    cur.execute("SELECT username, password FROM users WHERE username='{0}' AND password='{1}'".format(
        username, password))
    if cur.fetchone():
        return True
    else:
        return False

# SEARCH FOR USER DETAILS


def searchUser(info):
    con = sql.connect("database.db")
    cur = con.cursor()
    obj = cur.execute("SELECT * FROM users WHERE username='" +
                      info + "' OR email='" + info + "'")
    if obj.fetchone():
        return str(info)
    else:
        return "No"


def getFriendCount(user):
    con = sql.connect("database.db")
    cur = con.cursor()
    obj = cur.execute(
        "SELECT friendcount FROM users WHERE username='" + user + "'")
    for row in obj:
        return row[0]

# FRIEND REQUESTS etc


def sendRequest(fro, to, stat):
    con = sql.connect("database.db")
    cur = con.cursor()
    cur.execute("INSERT INTO friendship (friendone,friendtwo,status) VALUES ('{0}', '{1}', {2})".format(fro, to, stat))
    con.commit()
    con.close()


def getRequests(user):
    con = sql.connect("database.db")
    cur = con.cursor()
    obj = cur.execute("SELECT friendone FROM friendship WHERE friendtwo=='{0}' AND status==2".format(user))
    obj = obj.fetchall()
    con.commit() 
    con.close()
    return obj


def getStatus(fro, to):
    con = sql.connect("database.db")
    cur = con.cursor()
    obj = cur.execute("SELECT status FROM friendship WHERE friendone='" +
                      fro + "' AND friendtwo='" + to + "'")
    for row in obj.fetchall():
        if row[0] == 2:
            return 2
        else:
            return 3


def getFriends(user):
    con = sql.connect("database.db")
    cur = con.cursor()
    obj = cur.execute("SELECT friendtwo FROM friendship WHERE friendone='" + user + "' AND status='3'")
    obj = obj.fetchall()
    con.commit()
    con.close()
    return obj


def deleteRequest(fro, to):
    con = sql.connect("database.db")
    cur = con.cursor()
    cur.execute("DELETE FROM friendship WHERE friendone='" +
                fro + "' AND friendtwo='" + to + "'")
    con.commit()
    con.close()


#GROUPS

def getNonGroupTrans(user):
    con = sql.connect("database.db")
    cur = con.cursor()

    cur.execute(
        "SELECT * FROM gtrans WHERE gname=='default' AND admin=='default' AND (lender=='{0}' OR receiver=='{0}')".format(user))

    return cur.fetchall()


def createGroup(groupName, user, groupDate):
    con = sql.connect("database.db")
    cur = con.cursor()

    cur.execute(
        "SELECT * FROM groups WHERE gname=='{0}' AND admin=='{1}'".format(groupName, user))
    if cur.fetchone():
        return True
    else:
        con.commit()
        log(user, "created "+groupName)
        cur.execute(
            "INSERT INTO groups (gname, admin, memeber, groupDate) VALUES (?,?,?,?)", (groupName, user, user, groupDate))

    con.commit()
    con.close()
    return True


def addGroupie(groupName, admin, addie):
    con = sql.connect("database.db")
    cur = con.cursor()

    cur.execute(
        "SELECT * FROM groups WHERE gname=='{0}' AND admin=='{1}' AND memeber=='{2}'".format(groupName, admin, addie))
    if cur.fetchone():
        return True
    else:
        obj = cur.execute("SELECT groupDate FROM groups WHERE admin='" + admin + "' AND gname='" + groupName + "'")
        date = obj.fetchone()
        print date
        cur.execute("INSERT INTO groups (gname, admin, memeber, groupDate) VALUES (?,?,?,?)",
                    (groupName, admin, addie, date[0]))

    con.commit()
    con.close()
    return True

def delGroupie(groupName, admin, deltie):
    con = sql.connect("database.db")
    cur = con.cursor()

    cur.execute("DELETE FROM groups WHERE gname=='{0}' AND admin=='{1}' AND memeber=='{2}'".format(
        groupName, admin, deltie))

    cur.execute("UPDATE gtrans SET gname='default', admin='default' WHERE gname=='{0}' AND admin=='{1}' AND (lender=='{2}' OR receiver=='{2}')".format(
        groupName, admin, deltie))
    con.commit()
    con.close()
    return True

def getGroups(user):
    con = sql.connect("database.db")
    cur = con.cursor()

    cur.execute(
        "SELECT gname, admin, groupDate FROM groups WHERE admin=='{0}' OR memeber=='{0}'".format(user))
    lis = cur.fetchall()
    print lis
    ret = []
    for item in lis:
        if item not in ret:
            ret.append(item)
    return ret
    con.commit()
    con.close()

################################################
def addGroupTrans(groupName, admin, fro, to, trans):
    con = sql.connect("database.db")
    cur = con.cursor()

    # cur.execute(
    #     "SELECT * FROM groups WHERE gname=='{0}' AND admin=='{1}' AND lender=='{2}' AND receiver=='{3}'".format(groupName, admin, fro, to))

    # if cur.fetchone():
    #     cur.execute("UPDATE groups SET trans=trans+'{4}' WHERE gname=='{0}' AND admin=='{1}' AND lender=='{2}' AND receiver=='{3}'".format(
    #         groupName, admin, fro, to, amt))
    # else:
    cur.execute("INSERT INTO gtrans (gname, admin, lender, receiver, amount) VALUES (?,?,?,?,?)",
                (groupName, admin, fro, to, trans))

    con.commit()
    cur.execute("SELECT max(tid) FROM gtrans")
    tid = cur.fetchone()[0]

    con.close()

    return tid


def delGroupTrans(tid):
    con = sql.connect("database.db")
    cur = con.cursor()

    cur.execute("DELETE FROM gtrans WHERE tid=='{0}'".format(tid))

    con.commit()
    con.close()


def getGroupMemebers(groupName, admin):
    con = sql.connect("database.db")
    cur = con.cursor()

    cur.execute(
        "SELECT gname, admin, memeber FROM groups WHERE gname=='{0}' AND admin=='{1}'".format(groupName, admin))
    return cur.fetchall()

    con.commit()
    con.close()

def delGroup(groupName, admin):
    con = sql.connect("database.db")
    cur = con.cursor()

    cur.execute("UPDATE gtrans SET gname='default', admin='default' WHERE gname=='{0}' AND admin=='{1}'".format(groupName, admin))

    cur.execute("DELETE FROM groups WHERE gname=='{0}' AND admin=='{1}'".format(
        groupName, admin))
    cur.execute("DELETE FROM comments WHERE gname=='{0}' AND admin=='{1}'".format(groupName, admin))

    con.commit()
    con.close()

def getGroupTrans(groupName, admin):
    con = sql.connect("database.db")
    cur = con.cursor()

    cur.execute(
        "SELECT * FROM gtrans WHERE gname=='{0}' AND admin=='{1}'".format(groupName, admin))
    return cur.fetchall()

    con.commit()
    con.close()

######################################################################

def getComment(groupName, admin):
    con = sql.connect("database.db")
    cur = con.cursor()

    ret = {}
    lis = []
    cur.execute(
        "SELECT * FROM comments WHERE gname=='{0}' AND admin=='{1}'".format(groupName, admin))
    for i in cur.fetchall():
        print i
        if i[3] == -1:
            ret[i[0]] = {'comment': i[5], 'username': i[2], 'children': [], 'commentDate': i[6]}
            lis.append(i[0])
        else:
            ret[i[0]] = {'comment': i[5], 'username': i[2], 'children': [], 'commentDate': i[6]}
            ret[i[3]]['children'].append(i[0])

    return (ret, lis)  # lis is the list of start vertices

    con.commit()
    con.close()


def addComment(groupName, admin, com, par, user, commentDate):
    con = sql.connect("database.db")
    cur = con.cursor()

    cur.execute(
        "INSERT INTO comments (gname, admin, comment, parent, username, commentDate) VALUES (?,?,?,?,?,?)", (groupName, admin, com, par, user, commentDate))

    con.commit()loglog
    con.close()

###################################################################

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
