# Build kontext je NADŘAZENÝ adresář (obsahuje `sdk/` i adresář konektoru)
# — openmcp-sdk je lokální závislost, ne PyPI balík.
#
# ⚠️ TŘI místa níže obsahují SLUG:
#     COPY abraflexi ./abraflexi  ·  RUN pip install … ./abraflexi  ·  WORKDIR /app/abraflexi
# `deploy/Makefile` přejmenovává adresář repozitáře na slug.
# Hlídá to `tests/test_packaging.py` (kontroluje všechna tři) i
# `openmcp-sdk validate`.
FROM python:3.13-slim

WORKDIR /app

# sdk nejdřív — konektor na něj závisí v pyproject.toml.
COPY sdk ./sdk
COPY abraflexi ./abraflexi
# Závislosti se instalují zvlášť a teprve pak sdk + konektor s `--no-deps`.
# Bez toho by pip řešil i `openmcp-sdk @ git+https://…` z pyproject.toml,
# sáhl po `git`, který v image není, a build by spadl — přestože SDK je
# přímo tady v `./sdk`. Git reference je pravda pro toho, kdo instaluje
# z čistého klonu; image staví z přesného snapshotu podle `.sdk-ref`.
RUN pip install --no-cache-dir --no-compile ./sdk \
    && pip install --no-cache-dir --no-compile \
      "fastmcp>=2.11,<3" "pydantic>=2.6,<3" "httpx>=0.28,<0.29" "xmltodict>=0.13,<1" \
    && pip install --no-cache-dir --no-compile --no-deps ./abraflexi \
    && pip check

# Non-root. UID musí sedět s `runAsUser: 10001` v podSecurityContext.
RUN useradd --uid 10001 --system --no-create-home --shell /usr/sbin/nologin openmcp
USER 10001

# `python -m connector` volá run_connector("connector.yaml", …) s relativní
# cestou, takže WORKDIR musí být adresář obsahující manifest. Balík
# `connector` je nainstalovaný přes pip, tedy importovatelný nezávisle na cwd.
WORKDIR /app/abraflexi

EXPOSE 8000

# HEALTHCHECK tu záměrně není: v k8s běží readiness/liveness probe z
# `runtime.health_path` a docker HEALTHCHECK by byl mrtvý kód.
ENTRYPOINT ["python", "-m", "connector"]
