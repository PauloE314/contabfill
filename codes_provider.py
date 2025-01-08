import json
import difflib
from readers import BradescoReader, StoneReader


BANK_CODES = {BradescoReader.BANK: 9, StoneReader.BANK: 6276}


class CodesProvider:
    SIMILARITY_RATIO = 0.85
    relation: dict[str, int]

    def __init__(self):
        self.relation = {}

    def debit(self, entity: str) -> int | None:
        entity = entity.upper()
        keys = self.relation.keys()
        close = difflib.get_close_matches(entity, keys, 1, self.SIMILARITY_RATIO)

        return self.relation.get(close[0]) if close else None

    def credit(self, bank: str) -> int:
        code = BANK_CODES[bank]

        if code:
            return code

        raise ValueError(f"Tipo desconhecido de banco: {bank}")

    def set_codes_relation_from_json(self, path: str):
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
            self.relation = self.__upper_dict(data)

    def __upper_dict(self, d: dict):
        return {k.upper(): v for k, v in d.items()}
