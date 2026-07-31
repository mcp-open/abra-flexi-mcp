# Build kontext je NADŘAZENÝ adresář (obsahuje `sdk/` i adresář konektoru)
# — openmcp-sdk je lokální závislost, ne PyPI balík.
#
# ⚠️ TŘI místa níže obsahují SLUG:
#     COPY abraflexi ./abraflexi  ·  RUN pip install … ./abraflexi  ·  WORKDIR /app/abraflexi
# `deploy/Makefile` přejmenovává adresář repozitáře na slug.
# Hlídá to `tests/test_packaging.py` (kontroluje všechna tři) i
# `openmcp-sdk validate`.
# Debian slim nyní obsahuje neopravitelné HIGH/CRITICAL OS nálezy. Explicitní
# Alpine release zachovává oficiální CPython image a zmenšuje finální OS
# plochu; Python patch i multiarch manifest jsou připnuté.
FROM python:3.13.14-alpine3.24@sha256:399babc8b49529dabfd9c922f2b5eea81d611e4512e3ed250d75bd2e7683f4b0

WORKDIR /app

# sdk nejdřív — konektor na něj závisí v pyproject.toml.
COPY sdk ./sdk
COPY abraflexi ./abraflexi
# Síťové závislosti jsou plně tranzitivně uzamčené a hashované. SDK i
# konektor se potom instalují výhradně z přesného lokálního snapshotu; pip
# proto nikdy nepotřebuje git ani neřeší mutable dependency metadata.
RUN pip install --no-cache-dir --no-compile --only-binary=:all: \
      --require-hashes -r ./abraflexi/release/runtime-requirements.lock \
    && pip install --no-cache-dir --no-compile --no-deps --no-build-isolation \
      ./sdk ./abraflexi \
    && pip check

# Non-root. UID musí sedět s `runAsUser: 10001` v podSecurityContext.
# BusyBox `adduser` je součást Alpine base; nepřidáváme balík `shadow` jen
# kvůli vytvoření runtime identity.
RUN addgroup -S -g 10001 openmcp \
    && adduser -S -D -H -u 10001 -G openmcp -s /sbin/nologin openmcp
USER 10001

# `python -m connector` volá run_connector("connector.yaml", …) s relativní
# cestou, takže WORKDIR musí být adresář obsahující manifest. Balík
# `connector` je nainstalovaný přes pip, tedy importovatelný nezávisle na cwd.
WORKDIR /app/abraflexi

EXPOSE 8000

# HEALTHCHECK tu záměrně není: v k8s běží readiness/liveness probe z
# `runtime.health_path` a docker HEALTHCHECK by byl mrtvý kód.
ENTRYPOINT ["python", "-m", "connector"]
