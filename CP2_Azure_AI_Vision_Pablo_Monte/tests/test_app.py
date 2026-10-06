"""Testes locais: as respostas do Azure são simuladas, sem uso de chave real."""

import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

import requests
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import app


V32 = {
    "description": {"captions": [{"text": "garrafa de água", "confidence": 0.94}]},
    "tags": [{"name": "garrafa", "confidence": 0.98}],
}
V4 = {
    "captionResult": {"text": "a bottle of water", "confidence": 0.95},
    "tagsResult": {"values": [{"name": "bottle", "confidence": 0.97}]},
}
ENV_TESTE = {
    "AZURE_VISION_ENDPOINT": "https://recurso-de-teste.cognitiveservices.azure.com",
    "AZURE_VISION_KEY": "chave-ficticia-apenas-para-testes",
}


def resposta(dados, status=200):
    result = requests.Response()
    result.status_code = status
    result._content = json.dumps(dados).encode("utf-8")
    result.headers["Content-Type"] = "application/json"
    return result


class TesteAPI(unittest.TestCase):
    def setUp(self):
        self.config = patch.multiple(
            app,
            ENDPOINT=ENV_TESTE["AZURE_VISION_ENDPOINT"],
            KEY=ENV_TESTE["AZURE_VISION_KEY"],
        )
        self.config.start()
        self.addCleanup(self.config.stop)

    def test_duas_apis_com_upload_e_url(self):
        casos = [
            (app.analisar_v32, V32, "/vision/v3.2/analyze", "pt", "garrafa de água"),
            (app.analisar_v4, V4, "/computervision/imageanalysis:analyze", "en", "a bottle of water"),
        ]
        for analisar, dados, rota, idioma, descricao in casos:
            for entrada in ({"imagem_bytes": b"imagem-teste"}, {"imagem_url": "https://example.com/imagem.png"}):
                with self.subTest(api=analisar.__name__, origem=list(entrada)[0]):
                    with patch("requests.post", return_value=resposta(dados)) as post:
                        resultado = analisar(**entrada)
                    self.assertEqual(resultado["descricao"], descricao)
                    self.assertTrue(resultado["tags"])
                    self.assertGreater(resultado["confianca"], 0)
                    self.assertEqual(resultado["bruto"], dados)
                    self.assertEqual(post.call_args.args[0], app.ENDPOINT + rota)
                    kwargs = post.call_args.kwargs
                    self.assertEqual(kwargs["params"]["language"], idioma)
                    self.assertEqual(kwargs["headers"]["Ocp-Apim-Subscription-Key"], app.KEY)
                    if "imagem_bytes" in entrada:
                        self.assertEqual(kwargs["data"], entrada["imagem_bytes"])
                        self.assertEqual(kwargs["headers"]["Content-Type"], "application/octet-stream")
                    else:
                        self.assertEqual(kwargs["json"], {"url": entrada["imagem_url"]})
                        self.assertEqual(kwargs["headers"]["Content-Type"], "application/json")

    def test_entradas_invalidas_nao_chamam_azure(self):
        casos = [{}, {"imagem_bytes": b""}, {"imagem_url": "arquivo.png"},
                 {"imagem_bytes": b"foto", "imagem_url": "https://example.com/foto.png"}]
        with patch("requests.post") as post:
            for entrada in casos:
                with self.subTest(entrada=entrada), self.assertRaises(ValueError):
                    app.analisar_v32(**entrada)
            with patch.object(app, "KEY", ""), self.assertRaises(ValueError):
                app.analisar_v4(imagem_bytes=b"foto")
            with patch.object(app, "ENDPOINT", "http://endpoint-invalido"), self.assertRaises(ValueError):
                app.analisar_v32(imagem_bytes=b"foto")
            post.assert_not_called()

    def test_sem_legenda_nao_inventa_descricao(self):
        for analisar in (app.analisar_v32, app.analisar_v4):
            with self.subTest(api=analisar.__name__), patch("requests.post", return_value=resposta({})):
                resultado = analisar(imagem_bytes=b"foto")
                self.assertEqual(resultado["descricao"], "(sem descrição)")
                self.assertEqual(resultado["confianca"], 0)

    def test_erro_http_propagado_e_exibido_sem_chave(self):
        resp = resposta({"error": {"code": "InvalidImage", "message": app.KEY}}, 400)
        with patch("requests.post", return_value=resp), self.assertRaises(requests.HTTPError) as erro:
            app.analisar_v32(imagem_bytes=b"foto")
        mensagem = app.mensagem_de_erro(erro.exception)
        self.assertIn("400", mensagem)
        self.assertNotIn(app.KEY, mensagem)


class TesteInterface(unittest.TestCase):
    def abrir_por_url(self):
        tela = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20).run()
        tela.radio[0].set_value("URL").run()
        tela.text_input[0].set_value("https://example.com/imagem.png").run()
        return tela

    def test_abertura_sem_credenciais(self):
        with patch.dict(os.environ, {"AZURE_VISION_ENDPOINT": "", "AZURE_VISION_KEY": ""}):
            tela = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20).run()
        self.assertEqual(len(tela.exception), 0)
        self.assertTrue(tela.button[0].disabled)
        self.assertIn("Pablo Monte", tela.caption[1].value)
        self.assertIn("96322", tela.caption[1].value)

    def test_analise_url_nas_duas_versoes(self):
        for versao, dados, descricao in [
            ("v3.2 (descrição em português)", V32, "garrafa de água"),
            ("v4.0 (descrição em inglês)", V4, "a bottle of water"),
        ]:
            with self.subTest(versao=versao), patch.dict(os.environ, ENV_TESTE):
                with patch("requests.post", return_value=resposta(dados)) as post:
                    tela = self.abrir_por_url()
                    tela.sidebar.radio[0].set_value(versao).run()
                    tela.button[0].click().run()
                    self.assertEqual(len(tela.exception), 0)
                    self.assertTrue(any(descricao in item.value for item in tela.markdown))
                    post.assert_called_once()

    def test_timeout_e_limite_na_interface(self):
        casos = [
            (Mock(side_effect=requests.Timeout()), "demorou"),
            (Mock(return_value=resposta({}, 429)), "Limite"),
        ]
        for post, mensagem in casos:
            with self.subTest(mensagem=mensagem), patch.dict(os.environ, ENV_TESTE), patch("requests.post", post):
                tela = self.abrir_por_url()
                tela.button[0].click().run()
                self.assertEqual(len(tela.exception), 0)
                self.assertTrue(any(mensagem in item.value for item in tela.error))


if __name__ == "__main__":
    unittest.main()
