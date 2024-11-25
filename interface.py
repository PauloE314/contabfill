from typing import Callable
import tkinter as tk
from tkinter import filedialog


class GUI:
    BANKS = ("Bradesco", "Stone")
    WIDTH = 600
    HEIGHT = 400

    paths = []

    def __init__(self):
        self.root = tk.Tk()

    def start(self, process: Callable):
        self.__process_handler = process
        self.presets()
        self.build()
        self.root.mainloop()

    def build(self):
        frame = tk.Frame(self.root)
        tk.Label(frame, text="Banco:").pack(side=tk.LEFT)
        variable = tk.StringVar(self.root)
        variable.set(self.BANKS[0])
        tk.OptionMenu(frame, variable, *self.BANKS).pack(side=tk.RIGHT)
        frame.pack(pady=30)

        tk.Button(
            self.root,
            text="Selecionar arquivos",
            command=self.__handle_file_selected_button_clicked,
        ).pack(pady=20)

        self.selected_files_frame = tk.Frame(self.root)
        self.selected_files_frame.pack()
        tk.Label(self.selected_files_frame, text="Nenhum arquivo selecionado").pack()

        tk.Button(
            self.root,
            text="Processar",
            command=self.__handle_process_button_blicked,
        ).pack(pady=20)

    def presets(self):
        self.root.title("ContabFill")

        center_x = int(self.root.winfo_screenwidth() / 2 - self.WIDTH / 2)
        center_y = int(self.root.winfo_screenheight() / 2 - self.HEIGHT / 2)
        self.root.geometry(f"{self.WIDTH}x{self.HEIGHT}+{center_x}+{center_y}")

    def __handle_file_selected_button_clicked(self):
        paths = filedialog.askopenfilenames(
            title="PDFs para processamento", filetypes=[("Arquivos em PDF", "*.pdf")]
        )

        if len(paths):
            self.paths = paths
            # self.selected_files_label.config(text="\n".join(filenames))

            for child in self.selected_files_frame.winfo_children():
                child.destroy()

            for path in paths:
                filename = path.split("/")[-1]
                tk.Label(self.selected_files_frame, text=filename).pack()

    def __handle_process_button_blicked(self):
        pass
