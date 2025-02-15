from abc import ABC, abstractmethod
import csv
from datetime import datetime
import re
from typing import List, Tuple
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


class Parser(ABC):
    DEFAULT_EXTENSION: str
    FILE_TYPES: tuple[tuple[str, str]]

    @abstractmethod
    def export_releases(self, releases: List[Release], filename: str = ""):
        pass


class CSVParser(Parser):
    DEFAULT_EXTENSION = ".csv"
    FILE_TYPES = (("CSV", "*.csv"),)
    codes_provider: CodesProvider

    def __init__(self):
        super()
        self.codes_provider = CodesProvider()

    def export_releases(self, releases: List[Release], filename=None, codes_path=None):
        if not filename:
            filename = f"{datetime.now()}.csv"

        if codes_path:
            self.codes_provider.set_codes_relation_from_json(codes_path)

        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            rows = []

            for release in releases:
                rows.extend(self.__generate_release_rows(release))

            writer.writerows(
                [
                    (
                        "Data",
                        "Valor",
                        "Débito",
                        "Crédito",
                        "Complemento",
                        "Localização",
                    ),
                    *rows,
                ]
            )

    def __generate_release_rows(
        self, release: Release
    ) -> List[Tuple[str, str, str, str, str, str]]:
        tax_value = currency_to_cents(release.tax) if release.tax else 0
        fines_value = currency_to_cents(release.fines) if release.fines else 0
        total_tax_fines = cents_to_currency(tax_value + fines_value)

        real_destiny = release.detail or release.destiny

        credit = str(self.codes_provider.credit(release.bank) or "")
        debit = str(self.codes_provider.debit(real_destiny) or "")

        location = (
            f"{release.origin_file_and_page[0]} - {release.origin_file_and_page[1]}"
        )

        if tax_value or fines_value:
            return [
                (
                    release.date,
                    release.value,
                    debit,
                    "",
                    real_destiny,
                    location,
                ),
                (
                    release.date,
                    total_tax_fines,
                    debit,
                    "",
                    real_destiny,
                    location,
                ),
                (
                    release.date,
                    release.total,
                    "",
                    credit,
                    real_destiny,
                    location,
                ),
            ]

        return [
            (
                release.date,
                release.value,
                debit,
                credit,
                real_destiny,
                location,
            ),
        ]
