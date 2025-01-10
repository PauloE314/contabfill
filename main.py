import locale
from readers import ReaderFactory
from parsers import CSVParser
from interface import GUI


def main():
    locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")

    gui = GUI(
        parser=CSVParser(),
        reader_factory=ReaderFactory(),
    )
    gui.start()


if __name__ == "__main__":
    main()
