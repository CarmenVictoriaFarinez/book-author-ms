from fastapi.testclient import TestClient
from app.main import app
import os
import json
import urllib.request
import urllib.error
import time

client = TestClient(app)

AUTHORS_URL = os.getenv("AUTHORS_SERVICE_URL", "http://authors_service:8000").rstrip("/")


def _create_author(name="Autor Integracion", retries=10, sleep_s=0.3):
    url = f"{AUTHORS_URL}/authors/"
    data = json.dumps({"name": name, "bio": None}).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="POST", headers={"Content-Type": "application/json"}
    )

    last_err = None
    for _ in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            last_err = e
            time.sleep(sleep_s)

    raise last_err


def test_get_books_returns_list():
    r = client.get("/books/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_post_book_with_valid_author_id():
    author = _create_author()
    author_id = author["id"]

    r = client.post("/books/", json={"title": "Libro 1", "description": None, "author_ids": [author_id]})
    assert r.status_code == 200
    book_id = r.json()["id"]

    r2 = client.get(f"/books/{book_id}/authors")
    assert r2.status_code == 200
    authors = r2.json()
    assert isinstance(authors, list)
    assert any(a["id"] == author_id for a in authors)


def test_post_book_with_invalid_author_id_returns_404():
    r = client.post("/books/", json={"title": "Libro X", "description": None, "author_ids": [999999999]})
    assert r.status_code == 404
