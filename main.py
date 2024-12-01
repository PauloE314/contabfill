import locale
import logging
from readers import READER_LIST
from parsers import CSVParser
from interface import GUI
from io import StringIO
import traceback


def process_files(bank, paths):
    for Reader in READER_LIST:
        if bank == Reader.BANK:
            releases = []

            for path in paths:
                releases.extend(Reader.extract_releases(path))

            return releases
    raise Exception("Banco não reconhecido")


def main():
    locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")

    log_stream = StringIO()
    logging.basicConfig(stream=log_stream, level=logging.INFO, format="%(message)s")

    parser = CSVParser()

    gui = GUI(
        parser=parser,
        log_stream=log_stream,
        on_process=process_files,
    )
    gui.start()


if __name__ == "__main__":
    main()
