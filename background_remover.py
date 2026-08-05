# -*- coding: utf-8 -*-
"""
EnleveFond - Enleve le fond des images en quelques clics.

N'utilise NI rembg NI pymatting. Modele d'IA "u2net" via onnxruntime.
Dependances : onnxruntime, numpy, pillow.

Fonctionnement :
  1. On lance le programme (le .exe).
  2. Fenetre Windows : on selectionne UNE ou PLUSIEURS images.
  3. Fenetre Windows : on choisit l'EMPLACEMENT de sortie.
  4. Petite fenetre : on donne un NOM au dossier de sortie
     (pre-rempli avec la date/heure ; Entree pour valider).
  5. Le logiciel cree :
        <Nom>/
          |- Images/   (tous les PNG transparents)
          |- SVG/      (tous les SVG)
     puis enleve le fond et range tout automatiquement.
"""

import os
import sys
import base64
import traceback
import datetime
import urllib.request

import tkinter as tk
from tkinter import filedialog, messagebox, ttk


EXT_IMAGES = ("*.png", "*.jpg", "*.jpeg", "*.bmp", "*.webp", "*.tiff", "*.tif")

MODEL_URL = "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx"
MODEL_NOM = "u2net.onnx"
TAILLE_MODELE = 320
MEAN = (0.485, 0.456, 0.406)
STD = (0.229, 0.224, 0.225)


# ----------------------------------------------------------------------
# Utilitaires
# ----------------------------------------------------------------------
def dossier_programme():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def log_erreur(texte):
    try:
        chemin = os.path.join(dossier_programme(), "EnleveFond_erreur.txt")
        with open(chemin, "w", encoding="utf-8") as f:
            f.write(texte)
    except Exception:
        pass


def message_erreur(titre, texte):
    log_erreur(titre + "\n\n" + texte)
    try:
        r = tk.Tk()
        r.withdraw()
        messagebox.showerror(titre, texte)
        r.destroy()
    except Exception:
        pass


def chemin_modele():
    d = os.path.join(os.path.expanduser("~"), ".u2net")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    return os.path.join(d, MODEL_NOM)


def nettoyer_nom(nom):
    """Enleve les caracteres interdits par Windows."""
    for c in '\\/:*?"<>|':
        nom = nom.replace(c, "-")
    nom = nom.strip().strip(".")
    return nom or "Sans_fond"


def dossier_unique(chemin):
    """Si le dossier existe deja, ajoute _2, _3, ... pour ne rien ecraser."""
    if not os.path.exists(chemin):
        return chemin
    n = 2
    while os.path.exists("%s_%d" % (chemin, n)):
        n += 1
    return "%s_%d" % (chemin, n)


def faire_svg(png_bytes, largeur, hauteur, chemin_svg):
    """SVG 'image' : contient la photo PNG transparente (format d'origine)."""
    b64 = base64.b64encode(png_bytes).decode("ascii")
    svg = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'xmlns:xlink="http://www.w3.org/1999/xlink" '
        'width="{w}" height="{h}" viewBox="0 0 {w} {h}">\n'
        '  <image width="{w}" height="{h}" '
        'xlink:href="data:image/png;base64,{b64}"/>\n'
        '</svg>\n'
    ).format(w=largeur, h=hauteur, b64=b64)
    with open(chemin_svg, "w", encoding="utf-8") as fh:
        fh.write(svg)


def _seuil_otsu(np, gris):
    """Trouve automatiquement le seuil noir/blanc (methode d'Otsu)."""
    hist, _ = np.histogram(gris, bins=256, range=(0, 256))
    total = gris.size
    somme = float(np.dot(np.arange(256), hist))
    sumB = 0.0
    wB = 0
    maxv = 0.0
    seuil = 127
    for t in range(256):
        wB += hist[t]
        if wB == 0:
            continue
        wF = total - wB
        if wF == 0:
            break
        sumB += t * hist[t]
        mB = sumB / wB
        mF = (somme - sumB) / wF
        entre = wB * wF * (mB - mF) ** 2
        if entre > maxv:
            maxv = entre
            seuil = t
    return seuil


def vectoriser_svg(np, image_rgba, largeur, hauteur, chemin_svg):
    """SVG VECTORIEL detaille : trace le TRAIT NOIR de l'image (encre), en
    gardant les zones blanches comme des trous. Conserve tous les details
    (ideal dessins au trait, cliparts, gravure, decoupe, impression)."""
    import potrace
    from PIL import Image

    # Fond transparent -> blanc, puis niveaux de gris
    fond = Image.new("RGBA", (largeur, hauteur), (255, 255, 255, 255))
    fond.alpha_composite(image_rgba)
    gris = np.asarray(fond.convert("L"))

    seuil = _seuil_otsu(np, gris)
    seuil = max(60, min(200, seuil))  # garde-fou
    encre = gris < seuil  # l'encre = pixels sombres

    # Dans potracer, on inverse pour que l'encre soit tracée "pleine".
    bmp = potrace.Bitmap(~encre)
    chemin = bmp.trace(turdsize=2, alphamax=1.0)

    def P(pt):
        return "%.2f,%.2f" % (pt.x, pt.y)

    d = []
    for courbe in chemin:
        d.append("M" + P(courbe.start_point))
        for seg in courbe.segments:
            if seg.is_corner:
                d.append("L" + P(seg.c) + " L" + P(seg.end_point))
            else:
                d.append("C" + P(seg.c1) + " " + P(seg.c2) + " " + P(seg.end_point))
        d.append("Z")

    svg = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
        'viewBox="0 0 %d %d">\n'
        '  <path d="%s" fill="#000000" fill-rule="evenodd"/>\n'
        '</svg>\n'
        % (largeur, hauteur, largeur, hauteur, " ".join(d))
    )
    with open(chemin_svg, "w", encoding="utf-8") as fh:
        fh.write(svg)


# ----------------------------------------------------------------------
# Micro-interface : nommage rapide du dossier
# ----------------------------------------------------------------------
def demander_nom(root, defaut):
    """Petite fenetre pour nommer le dossier. Retourne le nom ou None."""
    dlg = tk.Toplevel(root)
    dlg.title("Nom du dossier de sortie")
    dlg.geometry("440x190")
    dlg.resizable(False, False)
    dlg.attributes("-topmost", True)

    tk.Label(dlg, text="Nom du dossier de sortie :",
             anchor="w", font=("Segoe UI", 10, "bold")).pack(
        padx=18, pady=(20, 2), fill="x")

    var = tk.StringVar(value=defaut)
    entry = tk.Entry(dlg, textvariable=var, width=50, font=("Segoe UI", 10))
    entry.pack(padx=18, pady=4)
    entry.select_range(0, tk.END)
    entry.icursor(tk.END)
    entry.focus_set()

    tk.Label(dlg, text="Astuce : appuyez sur Entree pour valider le nom propose.",
             fg="#666666", anchor="w").pack(padx=18, pady=(2, 2), fill="x")
    tk.Label(dlg, text="Deux sous-dossiers seront crees dedans : Images et SVG.",
             fg="#666666", anchor="w").pack(padx=18, pady=(0, 6), fill="x")

    res = {"nom": None}

    def valider(*_):
        res["nom"] = var.get()
        dlg.destroy()

    def annuler(*_):
        res["nom"] = None
        dlg.destroy()

    cadre = tk.Frame(dlg)
    cadre.pack(pady=6)
    tk.Button(cadre, text="Valider", width=14, command=valider).pack(side="left", padx=8)
    tk.Button(cadre, text="Annuler", width=14, command=annuler).pack(side="left", padx=8)

    dlg.bind("<Return>", valider)
    dlg.bind("<Escape>", annuler)
    dlg.grab_set()
    root.wait_window(dlg)
    return res["nom"]


# ----------------------------------------------------------------------
# Traitement IA
# ----------------------------------------------------------------------
def telecharger_modele(chemin, maj_texte):
    if os.path.exists(chemin) and os.path.getsize(chemin) > 1_000_000:
        return

    def _progression(bloc, taille_bloc, taille_totale):
        if taille_totale > 0:
            pct = min(100, int(bloc * taille_bloc * 100 / taille_totale))
            maj_texte("Telechargement du modele d'IA (une seule fois) : %d%%" % pct)

    tmp = chemin + ".part"
    urllib.request.urlretrieve(MODEL_URL, tmp, _progression)
    os.replace(tmp, chemin)


def enlever_fond(session, np, image_pil):
    from PIL import Image

    rgb = image_pil.convert("RGB")
    largeur, hauteur = rgb.size

    petit = rgb.resize((TAILLE_MODELE, TAILLE_MODELE), Image.LANCZOS)
    arr = np.array(petit).astype(np.float32)
    maxi = arr.max()
    if maxi > 0:
        arr = arr / maxi
    tmp = np.zeros((TAILLE_MODELE, TAILLE_MODELE, 3), dtype=np.float32)
    tmp[:, :, 0] = (arr[:, :, 0] - MEAN[0]) / STD[0]
    tmp[:, :, 1] = (arr[:, :, 1] - MEAN[1]) / STD[1]
    tmp[:, :, 2] = (arr[:, :, 2] - MEAN[2]) / STD[2]
    tmp = tmp.transpose((2, 0, 1))
    entree = np.expand_dims(tmp, 0).astype(np.float32)

    nom_entree = session.get_inputs()[0].name
    sortie = session.run(None, {nom_entree: entree})[0]
    pred = sortie[:, 0, :, :]
    mini, maxi = pred.min(), pred.max()
    pred = (pred - mini) / (maxi - mini + 1e-8)
    pred = np.squeeze(pred)

    masque = Image.fromarray((pred * 255).astype("uint8"), mode="L")
    masque = masque.resize((largeur, hauteur), Image.LANCZOS)

    resultat = rgb.convert("RGBA")
    resultat.putalpha(masque)
    return resultat


# ----------------------------------------------------------------------
# Programme principal
# ----------------------------------------------------------------------
def main():
    try:
        import numpy as np
        import onnxruntime as ort
        import potrace  # noqa  (vectorisation)
        from PIL import Image  # noqa
    except Exception:
        message_erreur(
            "Modules manquants",
            "Les modules necessaires ne sont pas installes.\n\n"
            "Relancez 'installer.bat'.\n\nDetail :\n" + traceback.format_exc(),
        )
        return

    root = tk.Tk()
    root.withdraw()

    # ETAPE 1 : selection des images
    fichiers = filedialog.askopenfilenames(
        title="Selectionnez la ou les images (fond a enlever)",
        filetypes=[("Images", " ".join(EXT_IMAGES)), ("Tous les fichiers", "*.*")],
    )
    if not fichiers:
        return

    # ETAPE 2 : emplacement de sortie (dossier parent)
    emplacement = filedialog.askdirectory(
        title="Choisissez l'emplacement ou creer le dossier de sortie",
        mustexist=False,
    )
    if not emplacement:
        return

    # ETAPE 3 : nom du dossier (micro-interface)
    defaut = "Sans_fond_" + datetime.datetime.now().strftime("%Y-%m-%d_%Hh%M")
    nom = demander_nom(root, defaut)
    if nom is None:
        return
    nom = nettoyer_nom(nom)

    # Creation de la structure  <Nom>/Images  et  <Nom>/SVG
    try:
        dossier_projet = dossier_unique(os.path.join(emplacement, nom))
        dossier_images = os.path.join(dossier_projet, "Images")
        dossier_svg = os.path.join(dossier_projet, "SVG")
        dossier_vecto = os.path.join(dossier_projet, "SVG_Vectorise")
        os.makedirs(dossier_images, exist_ok=True)
        os.makedirs(dossier_svg, exist_ok=True)
        os.makedirs(dossier_vecto, exist_ok=True)
    except Exception as e:
        message_erreur("Erreur", "Impossible de creer les dossiers :\n%s" % e)
        return

    # Fenetre de progression
    prog = tk.Toplevel(root)
    prog.title("Traitement en cours...")
    prog.geometry("480x150")
    prog.resizable(False, False)
    prog.attributes("-topmost", True)
    lbl = tk.Label(prog, text="Preparation...", anchor="w", justify="left",
                   wraplength=450)
    lbl.pack(padx=15, pady=(18, 6), fill="x")
    barre = ttk.Progressbar(prog, length=450, mode="determinate",
                            maximum=max(1, len(fichiers)))
    barre.pack(padx=15, pady=6)
    lbl_compte = tk.Label(prog, text="")
    lbl_compte.pack(padx=15, pady=(0, 10))
    prog.update()

    def maj_texte(t):
        lbl.config(text=t)
        prog.update()

    # Modele
    try:
        chemin = chemin_modele()
        telecharger_modele(chemin, maj_texte)
        maj_texte("Chargement du moteur d'IA...")
        session = ort.InferenceSession(chemin, providers=["CPUExecutionProvider"])
    except Exception:
        prog.destroy()
        message_erreur(
            "Erreur (modele d'IA)",
            "Impossible de preparer le modele d'IA.\n\n"
            "Verifiez votre connexion internet (necessaire au 1er usage).\n\n"
            "Detail :\n" + traceback.format_exc(),
        )
        return

    reussites = 0
    erreurs = []

    for i, chemin_img in enumerate(fichiers, start=1):
        nom_img = os.path.basename(chemin_img)
        maj_texte("Traitement : %s" % nom_img)
        lbl_compte.config(text="%d / %d" % (i, len(fichiers)))
        prog.update()
        try:
            image = Image.open(chemin_img)
            resultat = enlever_fond(session, np, image)

            base = os.path.splitext(nom_img)[0]
            nom_fichier = base + "_sans_fond"
            chemin_png = os.path.join(dossier_images, nom_fichier + ".png")
            n = 1
            while os.path.exists(chemin_png):
                nom_fichier = "%s_sans_fond_%d" % (base, n)
                chemin_png = os.path.join(dossier_images, nom_fichier + ".png")
                n += 1
            resultat.save(chemin_png, "PNG")

            with open(chemin_png, "rb") as fh:
                png_bytes = fh.read()
            chemin_svg = os.path.join(dossier_svg, nom_fichier + ".svg")
            faire_svg(png_bytes, resultat.width, resultat.height, chemin_svg)

            # SVG vectoriel detaille (trait) pour impression/decoupe/gravure
            chemin_vecto = os.path.join(dossier_vecto, nom_fichier + ".svg")
            vectoriser_svg(np, resultat, resultat.width, resultat.height, chemin_vecto)

            reussites += 1
        except Exception as e:
            erreurs.append("%s : %s" % (nom_img, e))

        barre["value"] = i
        prog.update()

    prog.destroy()

    if erreurs:
        messagebox.showwarning(
            "Termine (avec des soucis)",
            "%d image(s) sur %d.\n\nDossier : %s\n\nImages en erreur :\n%s"
            % (reussites, len(fichiers), dossier_projet, "\n".join(erreurs[:10])),
        )
    else:
        messagebox.showinfo(
            "Termine !",
            "C'est fait : %d image(s) sans fond.\n\nDossier : %s\n"
            "   - Images/ : les PNG transparents\n"
            "   - SVG/ : les SVG image (photo)\n"
            "   - SVG_Vectorise/ : les SVG vectoriels (impression 3D / decoupe)"
            % (reussites, dossier_projet),
        )

    try:
        if reussites and os.name == "nt":
            os.startfile(dossier_projet)  # noqa
    except Exception:
        pass

    root.destroy()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        message_erreur("Erreur inattendue", traceback.format_exc())
