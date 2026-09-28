"""Testes da API. Rode com: python -m unittest -v"""
import os
import tempfile
import unittest

import app as modulo


class TesteBase(unittest.TestCase):
    def setUp(self):
        # cada teste usa um banco temporário novo
        self.pasta = tempfile.TemporaryDirectory()
        modulo.DATABASE = os.path.join(self.pasta.name, "teste.db")
        modulo.API_KEY = None
        modulo.init_db()
        self.client = modulo.app.test_client()

    def tearDown(self):
        self.pasta.cleanup()

    def criar(self, **dados):
        dados.setdefault("titulo", "Tarefa de teste")
        return self.client.post("/tarefas", json=dados)


class TesteCRUD(TesteBase):
    def test_criar_retorna_201(self):
        r = self.criar(titulo="Estudar Flask", descricao="CRUD")
        self.assertEqual(r.status_code, 201)
        corpo = r.get_json()
        self.assertEqual(corpo["titulo"], "Estudar Flask")
        self.assertFalse(corpo["concluida"])

    def test_listar_e_filtrar(self):
        self.criar(titulo="a")
        self.criar(titulo="b", concluida=True)
        self.assertEqual(len(self.client.get("/tarefas").get_json()), 2)
        feitas = self.client.get("/tarefas?concluida=true").get_json()
        self.assertEqual([t["titulo"] for t in feitas], ["b"])

    def test_buscar_existente_e_inexistente(self):
        id_ = self.criar().get_json()["id"]
        self.assertEqual(self.client.get(f"/tarefas/{id_}").status_code, 200)
        self.assertEqual(self.client.get("/tarefas/999").status_code, 404)

    def test_atualizar(self):
        id_ = self.criar().get_json()["id"]
        r = self.client.put(f"/tarefas/{id_}", json={"concluida": True})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["concluida"])

    def test_apagar(self):
        id_ = self.criar().get_json()["id"]
        self.assertEqual(self.client.delete(f"/tarefas/{id_}").status_code, 204)
        self.assertEqual(self.client.delete(f"/tarefas/{id_}").status_code, 404)


class TesteValidacao(TesteBase):
    def test_titulo_vazio(self):
        self.assertEqual(self.criar(titulo="   ").status_code, 400)

    def test_titulo_muito_longo(self):
        self.assertEqual(self.criar(titulo="x" * 121).status_code, 400)

    def test_tipo_errado(self):
        self.assertEqual(self.criar(concluida="sim").status_code, 400)

    def test_corpo_nao_json(self):
        r = self.client.post("/tarefas", data="lixo", content_type="text/plain")
        self.assertEqual(r.status_code, 400)

    def test_filtro_invalido(self):
        self.assertEqual(self.client.get("/tarefas?concluida=talvez").status_code, 400)

    def test_sql_injection_nao_funciona(self):
        self.criar(titulo="x'); DROP TABLE tarefas;--")
        self.assertEqual(len(self.client.get("/tarefas").get_json()), 1)


class TesteAutenticacao(TesteBase):
    def test_sem_chave_configurada_libera(self):
        self.assertEqual(self.client.get("/tarefas").status_code, 200)

    def test_com_chave_configurada(self):
        modulo.API_KEY = "segredo"
        self.assertEqual(self.client.get("/tarefas").status_code, 401)
        errada = self.client.get("/tarefas", headers={"X-API-Key": "errada"})
        self.assertEqual(errada.status_code, 401)
        certa = self.client.get("/tarefas", headers={"X-API-Key": "segredo"})
        self.assertEqual(certa.status_code, 200)


if __name__ == "__main__":
    unittest.main()
