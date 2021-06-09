import markdown2
from xhtml2pdf import pisa
from xhtml2pdf.default import DEFAULT_CSS
import os


def mdht(md, ht=None):
    """convertion du fichier .md en .html

    Arguments:

            md: path du fichier md ou str
            ht: path de sortie du fichier html. (facultatif)

    Return:

            Si ht = None, la fonction retourne le html sous forme str
            Si un path est spécifié pour ht: la fonction crée un fichier.html et retourne en plus le html sous forme str

            Le html créé est brut, il ne contient pas de balises doctype, html, head, ni body.
            Pour obtenir un html structuré avec doctype html head style... utiliser la fonction mdhtml()

            Cette fonction est idéale en combinaison avec htpdf

    """

    DEFAULT_EXTRAS = [
        'fenced-code-blocks',
        'footnotes',
        'metadata',
        'pyshell',
        'smarty-pants',
        'wiki-tables']

    if os.path.isfile(md):

        html = markdown2.markdown_path(
            md,
            encoding="utf-8",
            html4tags=False,
            tab_width=4,
            safe_mode=None,
            extras=DEFAULT_EXTRAS,
            link_patterns=None,
            use_file_vars=False)

    elif isinstance(md, type(str())):

        html = markdown2.markdown(
            md,
            html4tags=False,
            tab_width=4,
            safe_mode=None,
            extras=DEFAULT_EXTRAS,
            link_patterns=None,
            use_file_vars=False)

    if ht is not None and ht != '':

        with open(ht, 'wb') as f:

            f.write(html.encode())
            f.close()

    return html


def mdhtml(md, ht=None, style='', href='', titre='Page'):
    """convertion du fichier .md en .html avec prise en charge du css et du titre de la page

    Arguments:

            md: path du fichier md.
            ht: path de sortie du fichier html. (facultatif)
            style: css qui sera incrusté directement dans la balise <style></style>. (facultatif)
            href: lien vers une page .css - incrusté dans la balise <link />. (facultatif)


            Si le titre n'est pas spécifié, et que le fichier .md contient Title dans ses meta, alors c'est le Title des meta qui sera utilisé comme titre de page.
            Si le titre n'est pas spécifié et que md est un str, le titre de la page html sera par default Page

            Pour ajouter un Title dans les meta de votre md, structurez votre md avec un entête comme ceci:

                    ---
                    Date:
                    Title:
                    Author:
                    Tags:
                    ---

            Ne pas oublier de faire un retour chariot apres les --- du bas


    Return:

            Si ht = None, la fonction retourne le html sous forme str
            Si un path est spécifié pour ht: la fonction crée un fichier.html et retourne en plus le html sous forme de str

            Le html créé est un html structuré avec doctype html head style

            Pour obtenir un html brut utilisez la fonction mdht()

            Cette fonction est idéale en combinaison avec htmlpdf

    """

    DEFAULT_EXTRAS = [
        'fenced-code-blocks',
        'footnotes',
        'metadata',
        'pyshell',
        'smarty-pants',
        'wiki-tables']

    if os.path.isfile(md):

        html = markdown2.markdown_path(
            md,
            encoding="utf-8",
            html4tags=False,
            tab_width=4,
            safe_mode=None,
            extras=DEFAULT_EXTRAS,
            link_patterns=None,
            use_file_vars=False)

        if titre == 'Page':

            metadata = html.metadata

            titre = metadata['Title']

    elif isinstance(md, type(str())):

        html = markdown2.markdown(
            md,
            html4tags=False,
            tab_width=4,
            safe_mode=None,
            extras=DEFAULT_EXTRAS,
            link_patterns=None,
            use_file_vars=False)

    # restructuration du html
    html = """<!doctype html><html><head><meta charset="utf-8"><title>{0}</title><link rel="stylesheet" href="{1}"/><style type="text/css">{2}</style></head><body>""".format(
        titre, href, style) + html + '</body></html>'

    if ht is not None and ht != '':

        with open(ht, 'wb') as f:

            f.write(html.encode())
            f.close()

    return html


def htpdf(html, pdf, css='', defo=DEFAULT_CSS):
    """Transforme un html non structuré (pas de doctype head html body) en pdf

    Arguments:

            html: path ou str du html
            pdf: path du pdf
            css: css qui sera ajouté au default_css
            defo: css adapté au format pdf - utilisé le DEFAULT_CSS de pisa

    Return:

            retourne un pdf

    """

    # recuperation du html depuis le file.html
    if os.path.isfile(html):

        with open(html, 'rb') as h:

            html = h.read().decode()

    # restucturation du html
    html = '<!doctype html><html><head><meta charset="utf-8"><title></title></head><body>' + \
        html + '</body></html>'

    # ecriture du pdf
    with open(pdf, 'wb') as p:

        pisa.CreatePDF(html.encode(), p, default_css=defo + css)


def htpdf2(html, pdf, href='', style='', css='', defo=DEFAULT_CSS):
    """Transforme un html non structuré (pas de doctype head html body) en pdf


    Arguments:

            html: path ou str du html
            pdf: path du pdf
            href: lien vers le .css qui sera ajouté dans la balise <link />
            style: css qui sera ajouté dans la balise <style></style>
            css: css qui sera ajouté au default_css
            defo: css adapté au format pdf - utilisé le DEFAULT_CSS de pisa

    Return:

            retourne le html structuré au format str
            création du pdf

    """

    css = defo + css

    # recuperation du html depuis le file.html
    if os.path.isfile(html):

        with open(html, 'rb') as h:

            html = h.read().decode()

    # restucturation du html
    html = '<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="{0}"/><style type="text/css">{1}</style><title></title></head><body>'.format(
        href, style) + html + '</body></html>'

    # ecriture du pdf
    with open(pdf, 'wb') as p:

        pisa.CreatePDF(html.encode(), p, default_css=css)

    return html


def htmlpdf(html, pdf, css=''):
    """Transforme un html déjà structuré (doctype head html body) en pdf


    Arguments:

            html: path ou str du html déjà structuré
            pdf: path du fichier pdf qui sera créé
            css: (type str) c'est le css qui sera ajouté au css par default de pisa
            Attention: le css de la balise style du html est prioritaire sur le css entré en argument !

    """

    # recuperation du html
    if os.path.isfile(html):

        with open(html, 'rb') as h:

            html = h.read().decode()

    if 'doctype' in html and 'head' in html and 'html' in html:

        # ecriture du pdf
        with open(pdf, 'wb') as p:

            pisa.CreatePDF(html.encode(), p, default_css=DEFAULT_CSS + css)


def mdpdf(md, pdf, css=''):
    """markdown to pdf"""

    h = mdht(md)

    htpdf(h, pdf, css=css)
