import csv
from datetime import datetime
from typing import List
from readers import Release


class CSVParser:
    def export_releases(self, releases: List[Release], filename=None):
        if not filename:
            filename = f"{self.folder}{datetime.now()}.csv"

        with open(filename, "w", newline="") as file:
            writer = csv.writer(file)
            data = [
                [
                    "Data",
                    "Valor",
                    "Débito",
                    "Crédito",
                    "Complemento",
                ]
            ]
            data.extend(
                [
                    [
                        r.date,
                        r.value,
                        "?",
                        "?",
                        r.detail or r.destiny,
                        "",
                    ]
                    for r in releases
                ]
            )

            writer.writerows(data)
