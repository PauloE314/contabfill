import csv
from datetime import datetime
from dataclasses import dataclass, field
import os
import re
from typing import Callable
import pypdf


@dataclass
class Entry:
    date: str
    raw_value: str
    destiny: str
    tax: str = field(default="")
    fines: str = field(default="")
    total: str = field(default="")
    detail: str = field(default="")

    def __post_init__(self):
        if self.total == "":
            self.total = self.raw_value


class BaseHandler:
    @classmethod
    def generate_entries(
        cls,
        date=None,
        raw_value=None,
        destiny=None,
        tax=None,
        fines=None,
        total=None,
        detail=None,
    ):
        if tax or fines:
            return [
                Entry(
                    date=date,
                    destiny=destiny,
                    raw_value=None,
                    total=total,
                    detail=detail,
                ),
                Entry(
                    date=date,
                    destiny=destiny,
                    raw_value=raw_value,
                    total=None,
                    detail=detail,
                ),
                Entry(
                    date=date,
                    destiny=destiny,
                    raw_value=None,
                    tax=tax,
                    fines=fines,
                    total=None,
                    detail=detail,
                ),
            ]

        return [Entry(date=date, raw_value=raw_value, destiny=destiny, detail=detail)]

    @classmethod
    def safe_re(cls, expression, content, position=0):
        result = re.findall(expression, content)
        return result[position] if result else None


class BradescoHandler(BaseHandler):
    DESTINY_RE = r"(.+)Nome:"
    DATE_RE = r"Data da operação: (.+)"
    RAW_VALUE_RE = r"(.+)Valor:"

    @classmethod
    def handle(cls, page: pypdf.PageObject):
        content = page.extract_text()
        method = re.search(r"Comprovante de Transação Bancária\n(.+)", content).group(1)

        match method.lower():
            case "pix":
                return BradescoHandler.pix(content)
            case "imposto/taxas":
                return BradescoHandler.tax(content)
            case "pagamento de folha":
                return BradescoHandler.payment(content)
            case _:
                raise ValueError(f"Receipt type is incorrect - {page}")

    @classmethod
    def pix(cls, content: str):
        return cls.generate_entries(
            date=cls.safe_re(cls.DATE_RE, content),
            raw_value=cls.safe_re(cls.RAW_VALUE_RE, content),
            destiny=cls.safe_re(cls.DESTINY_RE, content),
            detail=cls.safe_re(r"(.*)Descrição:", content),
        )

    @classmethod
    def tax(cls, content: str):
        return cls.generate_entries(
            date=cls.safe_re(cls.DATE_RE, content),
            raw_value=cls.safe_re(r"(R\$ \d+,\d\d)Valor principal:", content),
            total=cls.safe_re(r"(R\$ \d+,\d\d)Valor do pagamento:", content),
            tax=cls.safe_re(r"(R\$ \d+,\d\d)Juros:", content),
            fines=cls.safe_re(r"(R\$ \d+,\d\d)Multa:", content),
            destiny=cls.safe_re(r"Descrição:(.*)\nEmpresa \/ Órgão:", content),
            detail=cls.safe_re(r"REFERENCIA:(.*)Descrição:", content),
        )

    @classmethod
    def payment(cls, content: str):
        return cls.generate_entries(
            date=cls.safe_re(cls.DATE_RE, content),
            raw_value=cls.safe_re(cls.RAW_VALUE_RE, content),
            destiny=cls.safe_re(r"(.+)Favorecido:", content),
        )


class StoneHandler(BaseHandler):
    @classmethod
    def handle(cls, page: pypdf.PageObject):
        content = page.extract_text()

        date = cls.safe_re(r"no dia (.+)", content)
        raw_value = cls.safe_re(r"(R\$ \d+\.?\d+,\d+)", content)
        destiny = cls.safe_re(r"Nome\n(.+)", content, 1)

        return cls.generate_entries(date, raw_value, destiny)


def extract_entries_from_pdf(path, handler: Callable):
    reader = pypdf.PdfReader(path)
    entries = []

    for page in reader.pages:
        entries.extend(handler(page))

    return entries


def get_pdf_paths_from_folder(folder):
    absolute_folder = os.path.join(os.path.dirname(__file__), folder)
    file_paths = []

    for filename in os.listdir(absolute_folder):
        path = os.path.join(absolute_folder, filename)

        if os.path.isfile(path) and path.endswith(".pdf"):
            file_paths.append(path)

    return file_paths


def export_to_csv(entries: list[Entry]):
    with open(f"./output/{datetime.now()}.csv", "w", newline="") as file:
        writer = csv.writer(file)
        data = [
            [
                "Data",
                "Valor Bruto",
                "Juros",
                "Multa",
                "Valor Total",
                "Conta Crédito",
                "Conta Débito",
            ]
        ]
        data.extend(
            [
                [
                    r.date,
                    r.raw_value,
                    r.tax,
                    r.fines,
                    r.total,
                    r.detail or r.destiny,
                    "",
                ]
                for r in entries
            ]
        )

        writer.writerows(data)


def main():
    entries = []

    for path in get_pdf_paths_from_folder("./examples/Bradesco"):
        entries.extend(extract_entries_from_pdf(path, BradescoHandler.handle))

    for path in get_pdf_paths_from_folder("./examples/Stone"):
        entries.extend(extract_entries_from_pdf(path, StoneHandler.handle))

    export_to_csv(entries)


if __name__ == "__main__":
    main()
