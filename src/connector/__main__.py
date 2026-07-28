"""`python -m connector` — ENTRYPOINT Dockerfilu i lokální CLI vstup.

Tento soubor je **identický ve všech konektorech**. Logging, PII salt i
startovací kontroly řeší `run_connector`; měnit se tu má nanejvýš to, zda
konektor předává `test_connection` a `pii`.
"""

from __future__ import annotations

from openmcp_sdk import run_connector

from connector.pii_fields import POLICY
from connector.server import mcp, test_connection

run_connector(
    "connector.yaml",
    mcp,
    test_connection=test_connection,  # musí odpovídat capabilities.supports_test
    pii=POLICY,  # musí odpovídat runtime.pii_salt
)
