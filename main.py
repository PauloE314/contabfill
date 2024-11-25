import locale
from typing import Callable
import pypdf
from readers import BaseReader, BradescoReader, StoneReader, Release
from parsers import CSVParser
from interface import GUI


def files_selected(filenames):
    print(filenames)


def main():
    locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")

    GUI().start(files_selected)

    # releases = []
    # bradesco_paths = [
    #     "/home/paulo/Documentos/dev/contabfill/examples/Bradesco/Bradesco_pix.pdf",
    #     "/home/paulo/Documentos/dev/contabfill/examples/Bradesco/Bradesco_impostos.pdf",
    #     "/home/paulo/Documentos/dev/contabfill/examples/Bradesco/Bradesco_folha_de_pagamento.pdf",
    #     "/home/paulo/Documentos/dev/contabfill/examples/Bradesco/Bradesco_cobrança.pdf",
    # ]
    # stone_paths = [
    #     "/home/paulo/Documentos/dev/contabfill/examples/Stone/Exemplo_stone.pdf"
    # ]

    # for path in bradesco_paths:
    #     releases.extend(BradescoReader.extract_releases(path))

    # for path in stone_paths:
    #     releases.extend(StoneReader.extract_releases(path))

    # CSVParser().export_releases(releases)


if __name__ == "__main__":
    main()
