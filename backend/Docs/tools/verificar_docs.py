#!/usr/bin/env python3
"""Verifica la coherencia de docs/ (requisitos Q-25 y Q-30).

Uso:
    python3 docs/tools/verificar_docs.py            # revisa la documentación
    python3 docs/tools/verificar_docs.py --tests .,../frontend  # además exige que cada prueba citada exista en el código

Sale con código 1 si hay algún error. Los avisos no hacen fallar.
Sin dependencias: solo la biblioteca estándar.
"""
import re
import sys
from collections import Counter
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent
errores, avisos = [], []


def leer(nombre):
    ruta = DOCS / nombre
    return ruta.read_text(encoding="utf-8") if ruta.exists() else ""


def definidos(texto, patron):
    """IDs definidos: los que abren una fila de tabla."""
    return set(re.findall(r"^\| (%s) \|" % patron, texto, flags=re.M))


archivos = sorted(p for p in DOCS.rglob("*.md"))
textos = {p.relative_to(DOCS).as_posix(): p.read_text(encoding="utf-8") for p in archivos}

# ---------------------------------------------------------------- 1. IDs definidos
reglas = definidos(leer("03-reglas-de-negocio.md"), r"R-[A-Z]{3}-\d\d")
decisiones = definidos(leer("04-decisiones.md"), r"D-\d\d")
calidad = definidos(leer("06-calidad.md"), r"Q-\d\d")
metricas = definidos(leer("07-eventos-y-metricas.md"), r"M-\d\d")
mapa = leer("05-mapa-de-historias.md")
historias_mapa = dict(
    re.findall(r"^\| (HU-E\d\d-\d\d) \| \w \|.*?\| (V\d[ab]?) \|", mapa, flags=re.M)
)
eventos = set(re.findall(r"^\| `([a-z_]+)`(?:, `[a-z_]+`)* \|", leer("07-eventos-y-metricas.md"), flags=re.M))
eventos |= set(
    e
    for fila in re.findall(r"^\| ((?:`[a-z_]+`(?:, )?)+) \|", leer("07-eventos-y-metricas.md"), flags=re.M)
    for e in re.findall(r"`([a-z_]+)`", fila)
)

# ---------------------------------------------------------------- 2. IDs citados existen
citas = [
    (r"R-[A-Z]{3}-\d\d", reglas, "regla"),
    (r"D-\d\d", decisiones, "decisión"),
    (r"Q-\d\d", calidad, "requisito de calidad"),
    (r"M-\d\d", metricas, "métrica"),
    (r"HU-E\d\d-\d\d", set(historias_mapa), "historia"),
]
for nombre, texto in textos.items():
    for patron, validos, tipo in citas:
        for cita in sorted(set(re.findall(r"(?<![A-Za-z0-9-])%s(?!\d)" % patron, texto))):
            if cita not in validos:
                errores.append(f"{nombre}: cita {tipo} inexistente {cita}")

# ---------------------------------------------------------------- 3. Topes de extensión
for nombre, texto in textos.items():
    m = re.search(r"\*\*Tope de extensión:\*\* (\d+) líneas", texto)
    lineas = texto.count("\n") + 1
    if not m:
        avisos.append(f"{nombre}: no declara tope de extensión")
    elif lineas > int(m.group(1)):
        errores.append(f"{nombre}: {lineas} líneas, tope {m.group(1)}")

# ---------------------------------------------------------------- 4. Historias detalladas
DECLARACIONES = ["Derechos", "Idioma", "Guardado", "Analítica", "Datos personales"]
compartidas = set(re.findall(r"`((?:test|e2e|load)_[a-z0-9_]+)`", leer("03-reglas-de-negocio.md") + leer("06-calidad.md")))
detalladas, pruebas = {}, []
for nombre, texto in textos.items():
    if not nombre.startswith("historias/"):
        continue
    for bloque in re.split(r"^### ", texto, flags=re.M)[1:]:
        m = re.match(r"(HU-E\d\d-\d\d) · ", bloque)
        if not m:
            continue
        hu = m.group(1)
        if hu in detalladas:
            errores.append(f"{nombre}: {hu} está detallada dos veces")
        detalladas[hu] = nombre
        if not nombre.startswith(f"historias/{hu[3:6]}"):
            errores.append(f"{nombre}: {hu} está en el archivo de otra épica")
        corte = re.search(r"\*\*Corte:\*\* (V\d[ab]?)", bloque)
        if not corte or corte.group(1) != historias_mapa.get(hu):
            errores.append(f"{nombre}: {hu} declara un corte distinto al del mapa")
        filas = re.findall(r"^\| \d+ \| (.+?) \| (.*?) \|$", bloque, flags=re.M)
        if len(filas) < 3:
            errores.append(f"{nombre}: {hu} tiene menos de 3 criterios")
        for criterio, celda in filas:
            nombres = re.findall(r"`((?:test|e2e|load)_[a-z0-9_]+)`", celda)
            if not nombres:
                errores.append(f"{nombre}: {hu} tiene un criterio sin prueba: {criterio[:50]}…")
            pruebas += [(n, hu) for n in nombres]
        for d in DECLARACIONES:
            if not re.search(r"^- \*\*%s:\*\* \S" % d, bloque, flags=re.M):
                errores.append(f"{nombre}: {hu} no declara «{d}»")
        linea = re.search(r"^- \*\*Analítica:\*\* (.*)$", bloque, flags=re.M)
        for ev in re.findall(r"`([a-z_]+)`", linea.group(1) if linea else ""):
            if ev not in eventos:
                errores.append(f"{nombre}: {hu} emite un evento que no está en el catálogo: {ev}")

for prueba, veces in Counter(n for n, _ in pruebas).items():
    if veces > 1 and prueba not in compartidas:
        errores.append(f"prueba repetida en {veces} criterios: {prueba}")

for hu, corte in historias_mapa.items():
    if corte.startswith("V1") and hu not in detalladas:
        errores.append(f"{hu} es de {corte} y no está detallada en historias/")
    if not corte.startswith("V1") and hu in detalladas:
        avisos.append(f"{hu} es de {corte} y ya está detallada")

# ---------------------------------------------------------------- 5. Reglas sin historia
citadas = set(re.findall(r"R-[A-Z]{3}-\d\d", mapa))
for r in sorted(reglas - citadas):
    avisos.append(f"la regla {r} no la cita ninguna historia del mapa")

# ---------------------------------------------------------------- 6. Pruebas en el código (opcional)
if "--tests" in sys.argv:
    # Admite varias raíces separadas por comas: backend y frontend viven en repositorios distintos.
    raices = [Path(r) for r in sys.argv[sys.argv.index("--tests") + 1].split(",")]
    ignorar = {"node_modules", "docs", "Docs", ".venv", "venv", ".next", "__pycache__", ".git"}
    codigo = ""
    for raiz in raices:
        for ext in ("*.py", "*.ts", "*.tsx", "*.js", "*.mjs", "*.yml", "*.yaml"):
            for p in raiz.rglob(ext):
                if not ignorar & set(p.parts):
                    codigo += p.read_text(encoding="utf-8", errors="ignore")
    for prueba in sorted(set(n for n, _ in pruebas) | compartidas):
        if prueba not in codigo:
            errores.append(f"la prueba {prueba} no existe en el código")

# ---------------------------------------------------------------- Informe
print(
    f"{len(reglas)} reglas · {len(decisiones)} decisiones · {len(calidad)} requisitos de calidad · "
    f"{len(metricas)} métricas · {len(eventos)} eventos · {len(historias_mapa)} historias "
    f"({len(detalladas)} detalladas) · {len(pruebas)} criterios con prueba"
)
for a in avisos:
    print("AVISO  ", a)
for e in errores:
    print("ERROR  ", e)
print("Sin errores." if not errores else f"{len(errores)} errores.")
sys.exit(1 if errores else 0)
