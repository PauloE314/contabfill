import csv
from datetime import datetime
from dataclasses import dataclass, field
import locale
import os
import re
from typing import Callable
import pypdf


@dataclass
class Entry:
    date: str
    raw_value: str
    destiny: str
    tax: str = field(default="R$ 0,00")
    fines: str = field(default="R$ 0,00")
    total: str = field(default="")
    detail: str = field(default="")

    def __post_init__(self):
        if self.total == "":
            self.total = self.raw_value


class BaseHandler:
    @classmethod
    def generate_entries(
        cls,
        date: str = None,
        raw_value: str = None,
        destiny: str = None,
        tax: str = None,
        fines: str = None,
        total: str = None,
        detail: str = None,
    ):
        if (tax and not cls.is_zero_currency(tax)) or (
            fines and not cls.is_zero_currency(fines)
        ):
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
    def is_zero_currency(cls, value):
        number_list = map(lambda n: int(n), re.findall(r"\d", value))
        return sum(number_list) == 0

    @classmethod
    def safe_re(cls, expression, content, position=0):
        result = re.findall(expression, content)
        return result[position] if result else None


class BradescoHandler(BaseHandler):
    DESTINY_RE = r"(.+)Nome:"
    DATE_RE = r"Data da operação: (\d\d\/\d\d\/\d\d\d\d)"
    RAW_VALUE_RE = r"(.+)Valor:?"

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
            case "boleto de cobrança":
                return BradescoHandler.charge(content)
            case _:
                raise ValueError(f"Tipo incorreto de boleto")

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
            detail=cls.safe_re(r"(.*)Finalidade:", content),
        )

    @classmethod
    def charge(cls, content: str):
        return cls.generate_entries(
            date=cls.safe_re(cls.DATE_RE, content),
            destiny=cls.safe_re(r"(.*)Nome Fantasia", content),
            raw_value=cls.safe_re(cls.RAW_VALUE_RE, content),
            total=cls.safe_re(r"(.*)Valor total", content),
            tax=cls.safe_re(r"(.*)Juros", content),
            fines=cls.safe_re(r"(.*)Multa", content),
            detail=cls.safe_re(r"(.*)Descrição", content),
        )


class StoneHandler(BaseHandler):
    @classmethod
    def handle(cls, page: pypdf.PageObject):
        content = page.extract_text()

        date = cls.safe_re(r"no dia (\d\d? de \w+ de \d\d\d\d)", content)
        if date:
            date = datetime.strptime(date, "%d de %B de %Y").strftime("%d/%m/%Y")

        raw_value = cls.safe_re(r"(R\$ \d+\.?\d+,\d+)", content)
        destiny = cls.safe_re(r"Nome\n(.+)", content, 1)

        return cls.generate_entries(date, raw_value, destiny)


def extract_entries_from_pdf(path, handler: Callable):
    reader = pypdf.PdfReader(path)
    entries = []

    print(f"======Processando aquivo: {path}=======")
    for i, page in enumerate(reader.pages, 1):
        try:
            entries.extend(handler(page))
            print(f"Página {i} processada com sucesso")
        except Exception as e:
            print(f"Ocorreu um erro na página {i} do arquivo - {e}")

    return entries


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


def get_pdf_paths_from_folder(folder):
    absolute_folder = os.path.join(os.path.dirname(__file__), folder)
    file_paths = []

    for filename in os.listdir(absolute_folder):
        path = os.path.join(absolute_folder, filename)

        if os.path.isfile(path) and path.endswith(".pdf"):
            file_paths.append(path)

    return file_paths


def main():
    locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")

    entries = []

    for path in get_pdf_paths_from_folder("./examples/Bradesco"):
        entries.extend(extract_entries_from_pdf(path, BradescoHandler.handle))

    for path in get_pdf_paths_from_folder("./examples/Stone"):
        entries.extend(extract_entries_from_pdf(path, StoneHandler.handle))

    export_to_csv(entries)


if __name__ == "__main__":
    main()
