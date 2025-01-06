import json
import difflib

CODE_RELATION = {
    "JUROS": 4701,
}


class CodesProvider:
    SIMILARITY_RATIO = 85
    relation: dict[str, int]

    def __init__(self):
        self.relation = self.__upper_dict(CODE_RELATION)

    def credit(self, entity: str) -> str:
        value = self.__fetch(entity)
        return str(value) if value else ""

    def debit(self, _: str) -> str:
        value = self.relation.get("JUROS") or 4701
        return str(value) if value else ""

    def set_codes_relation_from_json(self, path: str):
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
            self.relation = self.__upper_dict(data)

    def __upper_dict(self, d: dict):
        return {k.upper(): v for k, v in d.items()}

    def __fetch(self, inpt: str) -> int | None:
        inpt = inpt.upper()
        keys = self.relation.keys()
        close = difflib.get_close_matches(inpt, keys, 1, 0.8)

        return self.relation.get(close[0]) if close else None
