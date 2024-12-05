from datetime import datetime
from dataclasses import dataclass, field
from typing import List
import re
import logging
import pypdf
from codes_provider import CodesProvider


@dataclass
class Release:
    date: str
    destiny: str
    value: str
    detail: str = field(default="")
    total: str = field(default="")
    tax: str = field(default="")
    fines: str = field(default="")

    def __post_init__(self):
        if not self.total:
            self.total = self.value


def safe_re(expression, content, position=0):
    result = re.findall(expression, content, re.M)
    try:
        return result[position] if result else ""
    except IndexError:
        return ""


class BaseReader:
    BANK: str
    codes_provider: CodesProvider

    def __init__(self, page: pypdf.PageObject):
        self.page = page
        self.codes_provider = CodesProvider()

    def handle(self) -> Release:
        raise AssertionError("Uso de classe abstrata")

    @classmethod
    def extract_releases(cls, path: str) -> List[Release]:
        pages = pypdf.PdfReader(path).pages
        releases = []

        logging.info("Aquivo: %s", path.split("/")[-1])
        for i, page in enumerate(pages, 1):
            release = cls(page).handle()
            releases.append(release)
            logging.info("Página %i processada com sucesso", i)

        return releases


class BradescoReader(BaseReader):
    BANK = "Bradesco"
    DESTINY_RE = r"(.+)Nome:"
    DATE_RE = r"Data da operação: (\d{2}\/\d{2}\/\d{2})"
    VALUE_RE = r"(.+)Valor:"

    def handle(self):
        content = self.page.extract_text()
        method = re.search(r"Comprovante de Transação Bancária\n(.+)", content).group(1)  # type: ignore

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
                raise ValueError("Tipo incorreto de boleto")

    def pix(self, content: str):
        return Release(
            date=safe_re(self.DATE_RE, content),
            value=safe_re(self.VALUE_RE, content),
            destiny=safe_re(self.DESTINY_RE, content),
            detail=safe_re(r"(.*)Descrição:", content),
        )

    def tax(self, content: str):
        return Release(
            date=safe_re(self.DATE_RE, content),
            value=safe_re(r"(R\$ \d+,\d\d)Valor principal:", content),
            total=safe_re(r"(R\$ \d+,\d\d)Valor do pagamento:", content),
            tax=safe_re(r"(R\$ \d+,\d\d)Juros:", content),
            fines=safe_re(r"(R\$ \d+,\d\d)Multa:", content),
            destiny=safe_re(r"Descrição:(.*)\nEmpresa \/ Órgão:", content),
            detail=safe_re(r"REFERENCIA:(.*)Descrição:", content),
        )

    def payment(self, content: str):
        return Release(
            date=safe_re(self.DATE_RE, content),
            value=safe_re(self.VALUE_RE, content),
            destiny=safe_re(r"(.+)Favorecido:", content),
            detail=safe_re(r"(.*)Finalidade:", content),
        )

    def charge(self, content: str):
        return Release(
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
    VALUE_RE = r"Valor\n(.+)"

    def handle(self):
        content = self.page.extract_text()
        is_pix = re.search(r"Tipo\nPix", content)

        if is_pix:
            return self.pix(content)
        return self.payment(content)

    def pix(self, content: str):
        return Release(
            date=self.__date(content),
            value=safe_re(self.VALUE_RE, content),
            destiny=safe_re(r"Nome\n(.+)", content, 1),
            detail=safe_re(r"Descrição do Pix\n(.+)", content),
        )

    def payment(self, content: str):
        return Release(
            date=self.__date(content),
            value=safe_re(self.VALUE_RE, content),
            destiny=safe_re(r"Favorecido\n(.+)", content),
        )

    def __date(self, content: str):
        date = safe_re(r"no dia (\d\d? de \w+ de \d\d\d\d)", content)
        if date:
            return datetime.strptime(date, "%d de %B de %Y").strftime("%d/%m/%Y")
        return ""


READER_LIST: List[type[BaseReader]] = [
    BradescoReader,
    StoneReader,
]

BANK_LIST = list(map(lambda Reader: Reader.BANK, READER_LIST))
