"""Výstupní modely nástrojů a vstupy zápisů.

Každý čtecí nástroj vrací **envelope** dědící z ``EnvelopeBase`` — data plus
``provenance`` a ``warnings``. Pole záznamů Flexi jsou dynamická (ploché
``pole@showAs`` atributy, částky jako řetězce, referenční dicty), takže se
záznamy drží jako ``dict`` — tvrdé typování by bylo křehké vůči konfiguraci
konkrétní instance.
"""

from __future__ import annotations

import math
from typing import Any, Literal

from openmcp_sdk.envelope import EnvelopeBase
from pydantic import BaseModel, Field, field_validator, model_validator

#: Operátory filtračního jazyka Flexi, které generické nástroje vystavují.
#: `in`/`between`/`or` záměrně chybí — držíme jen AND řetěz jednoduchých
#: podmínek, který jde bezpečně poskládat bez volné syntaxe.
FilterOp = Literal[
    "eq",
    "neq",
    "lt",
    "lte",
    "gt",
    "gte",
    "like",
    "like_similar",
    "begins",
    "begins_similar",
    "ends",
    "is_null",
    "is_not_null",
    "is_true",
    "is_false",
    "is_empty",
    "is_not_empty",
]


class FilterCondition(BaseModel):
    """Jedna podmínka filtru — podmínky se skládají operátorem AND."""

    field: str = Field(
        description=(
            "Název pole (camelCase), případně tečkovaná vazba první úrovně, "
            "např. datVyst, stavUhrK, firma.skupFir."
        )
    )
    op: FilterOp = Field(
        description=(
            "Operátor porovnání. Textové operátory (like, like_similar, begins, "
            "ends) hledají podřetězec/prefix samy o sobě — BEZ zástupných znaků "
            "(% v hodnotě se bere doslovně a nenajde nic); like_similar navíc "
            "ignoruje diakritiku."
        )
    )
    value: str | int | float | bool | None = Field(
        default=None,
        description="Porovnávaná hodnota; u operátorů is_* se vynechává.",
    )

    @field_validator("value")
    @classmethod
    def _finite_number(cls, value: Any) -> Any:
        """`inf`/`-inf`/`nan` nejsou hodnoty, které by šlo porovnávat.

        Pydantic je u `float` ve výchozím nastavení propouští (`allow_inf_nan`)
        a `Decimal(float("inf"))` z nich udělá literál `Infinity`, který by
        odešel do filtru v URL. Filtr se tím rozbije tiše — Flexi vrátí
        prázdný výsledek, ne chybu.
        """
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("hodnota musí být konečné číslo")
        return value


class RowsEnvelope(EnvelopeBase):
    """Seznam záznamů evidence."""

    items: list[dict[str, Any]]
    total: int | None = None
    truncated: bool = False


class RecordEnvelope(EnvelopeBase):
    """Jeden záznam evidence (detail)."""

    record: dict[str, Any]


class StockItemInput(BaseModel):
    """Položka nového skladového pohybu.

    Při zápisu se posílá jako ``polozkyDokladu`` (pozor na asymetrii Flexi:
    při čtení jsou položky ve ``skladovePolozky``).
    """

    product_code: str = Field(description="Kód produktu z ceníku (bez prefixu code:).")
    # `allow_inf_nan=False` NENÍ redundantní vůči `gt`/`ge`: `inf > 0` je True,
    # takže by `float("inf")` prošlo a do účetnictví by odešlo `Infinity`.
    # (`nan` porovnání neprojde, `-inf` u `gt=0` taky ne — díra je `+inf`.)
    quantity: float = Field(
        gt=0, allow_inf_nan=False, description="Množství v evidenční jednotce (mnozMj)."
    )
    unit_price: float = Field(
        ge=0, allow_inf_nan=False, description="Cena za jednotku (cenaMj)."
    )


class StockItemPriceInput(BaseModel):
    """Úprava existující položky skladového pohybu — jen cena a množství."""

    item_id: str = Field(description="ID položky dokladu (z detailu pohybu).")
    unit_price: float | None = Field(
        default=None, ge=0, allow_inf_nan=False, description="Nová cena za jednotku."
    )
    quantity: float | None = Field(
        default=None, gt=0, allow_inf_nan=False, description="Nové množství."
    )

    @model_validator(mode="after")
    def _at_least_one_change(self) -> StockItemPriceInput:
        if self.unit_price is None and self.quantity is None:
            raise ValueError("položka musí měnit aspoň cenu nebo množství")
        return self
