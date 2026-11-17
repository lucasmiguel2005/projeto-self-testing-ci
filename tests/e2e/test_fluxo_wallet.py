from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from src.controllers.api import criar_app
from src.services.antifraude_client import AntiFraudeClient


@pytest.fixture
def antifraude():
    return Mock(spec=AntiFraudeClient)


@pytest.fixture
def cliente(antifraude):
    return TestClient(criar_app(antifraude=antifraude))


def criar_conta(cliente, titular, saldo):
    resposta = cliente.post(
        "/contas", json={"titular": titular, "saldo_inicial": saldo}
    )
    assert resposta.status_code == 201
    return resposta.json()["numero"]


def transferir(cliente, origem, destino, valor, chave="chave-1"):
    return cliente.post(
        "/transferencias",
        json={"origem": origem, "destino": destino, "valor": valor},
        headers={"Idempotency-Key": chave},
    )


def test_fluxo_completo_conta_transferencia_e_extrato(cliente, antifraude):
    ana = criar_conta(cliente, "Ana", "100.00")
    bruno = criar_conta(cliente, "Bruno", "50.00")

    resposta = transferir(cliente, ana, bruno, "30.00")

    assert resposta.status_code == 200
    assert cliente.get(f"/contas/{ana}").json()["saldo"] == "70.00"
    assert cliente.get(f"/contas/{bruno}").json()["saldo"] == "80.00"

    extrato = cliente.get(f"/contas/{ana}/extrato").json()
    assert [(i["tipo"], i["valor"]) for i in extrato] == [("debito", "30.00")]
    antifraude.notificar.assert_called_once()


def test_repetir_a_chave_de_idempotencia_nao_transfere_de_novo(cliente):
    ana = criar_conta(cliente, "Ana", "100.00")
    bruno = criar_conta(cliente, "Bruno", "50.00")

    assert transferir(cliente, ana, bruno, "30.00").status_code == 200
    assert transferir(cliente, ana, bruno, "30.00").status_code == 200

    assert cliente.get(f"/contas/{ana}").json()["saldo"] == "70.00"
    assert cliente.get(f"/contas/{bruno}").json()["saldo"] == "80.00"


def test_saldo_insuficiente_devolve_422_e_nao_altera_saldos(cliente):
    ana = criar_conta(cliente, "Ana", "20.00")
    bruno = criar_conta(cliente, "Bruno", "50.00")

    resposta = transferir(cliente, ana, bruno, "80.00")

    assert resposta.status_code == 422
    assert cliente.get(f"/contas/{ana}").json()["saldo"] == "20.00"
    assert cliente.get(f"/contas/{bruno}").json()["saldo"] == "50.00"


def test_transferir_para_conta_inexistente_devolve_404(cliente):
    ana = criar_conta(cliente, "Ana", "100.00")

    assert transferir(cliente, ana, 999, "10.00").status_code == 404
    assert cliente.get("/contas/999").status_code == 404


def test_extrato_filtra_por_tipo(cliente):
    ana = criar_conta(cliente, "Ana", "100.00")
    bruno = criar_conta(cliente, "Bruno", "50.00")
    transferir(cliente, ana, bruno, "30.00", "c1")
    transferir(cliente, bruno, ana, "10.00", "c2")

    creditos = cliente.get(
        f"/contas/{ana}/extrato", params={"tipo": "credito"}
    ).json()

    assert [(i["tipo"], i["valor"]) for i in creditos] == [("credito", "10.00")]


def test_transferencia_sem_chave_de_idempotencia_e_rejeitada(cliente):
    ana = criar_conta(cliente, "Ana", "100.00")
    bruno = criar_conta(cliente, "Bruno", "50.00")

    resposta = cliente.post(
        "/transferencias",
        json={"origem": ana, "destino": bruno, "valor": "10.00"},
    )

    assert resposta.status_code == 422