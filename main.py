import locale
from readers import reader_chooser
from parsers import CSVParser
from interface import GUI


def main():
    locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")

    gui = GUI(
        parser=CSVParser(),
        reader_chooser=reader_chooser,
    )
    gui.start()


if __name__ == "__main__":
    main()
