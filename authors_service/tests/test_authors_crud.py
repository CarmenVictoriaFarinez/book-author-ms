from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

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
    assert "id" in body  # lo mínimo para validar creación

def test_put_author_books_empty_list_is_ok():
    # 1) crear autor
    r = client.post("/authors/", json={"name": "Autor Test", "bio": None})
    assert r.status_code == 200
    author_id = r.json()["id"]

    # 2) PUT con lista vacía (tu endpoint devuelve message y NO llama a books_service)
    r2 = client.put(f"/authors/{author_id}/books", json={"book_ids": []})
    assert r2.status_code == 200

    body = r2.json()
    assert body["author_id"] == author_id
    assert body["updated_books"] == []
    assert body["message"] == "No book_ids provided"

def test_get_author_404():
    r = client.get("/authors/999999999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Author not found"
