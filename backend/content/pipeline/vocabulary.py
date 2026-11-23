"""
Segmentación de un ejemplo contra el vocabulario del sílabo, para la
validación `example_level` (08-contenido.md §3): "Las demás palabras del
ejemplo pertenecen al mismo nivel o a uno inferior, con la tolerancia fijada".
"""
from __future__ import annotations

from .pinyin import is_chinese_char

_registered: set[str] = set()


def _composable(word: str, allowed: set[str]) -> bool:
    """¿Se puede escribir `word` como una sucesión de palabras de `allowed`? (一条 = 一 + 条)."""
    n = len(word)
    ok = [False] * (n + 1)
    ok[0] = True
    for i in range(n):
        if not ok[i]:
            continue
        for j in range(i + 1, n + 1):
            if word[i:j] in allowed:
                ok[j] = True
    return ok[n]


def out_of_level_words(text: str, target: str, allowed: set[str], known: set[str]) -> list[str]:
    """
    Palabras del ejemplo que no pertenecen al nivel del ejemplo ni a uno
    inferior (`allowed`). La palabra objetivo nunca cuenta. `known` son todas
    las palabras del sílabo cargadas (de cualquier nivel); se añaden al
    segmentador para que las reconozca como palabras.
    """
    import jieba

    jieba.setLogLevel(60)
    for w in (known | allowed | {target}) - _registered:
        jieba.add_word(w)
        _registered.add(w)

    out = []
    for token in jieba.cut(text):
        if not token or not all(is_chinese_char(c) for c in token):
            continue
        if token == target or token in allowed:
            continue
        rest = token.replace(target, "") if target else token
        if not rest or _composable(rest, allowed) or (target and _composable_with_target(token, target, allowed)):
            continue
        out.append(token)
    return out


def _composable_with_target(token: str, target: str, allowed: set[str]) -> bool:
    return _composable(token, allowed | {target})
