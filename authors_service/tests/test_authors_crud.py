from fastapi.testclient import TestClient
from app.main import app
import urllib.request
import json

client = TestClient(app)


# Esto simula la respuesta de urllib.request.urlopen(...)
class DummyResponse:
    def __init__(self, body: str, status: int = 200):
        self._body = body.encode("utf-8")
        self.status = status

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_get_authors_returns_list():
    r = client.get("/authors/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_post_author_creates_author():
    payload = {"name": "Ada Lovelace", "bio": "Pionera"}
    r = client.post("/authors/", json=payload)

    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Ada Lovelace"
    assert body["bio"] == "Pionera"
    assert "id" in body


def test_put_author_books_assigns_books(monkeypatch):
    # 1) Crear un autor (real, en tu DB)
    r = client.post("/authors/", json={"name": "Autor Test", "bio": None})
    assert r.status_code == 200
    author_id = r.json()["id"]

    # 2) Simular "books_service" SIN llamarlo de verdad
    #    Tu endpoint hace:
    #      GET  /books/10/authors
    #      PUT  /books/10/authors
    #    Aquí devolvemos respuestas falsas (pero válidas)
    def fake_urlopen(req, timeout=5):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        method = req.get_method() if hasattr(req, "get_method") else "GET"

        # Simula: GET http://books_service:8000/books/10/authors
        if method == "GET" and "/books/10/authors" in url:
            return DummyResponse(json.dumps([{"id": 77}]))  # autores actuales del libro

        # Simula: PUT http://books_service:8000/books/10/authors
        if method == "PUT" and "/books/10/authors" in url:
            payload = json.loads(req.data.decode("utf-8"))  # {"author_ids":[...]}
            # devolvemos lo mismo que un books_service "correcto" podría devolver
            return DummyResponse(json.dumps({"book_id": 10, "author_ids": payload["author_ids"]}))

        raise AssertionError(f"Unexpected call: {method} {url}")

    # Reemplaza urlopen real por el fake SOLO en este test
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    # 3) Ejecutar el PUT "real" de tu API
    r2 = client.put(f"/authors/{author_id}/books", json={"book_ids": [10]})
    assert r2.status_code == 200

    body = r2.json()
    assert body["author_id"] == author_id
    assert body["book_ids"] == [10]
    assert len(body["updated_books"]) == 1
    assert body["updated_books"][0]["book_id"] == 10
    # lo importante: que tu servicio añadió author_id a la lista
    assert author_id in body["updated_books"][0]["author_ids"]


def test_get_author_404():
    r = client.get("/authors/999999999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Author not found"
