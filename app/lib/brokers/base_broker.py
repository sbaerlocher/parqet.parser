from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class BaseBroker(ABC):
    """
    Abstrakte Basis-Klasse für Broker. Diese Klasse definiert die Schnittstelle,
    die alle Broker-Implementierungen umsetzen müssen.
    """

    @abstractmethod
    def detect(self, file_path: str, file_content: Optional[str] = None) -> bool:
        """
        Erkennt, ob eine Datei zu diesem Broker gehört.
        :param file_path: Pfad zur Eingabedatei.
        :param file_content: Optionaler Inhalt der Datei (z. B. für PDF-Parsing).
        :return: True, wenn die Datei zu diesem Broker gehört, sonst False.
        """
        pass

    @abstractmethod
    def extract_transactions(self, file_path: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extrahiert Transaktionen aus der Broker-Datei.
        :param file_path: Pfad zur Eingabedatei.
        :return: Dictionary von Transaktionen kategorisiert nach Typ.
        """
        pass

    @abstractmethod
    def process_transactions(
        self, transactions: Dict[str, List[Dict[str, Any]]], file_path: Optional[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Verarbeitet die extrahierten Transaktionen und sortiert sie in Kategorien.
        :param transactions: Dictionary von Transaktionen als Dictionaries.
        :param file_path: Optionaler Pfad zur Ursprungsdatei (z. B. für Logging oder Fehlerberichte).
        :return: Verarbeitete Daten nach Kategorien.
        """
        pass

    def move_and_rename_file(
        self, file_path: str, transactions: Dict[str, List[Dict[str, Any]]]
    ) -> None:
        """
        Standardimplementierung: Verschiebt und benennt die Datei um, basierend auf den extrahierten Transaktionen.
        Diese Methode kann von Unterklassen überschrieben werden.

        :param file_path: Pfad zur Eingabedatei.
        :param transactions: Dictionary der extrahierten Transaktionen zur Generierung des Zielpfads.
        :return: None
        """
        pass

    @abstractmethod
    def generate_output_file(self, category: str, file_path: str) -> str:
        """
        Generiert den Namen der Ausgabedatei basierend auf der Kategorie und dem Ursprungsdateipfad.
        :param category: Kategorie der Daten (z. B. "deposits").
        :param file_path: Ursprungsdateipfad.
        :return: Dateiname der Ausgabedatei.
        """
        pass
