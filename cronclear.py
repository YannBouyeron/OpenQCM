from sqlite3 import *
import time

# Supprime toutes les entrées correspondant à un QCM terminé depuis plus de 10 jours


t = time.time()


conn = connect("data.txt")

cur = conn.cursor()

cur.execute("SELECT id from qcm WHERE end > ?", (t - 86400,))

id2del = cur.fetchall()


for i in id2del:

    k = i[0]

    cur.execute("DELETE from qcm WHERE id = ?", (k,))
    conn.commit()

    cur.execute("DELETE from reponses WHERE id = ?", (k,))
    conn.commit()
