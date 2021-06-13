from bottle import *
from qcm import *


realTime = """<div align=center><form name="myForm" action="" method="POST"><input name="myClock" type="Text" style="text-align:center; width:200px;"></form></div><script language=javascript>self.setInterval(function () {time=new Date().toGMTString(); document.myForm.myClock.value=time},50)</script>"""


@route('/static/<filepath:path>')
def send_static(filepath):

    return static_file(filepath, root='./static/')


@route('/')
@route('/<exe>')
def index(exe=""):

    exemple = exe

    txt = """
        <form method="post" action="/traitementtxt" accept-charset="ISO-8859-1">
        <textarea name="txt" id="txt" rows="30" cols="150" wrap="virtual" style="overflow:scroll;">{0}</textarea>
        <input type="submit" name="creat" value="Envoyer"/>
        </form>""".format(exemple)

    ld = """
        <form action="/traitementExemple" method="post" accept-charset="ISO-8859-1">
        <label for="listderoulante">Besoin d’aide ?</label>
        <select name="listderoulante" id=listderoulante class="">
        <option value="qcm">QCM (1 seule bonne réponse)</option>
        <option value="vf">VraiFaux (1 ou plusieurs bonnes réponses)</option>
        </select><input type="submit" value="Envoyer"/></form>
        """

    uploader = """<form action="/upload" method="post" enctype="multipart/form-data">
	<h3 align=center>Upload QCM</h3>
	<p align=center><input type="file" name="upload" /></p>
	<p align=center><input type="submit" value="Charger" /></p></form>"""

    ht = """<h1 align=center>OpenQCM</h1>{0}</br><div align=center>{1}</div></br><div align=center>{2}</div></br></br><div class="uploader" align=center>{3}</div><p align=center><a href="https://github.com/YannBouyeron/OpenQCM">Github</a></p>""".format(
        realTime,
        ld,
        txt,
        uploader,
    )

    return template('page.html', {'titre': 'OpenQCM', 'body': ht})


@route('/traitementExemple', method="POST")
def tex():

    x = request.forms.get("listderoulante")

    response.status = 303
    response.set_header('Location',
                        'http://192.168.43.206:27200/{0}'.format(x))


@route('/getqcm/<id>')
@route('/getqcm/<id>/<secretprof>')
def getqcm(id, secretprof=None):

    id = int(id)

    f, s, e = creatForm(id)

    if secretprof is not None:

        pio = profIsOwner(id, secretprof)

    else:

        pio = False

    if pio or (time.time() > s and time.time() < e):

        return template('page.html', {'titre': 'OpenQCM', 'body': f})

    elif time.time() < s:

        ht = "<h1 align=center>OpenQCM</h1></br>{0}</br><h3 align=center>Ce QCM n'est pas encore actif !</h3>".format(
            realTime)

        return template('page.html', {'titre': 'OpenQCM', 'body': ht})

    elif time.time() > e:

        ht = "<h1 align=center>OpenQCM</h1></br>{0}</br><h3 align=center>Ce QCM n'est plus actif !</h3>".format(
            realTime)

        return template('page.html', {'titre': 'OpenQCM', 'body': ht})


@route('/postqcm')
def postqcm():

    x = """<h1 align=center>OpenQCM</h1></br><form action="/upload" method="post" enctype="multipart/form-data"><p align=center>Select a file</p><p align=center><input type="file" name="upload" /></p><p align=center><input type="submit" value="Start upload" /></p></form>"""

    return template('page.html', {'titre': 'OpenQCM', 'body': x})


@route("/traitementtxt", method="POST")
def traittxt():

    txt = request.forms.get("txt")  # str chargée depuis formulaire textarea

    html = qcm2sqlGetHTML(txt)

    return template('page.html', {'titre': 'OpenQCM', 'body': html})


@route('/upload', method='POST')
def do_upload():

    upload = request.files.get('upload')  # fichier chargé depuis local

    path = secrets.token_urlsafe(16)

    name, ext = os.path.splitext(upload.filename)

    if ext != '.txt':

        return 'File extension not allowed.'

    upload.save(path)

    html = qcm2sqlGetHTML(path)

    return template('page.html', {'titre': 'OpenQCM', 'body': html})


@route("/send", method='POST')
def sendresponse():

    id = request.forms.get("id")

    name = request.forms.get("name")

    qcmlist = getQcmFromSQL(int(id))

    qcm = json.loads(qcmlist[1])

    start = qcmlist[3]

    end = qcmlist[4]

    t = time.time()

    if t > end:

        return template('page.html', {
            'titre':
                'OpenQCM',
                'body':
                "<h1 align=center>OpenQCM</h1></br><h3 align=center>Vos réponses ne peuvent pas être accéptées. Le delais est dépassé !</h3>"
        })

    html = ""

    # si QCM ou alors VF

    if isTrueQCM(qcm):

        count = 0

        for i in qcm:

            if len(i) > 2:  # inutile mais pas envie de tabuler

                r = request.forms.get(i[0])

                html += "<p><strong>{0}</strong></p></br>".format(i[0])

                r = "-" + r

                for j in i[1:]:

                    if r == j[0]:

                        html += j[0] + "    <strong>" + \
                            str(j[1]) + "</strong></br></br>"

                        count += float(j[1])

    else:

        count = 0

        for i in qcm:

            if len(i) > 2:  # inutile mais pas envie de tabuler

                w = request.forms.getall(i[0])

                html += "<p><strong>{0}</strong></p></br>".format(i[0])

                for r in w:

                    r = "-" + r

                    for j in i[1:]:

                        if r == j[0]:

                            html += j[0] + "    <strong>" + \
                                str(j[1]) + "</strong></br></br>"

                            count += float(j[1])

        if count < 0:  # les points négatifs ne s’accumulent pas entre les différentes questions

            count = 0

    rep = response2sql(id, html, count, name, t)

    password = rep[4]

    # creat qrcode eleve

    linkeleve = "http://192.168.43.206:27200/eleve/{0}".format(password)

    streameleve = BytesIO()
    imgeleve = qrcode.make(linkeleve, image_factory=SvgImage)
    imgeleve.save(streameleve)

    linkeleve = streameleve.getvalue().decode()

    return template('page.html', {
        'titre':
            'OpenQCM',
            'body':
            """<h1 align=center>OpenQCM</h1>
            </br>{2}</br>
            <h3 align=center>Vos réponses ont bien été enregistrées.</br></br>Vos résultats seront disponibles à partir du {1} à l'adresse suivante:</h3>
            <h3 align=center>
            <a href='http://192.168.43.206:27200/eleve/{0}'>
            http://192.168.43.206:27200/eleve/{0}</a></h3>
            <div align=center>{3}</div>
            """.format(password, formaTime(end), realTime, linkeleve)
    })


@route("/eleve/<secret>")
@route("/eleve/<secret>/<secretprof>")
def resultateleve(secret, secretprof=None):

    res = eleveGetResult(secret)

    id = res[0]
    html = res[1]
    count = res[2]

    if count < 0:

        count = 0

    name = res[3]
    tstamp = res[5]

    k = getQcmFromSQL(id)

    total = k[5]

    end = k[4]

    if secretprof is not None:

        pio = profIsOwner(id, secretprof)

    else:

        pio = False

    if pio == False and end > time.time():

        return template('page.html', {
            'titre':
                'OpenQCM',
                'body':
                "<h1 align=center>OpenQCM</h1></br>{1}<h3 align=center>Vos résultats seront disponibles à partir du {0}</h3>".
                format(formaTime(end), realTime)
        })

    ht = """<h1 align=center>OpenQCM</h1></br>
		<h3 align=center>Résultats de {0}</h3></br>
		<h3 align=center>QCM {1}, validé le {2}</h3></br>
		{3}
		<h3 align=center>Score: {4} / {5}</h3>""".format(name, id,
                                                   formaTime(tstamp), html,
                                                   count, total)

    return template('page.html', {'titre': 'OpenQCM', 'body': ht})


@route("/prof/<id>/<secret>")
def resultatprof(id, secret):

    if profIsOwner(id, secret):

        res = profGetResult(id)

        qcm = getQcmFromSQL(id)

        start = qcm[3]
        end = qcm[4]

        alerte = "Toutes les données relatives à ce QCM seront détruites 10 jours après la fin de validité du QCM.</br>Pensez à télécharger les résultats de vos élèves avant le {0}".format(
            formaTime(end + 864000))

        total = qcm[5]

        # creat df for excel

        d = {"Nom": (), "Score /100": (), "Horodatage": (), "Lien": ()}

        df = pd.DataFrame(d)

        # creat table

        ht = '<table style="width:100%; border:1px solid black; border-collapse:collapse;"><tr><th>Nom</th><th>Score /100</th><th>Horodatage</th><th>Lien</th></tr>'

        for i in res:

            score = i[2]

            if score < 0:

                score = 0

            score = round((score / total) * 100, 2)

            lien = "http://192.168.43.206:27200/eleve/{0}/{1}".format(
                i[4], secret)

            horo = formaTime(i[5])

            raw = pd.DataFrame(
                [(i[3], score, horo, lien)],
                columns=("Nom", "Score /100", "Horodatage", "Lien"))

            df = df.append(raw)

            ht += '<tr><td>{0}</td> <td>{1}</td> <td>{2}</td> <td>{3}</td></tr>'.format(
                i[3], score, horo, "<a href='{0}'>Voir la copie</a>".format(lien))

        ht += "</table>"

        ht = ht.replace(
            "<th>",
            '<th style="text-align:center; border:1px solid black;">')
        ht = ht.replace(
            "<td>",
            '<td style="text-align:center; border:1px solid black;">')

        # remove old xlsx and zip

        xlsx2remove = glob.glob('./static/*.xlsx')
        zip2remove = glob.glob('./static/*.zip')

        for x in xlsx2remove:
            try:
                os.remove(x)
            except OSError as e:
                pass

        for z in zip2remove:
            try:
                os.remove(z)
            except OSError as e:
                pass

        # creat excel
        df.to_excel('./static/{0}.xlsx'.format(secret))

        # zip xlsx

        zip = zipfile.ZipFile(
            './static/{0}.zip'.format(secret),
            mode="w",
            compression=zipfile.ZIP_DEFLATED)

        zip.write('./static/{0}.xlsx'.format(secret))
        zip.close

        xl = """<a href="/static/{0}.zip">Télécharger au format .xlsx</a>""".format(
            secret)

        # intro

        t = time.time()

        if start > t:

            intro = '<h5 align=center>Ce QCM sera ouvert aux élèves du {0} au {1}</h5>'.format(
                    formaTime(start), formaTime(end))

            lientest = 'http://192.168.43.206:27200/getqcm/{0}/{1}'.format(
                id, secret)
            lientest = """<a href="{0}">{1}</a>""".format(
                lientest, 'Tester le QCM')

        elif end > t:

            intro = '<h5 align=center>Ce QCM est ouvert aux élèves jusqu’au {0}. Des résultats peuvent encore arriver !</h5>'.format(
                    formaTime(end))

            lientest = 'http://192.168.43.206:27200/getqcm/{0}/{1}'.format(
                id, secret)
            lientest = """<a href="{0}">{1}</a>""".format(
                lientest, 'Tester le QCM')

        else:  # QCM terminé

            intro = '<h5 align=center>{0} - {1}</h5>'.format(
                    formaTime(start), formaTime(end))

            lientest = 'Ce QCM n’est plus actif.'

        return template('page.html', {
            'titre':
                'OpenQCM',
                'body':
                """<h1 align=center>OpenQCM</h1></br>{4}</br><h3 align=center>QCM {0}</h3>{3}<p align=center>{5}</p></br><div align=center>{1}</div></br><p align=center>{2}</p><p align=center>{6}</p>""".
                format(id, ht, xl, intro, realTime, lientest, alerte)
        })

    else:

        return template(
            'page.html',
            {
                'titre': 'OpenQCM',
                'body': """<h1 align=center>OpenQCM</h1></br><h3 align=center>Vos identifiants sont incorrectes !</h3>"""})


run(host='0.0.0.0', port=27200, reload=True, debug=True)
# application = default_app()
