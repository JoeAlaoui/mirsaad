"""
Couche d'accès aux données JSON.
- Lecture/écriture UTF-8
- Écriture atomique (fichier temporaire + remplacement)
- Backup automatique avant toute écriture destructive
"""
import json
import os
import shutil
from datetime import datetime


class JsonRepository:
    def __init__(self, filepath, backups_dir=None):
        self.filepath = filepath
        self.backups_dir = backups_dir

    def read(self):
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"Fichier introuvable : {self.filepath}")
        with open(self.filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def write(self, data, backup=True):
        """Écrit les données. Crée un backup préalable si backup=True et que le fichier existe déjà."""
        if backup and os.path.exists(self.filepath):
            self._create_backup()

        tmp_path = self.filepath + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, self.filepath)  # remplacement atomique

    def _create_backup(self):
        if not self.backups_dir:
            return None
        os.makedirs(self.backups_dir, exist_ok=True)
        base = os.path.splitext(os.path.basename(self.filepath))[0]
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        backup_path = os.path.join(self.backups_dir, f"{base}_{timestamp}.json")
        shutil.copy2(self.filepath, backup_path)
        return backup_path

    def list_backups(self):
        if not self.backups_dir or not os.path.exists(self.backups_dir):
            return []
        base = os.path.splitext(os.path.basename(self.filepath))[0]
        files = [f for f in os.listdir(self.backups_dir) if f.startswith(base)]
        return sorted(files, reverse=True)

    def restore_backup(self, backup_filename):
        backup_path = os.path.join(self.backups_dir, backup_filename)
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup introuvable : {backup_filename}")
        self._create_backup()  # sauvegarder l'état courant avant restauration
        shutil.copy2(backup_path, self.filepath)
