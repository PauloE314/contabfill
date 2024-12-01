import csv
import re
from datetime import datetime
from typing import List
from readers import Release
from codes_provider import CodesProvider


def currency_to_cents(content: str):
    result = re.match(r"R?\$\s*(\d+(?:\d*(?:\.|,)\d*)?)(?:\.|,)(\d\d)", content)

    if not result:
        return 0

    whole, cents = result.groups()
    whole = whole.replace(",", "").replace(".", "")

    return int(whole) * 100 + int(cents)


def cents_to_currency(cents: int):
    return f"R$ {cents/100:,.2f}".replace(".", "t").replace(",", ".").replace("t", ",")


class Parser:
    DEFAULT_EXTENSION: str
    FILE_TYPES: tuple[tuple[str, str]]

    def export_releases(self, releases: List[Release], filename: str = None):
        pass


class CSVParser(Parser):
    DEFAULT_EXTENSION = ".csv"
    FILE_TYPES = (("CSV", "*.csv"),)
    codes_provider: CodesProvider

    def __init__(self):
        super()
        self.codes_provider = CodesProvider()

    def export_releases(self, releases: List[Release], filename=None):
        if not filename:
            filename = f"{self.folder}{datetime.now()}.csv"

        with open(filename, "w", newline="") as file:
            writer = csv.writer(file)
            rows = []

            for release in releases:
                rows.extend(self.__generate_release_rows(release))

            writer.writerows(
                [
                    [
                        "Data",
                        "Valor",
                        "Débito",
                        "Crédito",
                        "Complemento",
                    ],
                    *rows,
                ]
            )

    def __generate_release_rows(self, release: Release) -> List[str]:
        tax_value = currency_to_cents(release.tax) if release.tax else 0
        fines_value = currency_to_cents(release.fines) if release.fines else 0

        real_destiny = release.detail or release.destiny

        if tax_value or fines_value:
            return [
                [
                    release.date,
                    release.value,
                    self.codes_provider.credit(real_destiny),
                    "",
                    real_destiny,
                ],
                [
                    release.date,
                    cents_to_currency(tax_value + fines_value),
                    "",
                    self.codes_provider.debit(real_destiny),
                    real_destiny,
                ],
                [
                    release.date,
                    release.total,
                    "",
                    "",
                    real_destiny,
                ],
            ]

        return [
            [
                release.date,
                release.value,
                self.codes_provider.credit(real_destiny),
                "",
                real_destiny,
            ],
        ]