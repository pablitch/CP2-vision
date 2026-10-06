"""
Inova Trônica - MVP de Serviço Cognitivo
Envia uma imagem (upload local ou URL) ao Azure AI Vision e mostra a descrição.

CP2 - Cloud Computing & Machine as a Service (MaaS)
Pablo Monte - RM 96322 | Murilo Henrique Costa - RM 96203 | 5EMR
Base: https://github.com/M4ns0urX/Azure-AI-Vision

Executar:  streamlit run app.py
"""

import os
from pathlib import Path
from urllib.parse import urlsplit

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().with_name(".env"))

ENDPOINT = os.getenv("AZURE_VISION_ENDPOINT", "").strip().rstrip("/")
KEY = os.getenv("AZURE_VISION_KEY", "").strip()
TIMEOUT = 30


# ---------------------------------------------------------------------------
# Chamadas à API (REST puro, sem SDK)
# ---------------------------------------------------------------------------
def _montar_requisicao(imagem_bytes: bytes | None, imagem_url: str | None):
    """Define headers e corpo conforme a origem da imagem."""
    if not ENDPOINT or not KEY:
        raise ValueError("Preencha o endpoint e a chave no arquivo .env.")
    endpoint = urlsplit(ENDPOINT)
    if endpoint.scheme != "https" or not endpoint.hostname or endpoint.path or endpoint.query or endpoint.fragment or endpoint.username:
        raise ValueError("Copie somente o endpoint HTTPS do portal Azure, sem a rota da API.")
    if (imagem_bytes is not None) == bool(imagem_url):
        raise ValueError("Selecione uma imagem local ou uma URL pública.")
    headers = {"Ocp-Apim-Subscription-Key": KEY}
    if imagem_bytes is not None:
        if not imagem_bytes:
            raise ValueError("O arquivo selecionado está vazio.")
        headers["Content-Type"] = "application/octet-stream"
        return headers, {"data": imagem_bytes}
    if not url_publica_valida(imagem_url):
        raise ValueError("Informe uma URL HTTP ou HTTPS válida para a imagem.")
    headers["Content-Type"] = "application/json"
    return headers, {"json": {"url": imagem_url}}


def url_publica_valida(url: str | None) -> bool:
    """Confere o formato da URL; o acesso público é verificado pelo Azure."""
    try:
        partes = urlsplit(url or "")
        return bool(partes.scheme in ("http", "https") and partes.hostname and not partes.username and not any(c.isspace() for c in url))
    except ValueError:
        return False


def analisar_v4(imagem_bytes=None, imagem_url=None) -> dict:
    """Image Analysis 4.0 (legenda em inglês; disponível só em algumas regiões)."""
    url = f"{ENDPOINT}/computervision/imageanalysis:analyze"
    params = {
        "api-version": "2024-02-01",
        "features": "caption,tags",
        "language": "en",
        "gender-neutral-caption": "true",
    }
    headers, corpo = _montar_requisicao(imagem_bytes, imagem_url)
    resp = requests.post(url, params=params, headers=headers, timeout=TIMEOUT, allow_redirects=False, **corpo)
    resp.raise_for_status()
    dados = resp.json()

    legenda = dados.get("captionResult", {})
    tags = dados.get("tagsResult", {}).get("values", [])
    return {
        "descricao": legenda.get("text", "(sem descrição)"),
        "confianca": legenda.get("confidence", 0.0),
        "tags": [(t["name"], t["confidence"]) for t in tags],
        "bruto": dados,
    }


def analisar_v32(imagem_bytes=None, imagem_url=None, idioma="pt") -> dict:
    """Analyze v3.2 com descrição e tags em português por padrão."""
    url = f"{ENDPOINT}/vision/v3.2/analyze"
    params = {"visualFeatures": "Description,Tags", "language": idioma}
    headers, corpo = _montar_requisicao(imagem_bytes, imagem_url)
    resp = requests.post(url, params=params, headers=headers, timeout=TIMEOUT, allow_redirects=False, **corpo)
    resp.raise_for_status()
    dados = resp.json()

    legendas = dados.get("description", {}).get("captions", [])
    melhor = legendas[0] if legendas else {"text": "(sem descrição)", "confidence": 0.0}
    tags = dados.get("tags", [])
    return {
        "descricao": melhor["text"],
        "confianca": melhor["confidence"],
        "tags": [(t["name"], t["confidence"]) for t in tags],
        "bruto": dados,
    }


def mensagem_de_erro(exc: requests.HTTPError) -> str:
    if exc.response is None:
        return "Não foi possível obter uma resposta do serviço."
    status = exc.response.status_code
    dicas = {
        401: "Confira a chave e o endpoint do mesmo recurso no arquivo .env.",
        403: "Confira as permissões e as restrições de acesso do recurso Azure.",
        404: "Confira se o endpoint é de um recurso Computer Vision.",
        429: "Limite de requisições atingido. Aguarde antes de tentar novamente.",
    }
    if status in dicas:
        return f"{status} - {dicas[status]}"
    try:
        erro = exc.response.json().get("error", {})
        mensagem = f"{status} - {erro.get('code', '')}: {erro.get('message', '')}"
    except (ValueError, AttributeError):
        mensagem = f"{status} - O serviço recusou a solicitação. Confira a imagem e a configuração."
    return mensagem.replace(KEY, "[chave ocultada]") if KEY else mensagem


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def main():
    st.set_page_config(page_title="CP2 | Pablo Monte | Inova Trônica", page_icon="👁️")
    st.title("👁️ Inova Trônica — Descrição de Imagens")
    st.caption("CP2 • Cloud Computing & Machine as a Service (MaaS) • FIAP • 2026")
    st.caption("Pablo Monte — RM 96322 | Murilo Henrique Costa — RM 96203 | Turma 5EMR")

    with st.sidebar:
        st.header("Configuração")
        if ENDPOINT and KEY:
            st.success("Credenciais configuradas")
            st.text(f"Endpoint:\n{ENDPOINT}")
            st.caption("Chave de acesso protegida")
        else:
            st.error("Defina AZURE_VISION_ENDPOINT e AZURE_VISION_KEY no arquivo .env")

        versao = st.radio(
            "Versão da API",
            ["v3.2 (descrição em português)", "v4.0 (descrição em inglês)"],
            help="A v4.0 só gera legenda em algumas regiões da Azure. "
            "Se der erro de região, use a v3.2.",
        )

    origem = st.radio("Origem da imagem", ["Arquivo local", "URL"], horizontal=True)

    imagem_bytes, imagem_url = None, None
    if origem == "Arquivo local":
        arquivo = st.file_uploader("Escolha uma foto", type=["jpg", "jpeg", "png", "bmp"])
        if arquivo is not None and arquivo.size > 0:
            imagem_bytes = arquivo.getvalue()
            st.image(imagem_bytes, caption=arquivo.name, width="stretch")
    else:
        imagem_url = st.text_input("URL pública da imagem", placeholder="https://...").strip()
        if imagem_url and not url_publica_valida(imagem_url):
            st.warning("Informe uma URL HTTP ou HTTPS válida.")
        elif imagem_url:
            st.image(imagem_url, width="stretch")

    pronto = bool((imagem_bytes or url_publica_valida(imagem_url)) and ENDPOINT and KEY)
    if st.button("Analisar imagem", type="primary", disabled=not pronto):
        with st.spinner("Enviando ao serviço cognitivo..."):
            try:
                if versao.startswith("v4.0"):
                    resultado = analisar_v4(imagem_bytes, imagem_url)
                else:
                    resultado = analisar_v32(imagem_bytes, imagem_url)
            except requests.HTTPError as exc:
                st.error(f"Erro da API: {mensagem_de_erro(exc)}")
                st.stop()
            except requests.Timeout:
                st.error("O Azure demorou a responder. Tente novamente em alguns instantes.")
                st.stop()
            except requests.RequestException:
                st.error("Falha de comunicação com o Azure. Confira a conexão e o endpoint.")
                st.stop()
            except ValueError as exc:
                st.error(f"Não foi possível analisar a imagem: {exc}")
                st.stop()

        st.subheader("Descrição")
        st.markdown(f"### “{resultado['descricao']}”")
        st.progress(resultado["confianca"], text=f"Confiança: {resultado['confianca']:.1%}")

        if resultado["tags"]:
            st.subheader("Tags detectadas")
            st.write(" · ".join(f"`{nome}` ({conf:.0%})" for nome, conf in resultado["tags"][:15]))

        with st.expander("Resposta JSON completa da API"):
            st.json(resultado["bruto"])


if __name__ == "__main__":
    main()
