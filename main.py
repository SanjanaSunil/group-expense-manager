from flask import Flask
from flask import render_template
from flask import request, url_for, redirect, session, flash
from datetime import date
from datetime import time
from datetime import datetime
import models_1 as dbHandler
from hashlib import md5

app = Flask(__name__)
app.config['SECRET_KEY'] = 'e5ac358c-f0bf-11e5-9e39-d3b532c10a28'

######################################################################


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


@app.route('/', methods=['POST', 'GET'])
@app.route('/home', methods=['POST', 'GET'])
def index():
    if 'username' in session:
        username = session['username']
        avatar = dbHandler.getProfilePic(username, 100)
        groups = dbHandler.getGroups(username)
        gd = {}
        for i in groups:
            temp = dbHandler.getGroupMemebers(i[0], i[1])
            gd[i] = temp
            groups = gd
        if request.method == 'POST':
            search = request.form['search']
            if search != username:
                result = dbHandler.searchUser(search)
                if result != "No":
                    return redirect(url_for('anotheruser', result=result))
                return render_template('loggedinindex.html', username=username, result=result, groups=gd, avatar=avatar)
        return render_template('loggedinindex.html', username=username, groups=gd, avatar=avatar)
    return render_template('index.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    if 'username' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        if not dbHandler.uniq(username):
            return render_template('register.html', notUniq="nonunique")

        password = request.form['password']
        email = request.form['email']
        dbHandler.insertUser(username, password, email)
        session['username'] = username
        return redirect(url_for('index'))
    else:
        return render_template('register.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if 'username' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if dbHandler.allowLogin(username, password):
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', failedLogin="failed")
    else:
        return render_template('login.html')


@app.route('/logout')
def logout():
    if 'username' in session:
        session.pop('username', None)
    return redirect(url_for('index'))

######################################################################


# 0 represents user not logged in, 1 represents able to send a friend request, 2 represents request sent and 3 is already friends
@app.route('/user/<result>', methods=['POST', 'GET'])
def anotheruser(result):
    if 'username' in session:
        username = session['username']
        avatar = dbHandler.getProfilePic(result, 100)
        if username == result:
            return redirect(url_for('index'))
        if request.method == 'POST' or dbHandler.getStatus(username, result) == 2:
            dbHandler.sendRequest(username, result, 2)
            return render_template('anotheruser.html', anotheruser=result, loggedin=2, avatar=avatar)

        elif dbHandler.getStatus(username, result) == 3:
            friends = dbHandler.getFriends(username)
            nonGroupTrans = dbHandler.getNonGroupTrans(username)
            indiTrans = {}
            for friend in friends:
                indiTrans[friend[0]] = 0
                print friend[0]
            for group in nonGroupTrans:
                if group[3] in indiTrans.keys():
                    indiTrans[group[3]] -= group[5]
                if group[4] in indiTrans.keys():
                    indiTrans[group[4]] += group[5]
            return render_template('anotheruser.html', anotheruser=result, loggedin=3, indiTrans=indiTrans, avatar=avatar)

        elif dbHandler.getStatus(result, username) == 2:
            return render_template('anotheruser.html', anotheruser=result, loggedin=4, avatar=avatar)
        else:
            return render_template('anotheruser.html', anotheruser=result, loggedin=1, avatar=avatar)
    return render_template('anotheruser.html', anotheruser=result, loggedin=0, avatar=avatar)


@app.route('/addNonGroupTrans', methods=['POST', 'GET'])
def addNonGroupTrans():
    if 'username' in session:
        username = session['username']
        anotheruser = request.args.get('anotheruser')
        print anotheruser
        status = request.args.get('status')
        trans = request.form['trans']

        if status == "send":
            dbHandler.addGroupTrans(
                "default", "default", username, anotheruser, trans)
        else:
            dbHandler.addGroupTrans(
                "default", "default", anotheruser, username, trans)

        return redirect(url_for('anotheruser', result=anotheruser))


@app.route('/notifications', methods=['POST', 'GET'])
def notifications():
    if 'username' in session:
        username = session['username']
        sender = request.args.get('sender')
        redirectType = request.args.get('redirectType')
        print "printintg accept"
        print request.args.get('accept')
        if request.args.get('accept') == 'True':
            print "Okay I'm here    "
            dbHandler.sendRequest(username, sender, 3)
            dbHandler.sendRequest(sender, username, 3)
        elif request.args.get('decline') == 'True':
            dbHandler.deleteRequest(sender, username)

        friendrequests = dbHandler.getRequests(username)
        if redirectType == 'anotheruser':
            return redirect(url_for('anotheruser', result=sender))
        return render_template('notifications.html', friendrequests=friendrequests)
    return redirect(url_for('login'))


######################################################################


@app.route('/friends')
def getFriends():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    friends = dbHandler.getFriends(username)
    nonGroupTrans = dbHandler.getNonGroupTrans(username)
    print "^^^^^^^^^^"
    indiTrans = {}
    for friend in friends:
        indiTrans[friend[0]] = 0
        print friend[0]
    for group in nonGroupTrans:
        if group[3] in indiTrans.keys():
            indiTrans[group[3]] -= group[5]
        if group[4] in indiTrans.keys():
            indiTrans[group[4]] += group[5]
    print indiTrans
    for item in indiTrans.keys():
        print item[0]
    return render_template('friends.html', friends=friends, nonGroupTrans=nonGroupTrans, indiTrans=indiTrans)


#####################################################################


def buildCtrans(temp):
    ctrans = {}
    for i in temp:
        print (i[1:5])
        if (i[1], i[2], i[4], i[3]) in ctrans.keys():
            ctrans[(i[1], i[2], i[4], i[3])] -= i[5]
        elif (i[1], i[2], i[3], i[4]) not in ctrans.keys():
            ctrans[(i[1], i[2], i[3], i[4])] = i[5]
        else:
            ctrans[(i[1], i[2], i[3], i[4])] += i[5]

        if (i[1], i[2], i[3], i[4]) in ctrans.keys() and ctrans[(i[1], i[2], i[3], i[4])] == 0:
            ctrans.pop((i[1], i[2], i[3], i[4]), 0)
        if (i[1], i[2], i[4], i[3]) in ctrans.keys() and ctrans[(i[1], i[2], i[4], i[3])] == 0:
            ctrans.pop((i[1], i[2], i[4], i[3]), 0)
    return ctrans


names = []
# REMEMBER TO RESET NAMES LIST!!!!!!!!!!!!!!!!!!


@app.route('/new', methods=['POST', 'GET'])
def createGroup():

    global names

    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    friends = dbHandler.getFriends(username)
    alist = []
    groupname = None
    problem = False

    for friend in friends:
        alist.append(friend[0])

    if request.method == 'POST':
        groupname = request.form['groupname']

        if request.form['add'] == 'Create Group':
            groups = dbHandler.getGroups(username)

            check = True
            for group in groups:
                if group[0] == groupname and group[1] == username:
                    check = False
                    break

            if check:
                now = datetime.now()
                groupDate = now.strftime("%a, %d %B, %Y")
                dbHandler.log(username, "Created group " + groupname)
                dbHandler.createGroup(groupname, username, groupDate)
                for name in names:
                    dbHandler.addGroupie(groupname, username, name)
                names = []
                return redirect(url_for('index'))
            else:
                groupname = None
                problem = True

        name = request.form['tags']
        if name in alist:
            if name not in names:
                names.append(name)
    return render_template('createGroup.html', friends=alist, names=names, groupname=groupname, problem=problem)


@app.route('/viewGroup', methods=['POST', 'GET'])
def viewGroup():
    if 'username' not in session:
        return redirect(url_for('login'))

    groupName = request.args.get('groupName')
    admin = request.args.get('admin')
    username = session['username']
    memebers = dbHandler.getGroupMemebers(groupName, admin)
    memebers = [i[2] for i in memebers]
    memebers = sorted(memebers)

    problem = request.args.get('problem')
    temp = dbHandler.getGroupTrans(groupName, admin)
    ctrans = buildCtrans(temp)

    labels = dbHandler.getLabels(groupName, admin)

    labelTrans = {}
    for labl in labels:
        tmp = {}
        tmp['labelTrans'] = dbHandler.getGroupTrans(groupName, admin, labl)
        print tmp
        t = 0
        for j in tmp['labelTrans']:
            t = t + j[5]
        tmp['labelTotal'] = t
        tmp['labelLender'] = tmp['labelTrans'][0][3]
        tmp['labelZeroes'] = []
        for i in memebers:
            flag = 0
            for j in tmp['labelTrans']:
                if i == j[4]:
                    flag = 1

            if not flag:
                tmp['labelZeroes'].append(i)

        print 'bs________________________'
        print labl, tmp['labelZeroes']
        labelTrans[labl] = tmp

    print "labels or kuch bhi"
    print labels
    print labelTrans

    comments = dbHandler.getComment(groupName, admin)
    avatar = dbHandler.getProfilePic(username, 30)
    vertices = comments[1]
    comments = comments[0]

    friends=[i for i in memebers if i != username]
    nonGroupTrans = dbHandler.getGroupTrans(groupName, admin)
    nonGroupTrans = [i for i in nonGroupTrans if i[3]==username or i[4]==username]
    print "^^^^^^^^^^"
    print nonGroupTrans
    indiTrans = {}
    for friend in friends:
        indiTrans[friend[0]] = 0
        print friend[0]
    for group in nonGroupTrans:
        if group[3] in indiTrans.keys():
            indiTrans[group[3]] -= group[5]
        if group[4] in indiTrans.keys():
            indiTrans[group[4]] += group[5]
    print indiTrans
    return render_template('group.html', labels=labels, labelTrans=labelTrans, avatar=avatar, admin=admin, username=username, groupName=groupName, memebers=memebers, problem=problem, indiTrans=indiTrans, trans=temp, comments=comments, vertices=vertices)


@app.route('/delGroup/<groupName>', methods=['POST', 'GET'])
def delGroup(groupName):
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    dbHandler.delGroup(groupName, username)
    return redirect(url_for('index'))


@app.route('/delGroupie', methods=['POST', 'GET'])
def delGroupie():
    if 'username' not in session:
        return redirect(url_for('login'))

    admin = session['username']
    deletie = request.args.get('deletie')
    groupName = request.args.get('groupName')

    dbHandler.delGroupie(groupName, admin, deletie)

    return redirect(url_for('viewGroup', admin=admin, groupName=groupName))


@app.route('/addGroupie', methods=['POST', 'GET'])
def addGroupie():
    if 'username' not in session:
        return redirect(url_for('login'))

    groupName = request.args.get('groupName')
    rAddr = request.args.get('rAddr')
    username = session['username']

    if request.method == 'POST':

        memebers = dbHandler.getGroupMemebers(groupName, username)
        add = request.form['add']
        if (groupName, username, add) in memebers:
            return redirect(url_for(rAddr, groupName=groupName, admin=username, problem='memeber'))

        friends = dbHandler.getFriends(username)
        for friend in friends:
            if add == friend[0]:
                dbHandler.addGroupie(groupName, username, add)

        return redirect(url_for(rAddr, groupName=groupName, admin=username))


####################################################################


@app.route('/addTrans', methods=['POST', 'GET'])
def addTrans():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    groupName = request.args.get('groupName')
    admin = request.args.get('admin')
    fro = request.form['fro']
    to = request.form['to']
    amt = request.form['amt']

    friends = dbHandler.getGroupMemebers(groupName, admin)
    flag = 0
    for friend in friends:
        if fro == friend[2]:
            flag = flag + 1
        if to == friend[2]:
            flag = flag + 1

    # if fro == username or to == username:
    #    flag = flag+1
    if fro == to:
        flag = 0

    if flag > 1:
        dbHandler.addGroupTrans(groupName, admin, fro, to, amt)

    return redirect(url_for('viewGroup', admin=admin, groupName=groupName))


@app.route('/delTrans', methods=['POST', 'GET'])
def delTrans():
    if 'username' not in session:
        return redirect(url_for('login'))

    groupName = request.args.get('groupName')
    admin = request.args.get('admin')
    tid = request.args.get('tid')
    fro = request.args.get('fro')
    to = request.args.get('to')

    if tid=='False':
        dbHandler.delGroupTransBulk(groupName, admin, fro, to)
    dbHandler.delGroupTrans(tid)

    return redirect(url_for('viewGroup', admin=admin, groupName=groupName))

###############################################################


@app.route('/addComment', methods=['POST', 'GET'])
def addComment():
    if 'username' not in session:
        return redirect(url_for('home'))

    admin = request.args.get('admin')
    groupName = request.args.get('groupName')
    par = request.args.get('par')
    comment = request.form['comment']
    username = session['username']

    now = datetime.now()
    commentDate = now.strftime("%a, %d %B, %Y")
    print commentDate

    dbHandler.addComment(groupName, admin, comment, par, username, commentDate)
    return redirect(url_for('viewGroup', groupName=groupName, admin=admin))


@app.route('/delComment', methods=['POST', 'GET'])
def delComment():
    if 'username' not in session:
        return redirect(url_for('home'))

    admin = request.args.get('admin')
    groupName = request.args.get('groupName')
    par = request.args.get('par')
    commentDate = request.args.get('commentDate')
    # comment = request.form['comment']
    username = session['username']

    # now = datetime.now()
    # commentDate = now.strftime("%a, %d %B, %Y")
    # print commentDate

    dbHandler.delComment(groupName, admin, par, username, commentDate)
    return redirect(url_for('viewGroup', groupName=groupName, admin=admin))


@app.route('/editComment', methods=['POST', 'GET'])
def editComment():
    if 'username' not in session:
        return redirect(url_for('home'))

    admin = request.args.get('admin')
    groupName = request.args.get('groupName')
    cid = request.args.get('cid')
    comment = request.form['comment']
    username = session['username']

    print "reached here"
    # now = datetime.now()
    # commentDate = now.strftime("%a, %d %B, %Y")
    # print commentDate

    dbHandler.editComment(cid, comment, username, groupName)
    return redirect(url_for('viewGroup', groupName=groupName, admin=admin))


##############################################################


@app.route('/viewLog', methods=['POST', 'GET'])
def viewLog():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    logs = dbHandler.getLog(username)

    return render_template("log.html", user=username, logs=logs)


@app.route('/delLog', methods=['POST', 'GET'])
def delLog():
    if 'username' not in session:
        return redirect(url_for('login'))

    lid = request.args.get('lid')

    dbHandler.delLog(lid)
    return redirect(url_for('viewLog'))


############################################################

@app.route('/addBillTrans', methods=['POST', 'GET'])
def addBillTrans():
    if 'username' not in session:
        return redirect(url_for('login'))

    print "Well Okay... ^^^^^^^^^^^^^^^^^^^^^"
    groupName = request.args.get('groupName')
    admin = request.args.get('admin')
    lender = request.form['lender']
    receivers = dbHandler.getGroupMemebers(groupName, admin)
    label = request.args.get('label')
    if label:
        pass
    else:
        label = request.form['label']

    dbHandler.delGroupTransForLabel(groupName, admin, label)
    labels = dbHandler.getLabels(groupName, admin)
    for receiver in receivers:
        trans = request.form['n' + receiver[2]]
        if trans == 0:
            continue
        dbHandler.addGroupTrans(groupName, admin, lender,
                                receiver[2], trans, label)

    return redirect(url_for('viewGroup', groupName=groupName, admin=admin, problem=None, labels=labels))


@app.route('/settleBill', methods=['POST', 'GET'])
def settleBill():
    if 'username' not in session:
        return redirect(url_for('login'))

    groupName = request.args.get('groupName')
    admin = request.args.get('admin')
    # lender = request.form['lender']
    # receivers = dbHandler.getGroupMemebers(groupName, admin)
    label = request.args.get('label')
    if label:
        pass
    else:
        label = request.form['label']
    labels = dbHandler.getLabels(groupName, admin)

    dbHandler.delGroupTransForLabel(groupName, admin, label)
    return redirect(url_for('viewGroup', groupName=groupName, admin=admin, problem=None, labels=labels))


##############################################################
if __name__ == '__main__':
    app.run(debug=True)
