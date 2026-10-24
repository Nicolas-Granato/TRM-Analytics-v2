from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


class TestExportApi:

    def test_export_excel_success_flow(self):
        """Testa o endpoint POST /api/v1/export/excel com payload válido de divergências."""
        payload = {
            "enterprise_name": "EMPRESA DE TESTE LTDA",
            "items": [
                {
                    "audit_status": "CRITICAL",
                    "access_key": "35230100000000000000550010000000011000000001",
                    "valor_cents": 150000
                },
                {
                    "audit_status": "OK",
                    "access_key": "35230100000000000000550010000000011000000002",
                    "valor_cents": 200000
                }
            ]
        }

        response = client.post("/api/v1/export/excel", json=payload)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert "attachment; filename=" in response.headers["content-disposition"]
        assert len(response.content) > 0

    def test_export_excel_empty_items_returns_bad_request(self):
        """Valida se uma lista de itens vazia dispara HTTP 400."""
        payload = {
            "enterprise_name": "EMPRESA VAZIA",
            "items": []
        }

        response = client.post("/api/v1/export/excel", json=payload)

        assert response.status_code == 400
        assert "O DataFrame de auditoria está vazio" in response.json()["detail"] or "vazia" in response.json()["detail"]