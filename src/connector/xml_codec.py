"""Převod mezi XML formátem ABRA Flexi a python dicty.

Přenesené (a otypované) z ověřené starší implementace konektoru — XML je pro
Flexi zvolené rozhraní: má lepší dokumentaci a JSON varianta API se v praxi
ukázala problematická. Všechny requesty i odpovědi jsou zabalené v kořenovém
elementu ``winstrom`` (historický název produktu).

Konvence plochého tvaru: atribut elementu se přilepí k názvu pole —
``<firma showAs="Firma s.r.o.">code:FIRMA</firma>`` se stane dvojicí
``{"firma": "code:FIRMA", "firma@showAs": "Firma s.r.o."}``. Zpětný převod
(:func:`build_flexibee_xml`) je přesná inverze.
"""

from __future__ import annotations

from typing import Any

import xmltodict

from connector.registry import EVIDENCES

# Evidence, které musí být vždy seznam — jinak by odpověď s jediným záznamem
# měla jiný tvar než odpověď se dvěma a volající by musel větvit na každém
# přístupu. POZOR na kolize: názvy evidencí (`sklad`, `cenik`, `stredisko`…)
# jsou zároveň běžná referenční POLE záznamů, proto se listifikují jen přímo
# pod kořenovým elementem (viz `_force_list`).
ARRAY_TAGS = frozenset(EVIDENCES) | frozenset({"company"})

#: Elementy listifikované v libovolné hloubce — položky a servisní elementy.
#: `vazba` je tu kvůli `relations=vazby` (obal `<vazby><vazba>…`); jako
#: evidence pod kořenem ji pokrývá ARRAY_TAGS větev.
_ANY_DEPTH_TAGS = frozenset({"result", "priloha", "vazba"})

#: Obaly kolekcí položek: `<polozkyFaktury><faktura-vydana-polozka>…`.
#: Po parsování se obal zkolabuje na přímý seznam položek — volající pak
#: nemusí znát název položkové evidence.
WRAPPER_TAGS = frozenset(
    {
        "polozkyFaktury",
        "polozkyObchDokladu",
        "polozkyDokladu",
        "skladovePolozky",
        "prilohy",
        "vazby",
    }
)


def _force_list(path: Any, key: str, value: Any) -> bool:
    if key.endswith("-polozka") or key in _ANY_DEPTH_TAGS:
        return True
    return key in ARRAY_TAGS and len(path) == 1


def parse_flexibee_xml(xml_string: str) -> dict[str, Any]:
    """Naparsuj XML odpověď Flexi na dict se zploštělými atributy."""
    parsed = xmltodict.parse(
        xml_string,
        attr_prefix="@",
        cdata_key="#text",
        force_list=_force_list,
    )
    flattened = collapse_collections(flatten_attributes(parsed))
    if not isinstance(flattened, dict):
        # xmltodict na kořenovém elementu vždy vrací dict; tohle je pojistka
        # pro typovou soustavu, ne očekávaná větev.
        raise ValueError("kořen XML dokumentu není element")
    return flattened


def collapse_collections(obj: Any) -> Any:
    """Zkolabuj obaly kolekcí na přímý seznam položek.

    ``{"polozkyFaktury": {"faktura-vydana-polozka": [ … ]}}``
    → ``{"polozkyFaktury": [ … ]}``
    """
    if isinstance(obj, list):
        return [collapse_collections(item) for item in obj]
    if not isinstance(obj, dict):
        return obj
    out: dict[str, Any] = {}
    for key, value in obj.items():
        if key in WRAPPER_TAGS and isinstance(value, dict):
            children = [val for name, val in value.items() if not name.startswith("@")]
            if len(children) == 1 and isinstance(children[0], list):
                out[key] = collapse_collections(children[0])
                continue
        out[key] = collapse_collections(value)
    return out


def flatten_attributes(obj: Any) -> Any:
    """Zploští XML atributy do plochého tvaru ``pole@atribut``.

    ``{"firma": {"@showAs": "Název", "#text": "code:ID"}}``
    → ``{"firma": "code:ID", "firma@showAs": "Název"}``
    """
    if obj is None:
        return obj

    if isinstance(obj, list):
        return [flatten_attributes(item) for item in obj]

    if not isinstance(obj, dict):
        return obj

    flattened: dict[str, Any] = {}

    for key, value in obj.items():
        # Klíč začínající @ je atribut rodičovského elementu — zůstává.
        if key.startswith("@"):
            flattened[key] = value
            continue

        if isinstance(value, dict):
            has_text = "#text" in value
            attributes = [k for k in value if k.startswith("@")]
            other_props = [k for k in value if not k.startswith("@") and k != "#text"]

            if has_text and (attributes or not other_props):
                # Element s textem a atributy: text na hlavní klíč, atributy
                # jako `klíč@atribut`.
                flattened[key] = value["#text"]
                for attr in attributes:
                    flattened[f"{key}@{attr[1:]}"] = value[attr]
                for prop in other_props:
                    flattened[f"{key}.{prop}"] = flatten_attributes(value[prop])
            else:
                nested = flatten_attributes(value)
                nested_keys = list(nested.keys())
                if nested_keys and all(k.startswith("@") for k in nested_keys):
                    # Element jen s atributy — zploštit na rodiče.
                    for attr in nested_keys:
                        flattened[f"{key}@{attr[1:]}"] = nested[attr]
                else:
                    flattened[key] = nested
        else:
            flattened[key] = flatten_attributes(value)

    return flattened


def unflatten_attributes(obj: Any) -> Any:
    """Inverze :func:`flatten_attributes` — pro stavbu XML těla zápisu."""
    if obj is None:
        return obj

    if isinstance(obj, list):
        return [unflatten_attributes(item) for item in obj]

    if not isinstance(obj, dict):
        return obj

    unflattened: dict[str, Any] = {}
    attribute_map: dict[str, dict[str, Any]] = {}

    # První průchod: posbírat atributy `pole@atribut`.
    for key, value in obj.items():
        if "@" in key:
            field_name, attr_name = key.split("@", 1)
            attribute_map.setdefault(field_name, {})[f"@{attr_name}"] = value

    # Druhý průchod: postavit strukturu.
    for key, value in obj.items():
        if "@" in key:
            continue

        if key in attribute_map:
            if isinstance(value, dict):
                unflattened[key] = {**attribute_map[key], **unflatten_attributes(value)}
            else:
                unflattened[key] = {**attribute_map[key], "#text": value}
        else:
            unflattened[key] = unflatten_attributes(value)

    return unflattened


def build_flexibee_xml(payload: dict[str, Any]) -> str:
    """Postav XML tělo requestu z dictu (včetně ``winstrom`` obálky)."""
    xml = xmltodict.unparse(
        unflatten_attributes(payload),
        attr_prefix="@",
        cdata_key="#text",
        pretty=True,
        indent="  ",
    )
    if not isinstance(xml, str):  # pragma: no cover — xmltodict vrací str
        raise ValueError("xmltodict nevrátil řetězec")
    return xml


def as_str(value: Any) -> str:
    """Referenční pole může přijít jako dict (``@ref``/``@showAs``/``#text``).

    Bezpečně ho převede na řetězec — používej při čtení hodnot, u kterých si
    tvarem nejsi jistý.
    """
    if isinstance(value, dict):
        for candidate in ("#text", "value", "@showAs", "@ref"):
            if candidate in value:
                return as_str(value[candidate])
        return ""
    if value is None:
        return ""
    return str(value)


def strip_code(value: Any) -> str:
    """Odstraň ``code:`` prefix reference na číselník."""
    text = as_str(value)
    return text[5:] if text.startswith("code:") else text


def code_ref(value: str) -> str:
    """Doplň ``code:`` prefix pro zápis reference na číselník.

    Kódy můžou obsahovat mezery (typy dokladů) — ``code:`` prefix s mezerami
    ve Flexi funguje.
    """
    return value if value.startswith("code:") else f"code:{value}"


__all__ = [
    "ARRAY_TAGS",
    "as_str",
    "build_flexibee_xml",
    "code_ref",
    "flatten_attributes",
    "parse_flexibee_xml",
    "strip_code",
    "unflatten_attributes",
]
