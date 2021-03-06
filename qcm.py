import numpy as np
import secrets
import json
import os
import time

import pandas as pd
import qrcode
from qrcode.image.svg import SvgImage
from io import BytesIO
import zipfile
import glob

from sqlite3 import *


conn = connect("data.txt")

cur = conn.cursor()

cur.execute(
    "CREATE TABLE IF NOT EXISTS qcm (id INTEGER, questions TEXT, secret TEXT, start FLOAT, end FLOAT, total FLOAT)"
)

cur.execute(
    "CREATE TABLE IF NOT EXISTS reponses (id INTEGER, html TEXT, count FLOAT, name TEXT, secret TEXT, timestamp FLOAT)"
)


realTime = """<div align=center><form name="myForm" action="" method="POST"><input name="myClock" type="Text" style="text-align:center; width:200px;"></form></div><script language=javascript>self.setInterval(function () {time=new Date().toGMTString(); document.myForm.myClock.value=time},50)</script>"""


def txt2list(qcm):
    """
    input: str ou paht du qcm

    output: [["q", ("-p", int point), (), (), ()], [], [] ]

        les questions ouvertes sont au format ["q", (str nombre ligne du form, int point]
        les qcm sont au format ["q", ("-p", int point), (), (), ()]
    """

    if os.path.isfile(qcm):  # si upload depuis local

        with open(qcm, 'r') as f:

            x = f.readlines()
            x = x[2:]

    else:  # si str chargée depuis formulaire

        x = qcm
        x = x.split('\r')
        x = x[2:]

    for i, j in enumerate(x):

        # on remplace les ‘ issues du fichier local ou les ‘ transformées en
        # \x92 issues du formulaire par des fausses appos
        x[i] = replacequote(j)

    x = " ".join(x)

    y = x.split('\n')

    while '' in y:

        y.remove('')

    while ' ' in y:

        y.remove(' ')

    for i, j in enumerate(y):

        y[i] = j.strip()

    # restucture liste et formatage lien et reconnaissance note dans liste
    # notes admises

    for i, j in enumerate(y):

        if j[0] == "-":  # c'est une proposition relative à une question de QCM

            notes = [-0.5, -1.5, 1.5, 0.5, -1, -2, 1, 2, 0]

            z = y[i]

            for n in notes:

                nn = str(n)
                nn = nn.replace(".", ",")

                if z[len(j) - len(nn):] == nn:

                    y[i] = (z[:len(z) - len(nn)], n)

                    break

    # formatage lien

    for i, j in enumerate(y):

        if isinstance(j, type("")) and (
                j[:8] == "http://" or j[:7] == "http://"):

            j = j.strip()

            j = "<div align=center><img src='{0}' width=50%></div>".format(
                j)

            y[i] = j

    for i, j in enumerate(y):

        if isinstance(j, type("")):

            for d in y[i + 1:]:

                if isinstance(d, type("")):

                    y[i] += " " + d

                    y.remove(d)

                else:

                    break

    # decoupage questions

    ind = []

    for i, j in enumerate(y):

        if i == 0:

            pass

        elif isinstance(j, type(())) and isinstance(y[i - 1], type("")):

            ind.append(i - 1)

    k = []

    for i, j in enumerate(ind):

        if i > 0:

            k.append(y[ind[i - 1]:j])

    k.append(y[ind[len(ind) - 1]:])

    return k


def qcmChecker(k):
    """
    input: qcm au format liste retourné par la fonction txt2list()

    output: qcm au meme format avec questions mélangées.
    """

    g = np.random.choice(np.arange(len(k)), len(k), replace=False)

    kk = []

    for i in g:

        kk.append(k[i])

    for i, j in enumerate(kk):

        l = j[1:]

        gg = np.random.choice(np.arange(len(l)), len(l), replace=False)

        t = [j[0]]

        for q in gg:

            t.append(l[q])

        kk[i] = t

    return kk


def getInfo(qcm):
    """

    input: str ou path du qcm

    output: strat et end du qcm au format timestamp

    """

    if os.path.isfile(qcm):

        with open(qcm, "r") as f:

            lines = f.readlines()

            start = lines[0]

            start = time.strptime(start[:len(start) - 1], '%d/%m/%Y %Hh%M')
            start = time.mktime(start)

            end = lines[1]
            end = time.strptime(end[:len(end) - 1], '%d/%m/%Y %Hh%M')
            end = time.mktime(end)

    else:

        qcm = qcm.replace('\n', "")
        lines = qcm.split('\r')

        start = lines[0]
        start = time.strptime(start, '%d/%m/%Y %Hh%M')
        start = time.mktime(start)

        end = lines[1]
        end = time.strptime(end, '%d/%m/%Y %Hh%M')
        end = time.mktime(end)

    return start, end


def getNewId():

    cur.execute("SELECT id FROM qcm")

    r = cur.fetchall()

    x = []

    for i in r:

        for j in i:

            x.append(int(j))

    if len(x) == 0:

        x.append(1000)

    return max(x) + 1


def eleveGetResult(secret):

    cur.execute("SELECT * FROM reponses WHERE secret = ?", (secret, ))

    r = cur.fetchone()

    return r


def profGetResult(id):

    cur.execute("SELECT * FROM reponses WHERE id = ?", (id, ))

    r = cur.fetchall()

    return r


def profIsOwner(id, secret):

    cur.execute("SELECT * FROM qcm  WHERE id = ?", (id, ))

    r = cur.fetchone()

    if secret == r[2]:

        return True

    else:

        return False


def getTotal(k):
    """
    input: qcm au format liste retourné par la fonction txt2list()

    output: total des points du qcm et ou des questions ouvertes

    """

    if isTrueQCM(k):

        total = []

        for i in k:

            x = []

            for j in i[1:]:

                x.append(j[1])

            m = max(x)

            total.append(m)

        s = sum(total)

    else:

        total = []

        for i in k:

            x = []

            for j in i[1:]:

                if j[1] > 0:

                    x.append(j[1])

            m = sum(x)

            total.append(m)

        s = sum(total)

    return s


def qcm2sqlGetHTML(path):
    """
    input: str ou path du qcm

    output: html a afficher après creation du qcm sur le site ou upload du qcm via le site

    """

    x = qcm2sql(path)

    id = x[0]

    start = formaTime(x[1][0])

    end = formaTime(x[1][1])

    alerte = "Toutes les données relatives à ce QCM seront détruites 10 jours après la fin de validité du QCM.</br>Pensez à télécharger les résultats de vos élèves avant le {0}".format(
        formaTime(
            x[1][1] +
            864000))

    password = x[2]

    if os.path.isfile(path):

        os.remove(path)

    # creat qrcode eleve

    linkeleve = "http://192.168.43.206:27200/getqcm/{0}".format(id)

    streameleve = BytesIO()
    imgeleve = qrcode.make(linkeleve, image_factory=SvgImage)
    imgeleve.save(streameleve)

    linkeleve = streameleve.getvalue().decode()

    # creat qrcode prof

    linkprof = "http://192.168.43.206:27200/prof/{0}/{1}".format(
        id, password)

    streamprof = BytesIO()
    imgprof = qrcode.make(linkprof, image_factory=SvgImage)
    imgprof.save(streamprof)

    linkprof = streamprof.getvalue().decode()

    html = """<h1 align=center>OpenQCM</h1></br>{4}</br>
        <h3 align=center>Votre QCM référence: {0} a bien été enregistré.</h3>
        <h4 align=center>Ce QCM est actif du {1} au {2}</h4>

        <h4 align=center>Communiquez ce lien à vos élèves:</h4>
        <p align=center><a
href="http://192.168.43.206:27200/getqcm/{0}">http://192.168.43.206:27200/getqcm/{0}</a></p>
        <div align=center>{6}</div>
        </br></br>
        <h2 align=center>Votre code secret est: <em>{3}</em></h2>
        <h5 align=center>Conservez ce code confidentiel et/ou le lien confidentiel ci-dessous.</br>Ils vous seront indispensables pour obtenir les résultats de vos élèves.</h5>

        <h3 align=center>Votre interface professeur est disponible à l’adresse suivante:</h3>

        <p align=center><a href="http://192.168.43.206:27200/prof/{0}/{3}">http://192.168.43.206:27200/prof/{0}/{3}</a></p>
        <div align=center>{5}</div><p align=center>{7}</p>""".format(id, start, end, password, realTime, linkprof, linkeleve, alerte)

    return html


def qcm2sql(qcmPath):
    """
    input: str ou path du qcm

    output: id, (strat timestamp, end timestamp), password prof

    ajoute les données du qcm dans la table qcm

    """

    k = txt2list(qcmPath)

    total = getTotal(k)

    info = getInfo(qcmPath)

    id = getNewId()

    password = secrets.token_urlsafe(8)

    d = (
        id,
        json.dumps(
            k,
            ensure_ascii=False),
        password,
        info[0],
        info[1],
        total)

    cur.execute(
        "INSERT INTO qcm (id, questions, secret, start, end, total) VALUES(?,?,?,?,?,?)",
        d)

    conn.commit()

    return id, info, password


def response2sql(id, html, count, name, timestamp):
    """
    input:

        id du qcm
        html de la réponse élève
        count du total de point de l'élève
        name (pseudo) de l'élève
        timestamp de l'envoi des réponses par l'élève

    output: memes info + password eleve
    """

    password = secrets.token_urlsafe(8)  # creation du password eleve

    d = (id, html, count, name, password, timestamp)

    cur.execute(
        "INSERT INTO reponses (id, html, count, name, secret, timestamp) VALUES(?,?,?,?,?,?)",
        d)

    conn.commit()

    return d


def getQcmFromSQL(id):

    cur.execute("SELECT * FROM qcm WHERE id = ?", (id, ))

    r = cur.fetchone()

    return r


def creatForm(id):

    x = getQcmFromSQL(id)

    qcm = json.loads(x[1])
    qcm = qcmChecker(qcm)

    s = formaTime(x[3])
    e = formaTime(x[4])

    realTime = """<div align=center><form name="myForm" action="" method="POST"><input name="myClock" type="Text" style="text-align:center; width:200px;"></form></div><script language=javascript>self.setInterval(function () {time=new Date().toGMTString(); document.myForm.myClock.value=time},50)</script>"""

    delta = "<h1 align=center>OpenQCM</h1><p align=center>Ce QCM est actif du {0} au {1}</p></br>".format(
            s, e)

    d = delta + realTime + \
        """<form method="post" action="/send" accept-charset="iso-8859-1"><p align=center>Pseudo: <input type="text" size="21" maxlength="8" placeholder="8 caractères maximum" name="name" required/></p><input type="hidden" name="id" value="{0}"/><br/><br/><br/>""".format(id)

    for i in qcm:

        label = i[0]

        d += "<hr><p width=100%><strong>{0}</strong></p></br>".format(
            restorequote(label))

        for j in i[1:]:

            if isTrueQCM(qcm):

                d += """<input type="radio" name="{0}" value="{1}" required/>{2}</br>""".format(
                    label, j[0][1:], restorequote(j[0][1:]))

            else:

                d += """<input type="checkbox" name="{0}" value="{1}"/>{2}</br>""".format(
                    label, j[0][1:], restorequote(j[0][1:]))

            # attention tu as retiré le "-" il faudra y penser lors des compara

        d += "</br><hr>"

    d += """<hr><p align=center><input type="submit" value="Enregistrer" required /></p></form>"""

    return d, x[3], x[4]


def formaTime(timestamp):
    """

    Convert timestamp UNIX to format time: '21/10/2020 08h36 GMT'

    """

    t = time.gmtime(timestamp)

    if len(str(t[4])) == 1:

        m = "0" + str(t[4])

    else:

        m = t[4]

    if len(str(t[3])) == 1:

        h = "0" + str(t[3])

    else:

        h = t[3]

    if len(str(t[1])) == 1:

        mois = "0" + str(t[1])

    else:

        mois = t[1]

    if len(str(t[2])) == 1:

        jour = "0" + str(t[2])

    else:

        jour = t[2]

    f = """{0}/{1}/{2} {3}h{4} GMT""".format(jour, mois, t[0], h, m)

    return f


def isTrueQCM(k):
    """

    Retourne True si c'est un vrai QCM avec 1 seule bonne réponse par question

    Retourne False si c'est un Vrai / Faux

    """

    r = []

    for q in k:

        x = []

        for p in q[1:]:

            x.append(p[1])

        c = 0

        for i in x:

            if i > 0:

                c += 1

        r.append(c)

    for i in r:

        if i > 1:

            return False

    return True


def replacequote(x):
    """
    remplace les guillemet, les x92 (guillement) issu des form html et les doublequoote par des caractères compatible SQL
    """

    x = x.replace("’", "´")
    x = x.replace("\x92", "´")
    x = x.replace('"', "$$")

    return(x)


def restorequote(x):
    """restore les guillemet et les double quote a la sortie de sql avant affichage html"""

    x = x.replace("´", "’")

    x = x.replace("$$", '"')

    return(x)
