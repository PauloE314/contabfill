import traceback
from typing import Callable, List, Tuple
from tkinter import filedialog, messagebox
import tkinter as tk
from datetime import datetime
from readers import BANK_LIST, Release
from parsers import CSVParser


class GUI:
    WIDTH = 1000
    HEIGHT = 600

    paths: Tuple[str, ...] = tuple()

    bank_selection: tk.StringVar
    selected_files_frame: tk.Frame
    process_handler: Callable[[str, Tuple[str, ...]], List[Release]]
    parser: CSVParser
    codes_relation_button: tk.Button
    codes_relation_path: str | None

    def __init__(
        self,
        parser: CSVParser,
        on_process: Callable[[str, Tuple[str, ...]], List[Release]],
    ):
        self.parser = parser
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
        self.bank_var.set(BANK_LIST[0])
        bank_selection = tk.OptionMenu(self.root, self.bank_var, *BANK_LIST)

        # File selection
        find_file_label = tk.Label(self.root, text="Arquivos:")
        find_file_button = tk.Button(
            self.root,
            text="Selecionar arquivos",
            anchor="w",
            command=self.find_pdf_files,
        )
        clear_files_button = tk.Button(
            self.root, text="X", command=self.clear_pdf_files
        )
        self.selected_files_frame = tk.Frame(self.root, borderwidth=1, relief="sunken")
        self.update_selected_file_list()

        # Process
        process_button = tk.Button(
            self.root,
            text="Processar",
            command=self.process,
        )

        # Code relation selection
        codes_relation_label = tk.Label(self.root, text="Relação de códigos: ")
        self.codes_relation_button = tk.Button(
            self.root,
            text="Ainda não selecionado",
            command=self.find_codes_relation_json,
            anchor="w",
        )
        clear_codes_relation_button = tk.Button(
            self.root, text="X", command=self.clear_codes_relation
        )

        # Grid
        self.root.maxsize(1000, 500)
        self.root.configure(padx=15, pady=15)
        self.root.rowconfigure(2, weight=1)
        self.root.rowconfigure(3, weight=1)
        self.root.columnconfigure(3, weight=1)
        self.root.columnconfigure(4, weight=1, minsize=300)

        self.selected_files_frame.grid(
            row=0, column=4, rowspan=4, sticky="news", padx=(15, 0)
        )
        self.selected_files_frame.grid_propagate(False)

        bank_label.grid(row=0, column=0, sticky="W")
        bank_selection.grid(row=0, column=1, sticky="W")
        find_file_label.grid(row=1, column=0, sticky="W")
        find_file_button.grid(row=1, column=1, sticky="WE")
        clear_files_button.grid(row=1, column=2, sticky="W")
        codes_relation_label.grid(row=2, column=0, sticky="NW")
        self.codes_relation_button.grid(
            row=2,
            column=1,
            sticky="NWE",
        )
        clear_codes_relation_button.grid(row=2, column=2, sticky="NW")
        process_button.grid(row=3, column=0, columnspan=2, sticky="SEW")

    def find_pdf_files(self):
        paths = filedialog.askopenfilenames(
            title="PDFs para processamento", filetypes=[("Arquivos em PDF", "*.pdf")]
        )

        if len(paths) and isinstance(paths, tuple):
            self.paths = paths
            self.update_selected_file_list()

    def clear_pdf_files(self):
        self.paths = tuple()
        self.update_selected_file_list()

    def update_selected_file_list(self):
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

    def find_codes_relation_json(self):
        path = filedialog.askopenfilename(
            title="JSON de códigos", filetypes=[("Arquivo JSON", "*.json")]
        )
        if path:
            self.codes_relation_path = path
            self.codes_relation_button.configure(
                text=f"Selecionado: {path.split("/")[-1]}"
            )

    def clear_codes_relation(self):
        self.codes_relation_button.configure(text="Ainda não selecionado")
        self.codes_relation_path = None

    def process(self):
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
            self.save_error_file(e)
            return

        full_filename = filedialog.asksaveasfilename(
            initialfile=f"Processamento - {datetime.now()}",
            defaultextension=self.parser.DEFAULT_EXTENSION,
            filetypes=self.parser.FILE_TYPES,
        )

        if not full_filename:
            return

        self.parser.export_releases(
            releases, filename=full_filename, codes_path=self.codes_relation_path
        )
        self.paths = ()
        self.update_selected_file_list()

    def save_error_file(self, _: Exception):
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
