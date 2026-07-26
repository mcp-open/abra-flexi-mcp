"""Společná sada testů ze SDK.

Tento soubor se kopíruje do konektorů **1:1**, mění se jen konfigurace třídy.
"""

from __future__ import annotations

from openmcp_sdk.testing.conformance import ConnectorConformance


class TestConformance(ConnectorConformance):
    manifest = "connector.yaml"
    server = "connector.server:mcp"
    test_connection = "connector.server:test_connection"
    pii_policy = "connector.pii_fields:POLICY"
    package = "abraflexi-mcp"
    # Credentials potřebné pro local-stdio start v subprocesu.
    local_env = {
        "ABRAFLEXI_API_URL": "https://demo.flexibee.eu:5434",
        "ABRAFLEXI_COMPANY": "demo",
        "ABRAFLEXI_USERNAME": "winstrom",
        "ABRAFLEXI_PASSWORD": "test-heslo",
    }
