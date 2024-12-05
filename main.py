import locale
from io import StringIO
from typing import List, Tuple
from readers import READER_LIST
from parsers import CSVParser
from interface import GUI
from readers import Release


def process_files(bank: str, paths: Tuple[str, ...]):
    for Reader in READER_LIST:
        if bank == Reader.BANK:
            releases: List[Release] = []

            for path in paths:
                releases.extend(Reader.extract_releases(path))

            return releases
    raise TypeError("Banco não reconhecido")


def main():
    locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")

    # parser = CSVParser()

    # gui = GUI(
    #     parser=parser,
    #     on_process=process_files,
    # )
    # gui.start()

    print(
        process_files(
            READER_LIST[1].BANK,
            (
                "/home/paulo/Documentos/dev/contabfill/examples/Stone/Exemplo_pix_detalhado.pdf",
                "/home/paulo/Documentos/dev/contabfill/examples/Stone/Exemplo_pix_simples.pdf",
            ),
        )
    )


if __name__ == "__main__":
    main()
