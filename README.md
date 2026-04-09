# Bibliothèque to Kindle

A simple app that removes Adobe DRM from library ebooks (EPUB and PDF) and sends them to your Kindle. Works on macOS and Windows.
<img width="449" height="339" alt="image" src="https://github.com/user-attachments/assets/6ac04d7b-ecb1-48aa-9994-fdf3af442eab" />


## How it works

1. Drop an `.acsm`, `.epub`, or `.pdf` file onto the app
2. If it's an ACSM, the app opens Adobe Digital Editions to download the book and waits for it to appear
3. DRM is removed using [DeDRM_tools](https://github.com/noDRM/DeDRM_tools)
4. The DRM-free file is saved to your configured output folder and your default email client opens with the Kindle address and file pre-filled — just click Send

If a borrowed book's loan has expired, the app will ask you to confirm you've deleted it from your Kindle library before letting you borrow another one.

## Installation

**[Download the latest release](https://github.com/labriedion/bibliotheque-to-kindle/releases/latest)**
— pick `BibliothequeToKindle.dmg` for macOS or `BibliothequeToKindle.exe` for Windows.

On first launch, click the ⚙ icon and enter your Kindle email address. Find it at:
**Amazon → Manage Your Content and Devices → Preferences → Personal Document Settings**

> **macOS — "App can't be opened" warning**
> Because the app is not signed with an Apple Developer certificate, macOS will block it on first launch. To open it:
> 1. Right-click (or Control-click) the app and choose **Open**
> 2. Click **Open** in the dialog that appears
>
> You only need to do this once. After that, the app opens normally.
>
> Alternatively: go to **System Settings → Privacy & Security**, scroll down, and click **Open Anyway** next to the blocked app.

## Requirements

- [Adobe Digital Editions](https://www.adobe.com/solutions/ebook/digital-editions/download.html) — installed and authorized with your library account
- An email client with at least one configured account:
  - **macOS**: Mail.app
  - **Windows**: Outlook, Thunderbird, Windows Mail, or any MAPI-compatible client

## Legal notice

This tool is intended for removing DRM from ebooks you have legitimately borrowed or purchased, for **personal use only**. Circumventing DRM may be restricted in your jurisdiction. Use responsibly.

**Please respect borrowing periods.** When a library loan expires, delete the book from your Kindle and your device, just as you would return a physical book. This tool should not be used to create permanent copies of borrowed books or to distribute them in any way. It exists solely to let you read books you have legitimately borrowed on your own Kindle, for the duration of the loan **only**.

This project includes code from [DeDRM_tools](https://github.com/noDRM/DeDRM_tools) by noDRM.

## License

GPL v3 — see [LICENSE](LICENSE).

---

# Bibliothèque to Kindle (Français)

Une application simple qui supprime le DRM Adobe des livres numériques empruntés à la bibliothèque (EPUB et PDF) et les envoie à votre Kindle. Fonctionne sur macOS et Windows.

## Comment ça marche

1. Déposez un fichier `.acsm`, `.epub` ou `.pdf` sur l'application
2. Si c'est un ACSM, l'application ouvre Adobe Digital Editions pour télécharger le livre et attend qu'il apparaisse
3. Le DRM est supprimé à l'aide de [DeDRM_tools](https://github.com/noDRM/DeDRM_tools)
4. Le fichier sans DRM est enregistré dans votre dossier de sortie configuré et votre client de messagerie s'ouvre avec l'adresse Kindle et le fichier déjà remplis — il suffit de cliquer Envoyer

Si le prêt d'un livre a expiré, l'application vous demandera de confirmer que vous l'avez supprimé de votre bibliothèque Kindle avant de vous permettre d'en emprunter un autre.

## Installation

**[Télécharger la dernière version](https://github.com/labriedion/bibliotheque-to-kindle/releases/latest)**
— choisissez `BibliothequeToKindle.dmg` pour macOS ou `BibliothequeToKindle.exe` pour Windows.

Au premier lancement, cliquez sur l'icône ⚙ et entrez votre adresse e-mail Kindle. Trouvez-la sur :
**Amazon → Gérer votre contenu et vos appareils → Préférences → Paramètres des documents personnels**

> **macOS — message « L'application ne peut pas être ouverte »**
> L'application n'étant pas signée avec un certificat Apple Developer, macOS la bloquera au premier lancement. Pour l'ouvrir :
> 1. Faites un clic droit (ou Contrôle-clic) sur l'application et choisissez **Ouvrir**
> 2. Cliquez sur **Ouvrir** dans la fenêtre qui apparaît
>
> Vous n'avez besoin de faire cela qu'une seule fois. Ensuite, l'application s'ouvre normalement.
>
> Sinon : allez dans **Réglages Système → Confidentialité et sécurité**, faites défiler vers le bas et cliquez sur **Ouvrir quand même** à côté de l'application bloquée.

## Prérequis

- [Adobe Digital Editions](https://www.adobe.com/solutions/ebook/digital-editions/download.html) — installé et autorisé avec votre compte de bibliothèque
- Un client de messagerie avec au moins un compte configuré :
  - **macOS** : Mail.app
  - **Windows** : Outlook, Thunderbird, Windows Mail ou tout client compatible MAPI

## Avis légal

Cet outil est destiné à supprimer le DRM des livres numériques que vous avez légitimement empruntés ou achetés, pour **usage personnel uniquement**. Le contournement du DRM peut être restreint dans votre juridiction. Utilisez de manière responsable.

**Veuillez respecter les périodes d'emprunt.** Lorsqu'un prêt de bibliothèque expire, supprimez le livre de votre Kindle et de votre appareil, tout comme vous retourneriez un livre physique. Cet outil ne doit pas être utilisé pour créer des copies permanentes de livres empruntés ni pour les distribuer de quelque façon que ce soit. Il existe uniquement pour vous permettre de lire sur votre propre Kindle des livres que vous avez légitimement empruntés, et ce, pendant la durée du prêt **seulement**.

Ce projet inclut du code de [DeDRM_tools](https://github.com/noDRM/DeDRM_tools) par noDRM.

## Licence

GPL v3 — voir [LICENSE](LICENSE).
