# Module Rapports - Documentation

Ce module gère deux types de rapports pour les stagiaires :
1. **Le rapport journalier des tâches** (Daily Task Report)
2. **Le rapport final de stage** (Final Internship Report)

---

## 🚀 API Endpoints

### 1. Rapport Journalier (`/api/rapports-journaliers/`)

* **GET `/api/rapports-journaliers/`** :
  * Si connecté en tant que **Stagiaire** : Retourne la liste de ses propres rapports journaliers.
  * Si connecté en tant que **RH / Manager / Admin** : Retourne la liste de tous les rapports de tous les stagiaires.
  * *Paramètres de filtrage optionnels* (pour RH/Manager/Admin) : `stagiaire_id`, `date_rapport` (ex: `?date_rapport=2026-06-19`).
* **POST `/api/rapports-journaliers/deposer/`** :
  * Permet au stagiaire connecté de générer et déposer son rapport journalier pour la date du jour.
  * **Corps de la requête** :
    ```json
    {
      "commentaire": "Commentaire libre facultatif..."
    }
    ```
  * **Comportement automatique** : Les tâches réalisées aujourd'hui (statut `terminee` et modifiées aujourd'hui) et les tâches en cours (statut différent de `terminee`) assignées au stagiaire sont automatiquement extraites de la base de données et enregistrées dans les champs structurés JSON `taches_realisees` et `taches_en_cours`. Le champ `depose` passe à `True`.

---

### 2. Rapport Final (`/api/rapports-finaux/`)

* **GET `/api/rapports-finaux/`** :
  * Si connecté en tant que **Stagiaire** : Récupère son rapport final.
  * Si connecté en tant que **RH / Manager / Admin** : Récupère les rapports finaux de tous les stagiaires.
* **POST `/api/rapports-finaux/`** :
  * Permet à un stagiaire d'uploader son rapport final en format PDF.
  * **Données de formulaire (multipart/form-data)** :
    * `fichier_path` : Le fichier PDF.
* **POST `/api/rapports-finaux/<id>/valider/`** (Réservé aux RH et Admins) :
  * Permet de valider ou refuser un rapport final.
  * **Corps de la requête** :
    ```json
    {
      "statut_validation": "valide", 
      "commentaire_rh": "Optionnel - commentaire de validation ou de refus"
    }
    ```
  * **Comportement automatique** :
    * Le statut du rapport final met à jour la fiche du stagiaire associé (`rapport_final_depose = True`, `rapport_final_statut = 'valide'|'refuse'`).
    * Si le statut est `valide`, la fiche du stagiaire est marquée comme `stage_valide = True`.
    * Une notification WhatsApp est automatiquement envoyée au stagiaire pour lui notifier la décision avec le commentaire éventuel.

---

## ⏰ Tâches Planifiées (Rappels de 17h)

Pour envoyer automatiquement un rappel WhatsApp aux stagiaires actifs n'ayant pas encore déposé leur rapport à 17h, exécutez la commande Django suivante via un planificateur de tâches (cron ou Windows Task Scheduler) :

```bash
python manage.py remind_daily_reports
```

La commande sélectionne tous les stagiaires dont le stage est actif à la date courante, vérifie s'ils ont un rapport soumis (`depose=True`) pour aujourd'hui, et envoie un message d'alerte WhatsApp aux retardataires.
