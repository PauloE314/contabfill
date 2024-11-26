from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Callable
import re
import pypdf
import logging


@dataclass
class Release:
    date: str
    value: str
    destiny: str
    detail: str = field(default="")


def safe_re(expression, content, position=0):
    result = re.findall(expression, content, re.M)
    return result[position] if result else None


def currency_to_cents(content: str):
    result = re.match(r"R?\$\s*(\d+(?:\d*(?:\.|,)\d*)?)(?:\.|,)(\d\d)", content)

    if not result:
        return 0

    whole, cents = result.groups()
    whole = whole.replace(",", "").replace(".", "")

    return int(whole) * 100 + int(cents)


def cents_to_currency(cents: int):
    return f"R$ {cents/100:,.2f}".replace(".", "t").replace(",", ".").replace("t", ",")


class BaseReader:
    BANK: str = "BASE"

    def __init__(self, page: pypdf.PageObject):
        self.page = page

    def handle(self) -> List[Release]:
        raise

    def generate_entries(
        self,
        date: str = None,
        value: str = None,
        destiny: str = None,
        tax: str = None,
        fines: str = None,
        total: str = None,
        detail: str = None,
    ):
        tax_value = currency_to_cents(tax) if tax else 0
        fines_value = currency_to_cents(fines) if fines else 0

        if tax_value or fines_value:
            return [
                Release(
                    date=date,
                    detail=detail,
                    destiny=destiny,
                    value=value,
                ),
                Release(
                    date=date,
                    detail=detail,
                    destiny=destiny,
                    value=cents_to_currency(tax_value + fines_value),
                ),
                Release(
                    date=date,
                    detail=detail,
                    destiny=destiny,
                    value=total,
                ),
            ]

        return [Release(date=date, value=value, destiny=destiny, detail=detail)]

    @classmethod
    def extract_releases(cls, path: str):
        pages = pypdf.PdfReader(path).pages
        releases = []

        logging.info(f"Aquivo: {path.split("/")[-1]}")
        for i, page in enumerate(pages, 1):
            try:
                releases.extend(cls(page).handle())

                logging.info(f"Página {i} processada com sucesso")
            except Exception as e:
                logging.error(f"Ocorreu um erro na página {i} do arquivo {path} - {e}")

        return releases


class BradescoReader(BaseReader):
    BANK = "Bradesco"
    DESTINY_RE = r"(.+)Nome:"
    DATE_RE = r"Data da operação: (\d{2}\/\d{2}\/\d{2})"
    VALUE_RE = r"(.+)Valor:"

    def handle(self):
        content = self.page.extract_text()
        method = re.search(r"Comprovante de Transação Bancária\n(.+)", content).group(1)

        match method.lower():
            case "pix":
                return self.pix(content)
            case "imposto/taxas":
                return self.tax(content)
            case "pagamento de folha":
                return self.payment(content)
            case "boleto de cobrança":
                return self.charge(content)
            case _:
                raise ValueError(f"Tipo incorreto de boleto")

    def pix(self, content: str):
        return self.generate_entries(
            date=safe_re(self.DATE_RE, content),
            value=safe_re(self.VALUE_RE, content),
            destiny=safe_re(self.DESTINY_RE, content),
            detail=safe_re(r"(.*)Descrição:", content),
        )

    def tax(self, content: str):
        return self.generate_entries(
            date=safe_re(self.DATE_RE, content),
            value=safe_re(r"(R\$ \d+,\d\d)Valor principal:", content),
            total=safe_re(r"(R\$ \d+,\d\d)Valor do pagamento:", content),
            tax=safe_re(r"(R\$ \d+,\d\d)Juros:", content),
            fines=safe_re(r"(R\$ \d+,\d\d)Multa:", content),
            destiny=safe_re(r"Descrição:(.*)\nEmpresa \/ Órgão:", content),
            detail=safe_re(r"REFERENCIA:(.*)Descrição:", content),
        )

    def payment(self, content: str):
        return self.generate_entries(
            date=safe_re(self.DATE_RE, content),
            value=safe_re(self.VALUE_RE, content),
            destiny=safe_re(r"(.+)Favorecido:", content),
            detail=safe_re(r"(.*)Finalidade:", content),
        )

    def charge(self, content: str):
        return self.generate_entries(
            date=safe_re(self.DATE_RE, content),
            destiny=safe_re(r"(.*)Nome Fantasia", content),
            value=safe_re(r"^(.*)Valor\s*$", content),
            total=safe_re(r"(.*)Valor total", content),
            tax=safe_re(r"(.*)Juros", content),
            fines=safe_re(r"(.*)Multa", content),
            detail=safe_re(r"(.*)Descrição", content),
        )


class StoneReader(BaseReader):
    BANK = "Stone"

    def handle(self):
        content = self.page.extract_text()

        date = safe_re(r"no dia (\d\d? de \w+ de \d\d\d\d)", content)
        if date:
            date = datetime.strptime(date, "%d de %B de %Y").strftime("%d/%m/%Y")

        value = safe_re(r"(R\$ \d+\.?\d+,\d+)", content)
        destiny = safe_re(r"Nome\n(.+)", content, 1)

        return self.generate_entries(date, value, destiny)


READER_LIST: List[type[BaseReader]] = [
    BradescoReader,
    StoneReader,
]

BANK_LIST = list(map(lambda Reader: Reader.BANK, READER_LIST))
