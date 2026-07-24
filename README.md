# EnleveFond 🖼️✂️

**Enlève le fond de vos images en quelques clics, sur votre ordinateur, gratuitement.**

Pas de site web chiant, pas de compte, pas de pub, pas de limite. Vous
double-cliquez, vous choisissez vos images, et c'est fait. Le tout
fonctionne **hors-ligne** grâce à un modèle d'intelligence artificielle
(`u2net`) qui tourne directement sur votre PC.

---

## ✨ Ce que ça fait

- Sélection d'**une ou plusieurs** images à la fois.
- Détourage automatique par IA (gère les contours, cheveux, etc.).
- Range tout proprement dans un dossier que **vous nommez** :
  ```
  MonDossier/
    ├── Images/   → les PNG (fond transparent)
    └── SVG/      → les mêmes images en .svg
  ```
- Nom de dossier pré-rempli avec la date/heure : appuyez sur **Entrée**
  pour aller vite, ou tapez le vôtre.

## 🔒 Confidentialité

Vos images **ne quittent jamais votre ordinateur**. Le logiciel ne fait
aucun envoi de données. La seule connexion internet nécessaire, c'est
**au tout premier lancement**, pour télécharger une seule fois le modèle
d'IA (~170 Mo). Ensuite, tout fonctionne sans internet.

## 🚀 Installation (Windows)

1. Installez **Python** depuis <https://www.python.org/downloads/>
   (cochez bien **« Add Python to PATH »** pendant l'installation).
2. Téléchargez ce projet (bouton vert **Code → Download ZIP**) et
   décompressez-le.
3. Double-cliquez sur **`installer.bat`** et laissez-le finir.
4. Votre logiciel est créé dans le sous-dossier **`dist`** :
   `EnleveFond.exe`.

Astuce : clic droit sur `EnleveFond.exe` → *Envoyer vers* → *Bureau
(créer un raccourci)*.

## 🖱️ Utilisation

1. Double-cliquez sur `EnleveFond.exe`.
2. Sélectionnez une ou plusieurs images (Ctrl+clic pour plusieurs).
3. Choisissez l'emplacement de sortie.
4. Donnez un nom au dossier (ou Entrée pour le nom proposé).
5. C'est fait — le dossier s'ouvre tout seul avec vos images détourées.

## 🧩 Comment ça marche (technique)

- Interface : `tkinter` (inclus avec Python).
- IA : modèle **u2net** exécuté via **onnxruntime**.
- Traitement d'image : **Pillow** + **numpy**.
- Le `.exe` est construit avec **PyInstaller**.

Aucune donnée n'est collectée, aucun serveur externe n'est contacté
(hors le téléchargement unique du modèle).

## 🙏 Crédits

- Modèle **U²-Net** — Qin et al. (recherche open-source).
- Le fichier `u2net.onnx` est récupéré depuis les *releases* du projet
  [rembg](https://github.com/danielgatis/rembg).

## 📄 Licence

Distribué sous licence **MIT** — voir le fichier [LICENSE](LICENSE).
Vous pouvez l'utiliser, le modifier et le partager librement.
