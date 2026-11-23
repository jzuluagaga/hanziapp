"""
Armado de mazos por tema (D-49, 08-contenido.md §7).

Entrada: las palabras vigentes de un nivel con su subtema aprobado. Salida: una lista
de mazos (claves de tema o subtema, parte, palabras) con tamaño objetivo T del nivel
y banda [0,5 T; 1,5 T]:

1. Un tema con menos de 8 palabras se junta con el tema siguiente en el orden.
2. Un tema que cabe en 1,5 T es un mazo.
3. Si no cabe, se divide por subtemas: los mayores de 1,5 T se parten en tramos iguales
   y después los menores de 0,5 T se juntan con el vecino que dé el grupo más pequeño.
   Ningún mazo queda con menos de 8 palabras.
Los nombres se arman en la interfaz con las claves; no hay claves nuevas por fusión.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

ABS_MIN = 8


@dataclass
class Group:
    keys: list[str]
    words: list[int] = field(default_factory=list)
    part: int | None = None


def _merge_small(groups: list[Group], lo: float, hi: float) -> list[Group]:
    """Junta cada grupo menor de 0,5 T con el vecino (anterior o siguiente) que dé el grupo más pequeño.
    Solo supera 1,5 T si no hay otra forma de que ningún mazo quede con menos de 8 palabras."""
    out = list(groups)
    stuck: set[int] = set()
    while True:
        small = [i for i, g in enumerate(out) if len(g.words) < lo and id(g) not in stuck]
        if not small or len(out) == 1:
            return out
        i = min(small, key=lambda k: len(out[k].words))
        options = [j for j in (i - 1, i + 1) if 0 <= j < len(out)]
        j = min(options, key=lambda k: len(out[k].words))
        if len(out[i].words) + len(out[j].words) > hi and len(out[i].words) >= ABS_MIN:
            stuck.add(id(out[i]))
            continue
        a, b = sorted((i, j))
        keys = out[a].keys + [k for k in out[b].keys if k not in out[a].keys]
        out[a:b + 1] = [Group(keys, out[a].words + out[b].words)]


def _split_big(g: Group, target: int, hi: float) -> list[Group]:
    if len(g.words) <= hi:
        return [g]
    k = math.ceil(len(g.words) / target)
    size = math.ceil(len(g.words) / k)
    return [Group(list(g.keys), g.words[i:i + size], part=n) for n, i in enumerate(range(0, len(g.words), size), start=1)]


def plan_level(taxonomy: dict, words_by_sub: dict[str, list[int]], target: int) -> list[Group]:
    """`words_by_sub`: subtema → ids de palabras en el orden del sílabo."""
    lo, hi = 0.5 * target, 1.5 * target
    units: list[tuple[list[str], list[Group], set[str]]] = []  # (claves del tema, grupos por subtema, subtemas del tema)
    for theme in taxonomy["themes"]:
        subs = [Group([s["key"]], list(words_by_sub.get(s["key"], []))) for s in theme["subthemes"]]
        subs = [g for g in subs if g.words]
        if subs:
            units.append(([theme["key"]], subs, {g.keys[0] for g in subs}))

    # 1. Temas con menos de 8 palabras: se juntan con el siguiente (o con el anterior si es el último).
    i = 0
    while i < len(units):
        keys, subs, present = units[i]
        if sum(len(g.words) for g in subs) < ABS_MIN and len(units) > 1:
            j = i + 1 if i + 1 < len(units) else i - 1
            small = Group(keys, [w for g in subs for w in g.words])  # entra como un bloque con el nombre del tema
            nkeys, nsubs, npresent = units[j]
            merged = (keys + nkeys, [small] + nsubs, set()) if j > i else (nkeys + keys, nsubs + [small], set())
            units[min(i, j)] = merged
            del units[max(i, j)]
            i = max(0, min(i, j))
            continue
        i += 1

    decks: list[Group] = []
    for keys, subs, present in units:
        total = sum(len(g.words) for g in subs)
        if total <= hi:
            decks.append(Group(keys, [w for g in subs for w in g.words]))
            continue
        pieces: list[Group] = []
        for g in subs:
            pieces += _split_big(g, target, hi)
        built = _merge_small(pieces, lo, hi)
        # Nombres: si un subtema quedó repartido entre mazos o un mazo junta tres o más subtemas,
        # todos los mazos del tema se llaman "Tema · Parte n"; si no, cada uno lleva sus subtemas.
        seen_keys = [k for g in built for k in g.keys]
        spread = len(seen_keys) != len(set(seen_keys)) or any(len(g.keys) >= 3 for g in built)
        for n, g in enumerate(built, start=1):
            if spread:
                g.keys, g.part = list(keys), n
            else:
                g.part = None
        decks += built
    return decks
