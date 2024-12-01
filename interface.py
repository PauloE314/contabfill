import traceback
from typing import Callable, List
from io import StringIO
from tkinter import filedialog, messagebox, font
import tkinter as tk
from datetime import datetime
from readers import BANK_LIST, Release
from parsers import CSVParser


class GUI:
    BANKS = BANK_LIST
    WIDTH = 1000
    HEIGHT = 600

    paths: List[str] = []
    bank_selection: tk.StringVar
    selected_files_frame: tk.Frame
    log_stream: StringIO
    process_handler: Callable[[str, List[str]], None]
    parser: CSVParser

    def __init__(
        self,
        log_stream: StringIO,
        parser: CSVParser,
        on_process: Callable[[str, List[str]], List[Release]],
    ):
        self.parser = parser
        self.log_stream = log_stream
        self.process_handler = on_process
        self.root = tk.Tk()

    def start(self):
        self.presets()
        self.build()
        self.root.mainloop()

    def presets(self):
        self.root.title("ContabFill")

        center_x = int(self.root.winfo_screenwidth() / 2 - self.WIDTH / 2)
        center_y = int(self.root.winfo_screenheight() / 2 - self.HEIGHT / 2)
        self.root.geometry(f"{self.WIDTH}x{self.HEIGHT}+{center_x}+{center_y}")

    def build(self):
        # Bank selection
        bank_label = tk.Label(self.root, text="Banco:")
        self.bank_var = tk.StringVar(self.root)
        self.bank_var.set(self.BANKS[0])
        bank_selection = tk.OptionMenu(self.root, self.bank_var, *self.BANKS)

        # File selection
        find_file_label = tk.Label(self.root, text="Arquivos:")
        find_file_button = tk.Button(
            self.root,
            text="Selecionar arquivos",
            command=self.__handle_file_selected_button,
        )
        self.selected_files_frame = tk.Frame(self.root, borderwidth=1, relief="sunken")
        self.__update_selected_file_list()

        # Process
        process_button = tk.Button(
            self.root,
            text="Processar",
            command=self.__handle_process_button,
        )

        # Grid
        self.root.maxsize(1000, 500)
        self.root.configure(padx=15, pady=15)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(2, weight=1)
        self.root.columnconfigure(2, weight=1)
        self.root.columnconfigure(3, weight=1, minsize=300)

        self.selected_files_frame.grid(
            row=0, column=3, rowspan=3, sticky="news", padx=(15, 0)
        )
        self.selected_files_frame.grid_propagate(False)

        bank_label.grid(row=0, column=0, sticky="W")
        bank_selection.grid(row=0, column=1, sticky="W")
        find_file_label.grid(row=1, column=0, sticky="NW")
        find_file_button.grid(row=1, column=1, sticky="NW")
        process_button.grid(row=2, column=0, columnspan=2, sticky="SEW")

    def __handle_file_selected_button(self):
        paths = filedialog.askopenfilenames(
            title="PDFs para processamento", filetypes=[("Arquivos em PDF", "*.pdf")]
        )

        if len(paths):
            self.paths = paths
            self.__update_selected_file_list()

    def __update_selected_file_list(self):
        for child in self.selected_files_frame.winfo_children():
            child.destroy()

        path_amount = len(self.paths)

        tk.Label(
            self.selected_files_frame,
            text="Lista de arquivos",
            borderwidth=1,
            relief="sunken",
        ).pack(pady=(5, 20), ipady=5, ipadx=10)
        if path_amount == 0:
            tk.Label(
                self.selected_files_frame,
                text="Nenhum arquivo selecionado",
            ).pack()

        else:
            tk.Label(
                self.selected_files_frame,
                text=f"{path_amount} arquivo(s) selecionado(s)\n",
            ).pack()

        for path in self.paths:
            filename = path.split("/")[-1]
            tk.Label(self.selected_files_frame, text=filename).pack()

    def __handle_process_button(self):
        if len(self.paths) == 0 or not self.bank_var.get():
            messagebox.showwarning(
                title="Processamento indevido",
                message="Selecione os arquivos para processamento e o seu tipo de banco",
            )
            return

        releases: List[Release] = []

        try:
            releases = self.process_handler(self.bank_var.get(), self.paths)
        except Exception as e:
            self.__save_error_file(e)
            return

        full_filename = filedialog.asksaveasfilename(
            defaultextension=self.parser.DEFAULT_EXTENSION,
            filetypes=self.parser.FILE_TYPES,
        )

        if not full_filename:
            return

        self.parser.export_releases(releases, filename=full_filename)
        self.paths = []
        self.__update_selected_file_list()

    def __save_error_file(self, error: Exception):
        file = filedialog.asksaveasfile(
            initialfile=f"Error - {datetime.now()}",
            mode="w",
            defaultextension=".txt",
            filetypes=(("TXT", "*.txt"),),
        )

        if not file:
            return

        file.write(traceback.format_exc())
        file.close()
