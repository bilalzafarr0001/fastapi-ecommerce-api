from decimal import Decimal

from app.core.config import settings
from app.modules.categories.models import Category
from app.modules.products.models import Product


def test_admin_can_create_a_product(client, admin_headers, category):
    response = client.post(
        "/api/v1/products",
        json={"name": "Keyboard", "price": "49.90", "stock": 5, "category_id": category.id},
        headers=admin_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["price"] == "49.90"  # Decimals are sent as strings
    assert body["category"] == {"id": category.id, "name": "Electronics"}
    assert body["in_stock"] is True  # computed field


def test_customer_cannot_create_a_product(client, customer_headers, category):
    response = client.post(
        "/api/v1/products",
        json={"name": "Keyboard", "price": "49.90", "stock": 5, "category_id": category.id},
        headers=customer_headers,
    )
    assert response.status_code == 403


def test_product_validation(client, admin_headers, category):
    bad_products = [
        {"name": "Keyboard", "price": "-1", "stock": 5, "category_id": category.id},  # negative price
        {"name": "Keyboard", "price": "9.999", "stock": 5, "category_id": category.id},  # 3 decimals
        {"name": "K", "price": "9.99", "stock": 5, "category_id": category.id},  # name too short
        {"name": "Keyboard", "price": "9.99", "stock": -3, "category_id": category.id},  # negative stock
    ]
    for product in bad_products:
        response = client.post("/api/v1/products", json=product, headers=admin_headers)
        assert response.status_code == 422, product


def test_list_products_with_filters_and_pagination(client, db, category):
    for name, price, stock in [("Phone", "500", 3), ("Phone Case", "15", 0), ("Laptop", "1200", 2)]:
        db.add(Product(name=name, price=Decimal(price), stock=stock, category=category))
    db.commit()

    body = client.get("/api/v1/products", params={"search": "phone"}).json()
    assert body["total"] == 2

    body = client.get("/api/v1/products", params={"in_stock": True, "sort_by": "price", "sort_order": "asc"}).json()
    assert [item["name"] for item in body["items"]] == ["Phone", "Laptop"]

    body = client.get("/api/v1/products", params={"page": 2, "size": 2}).json()
    assert body["total"] == 3 and body["pages"] == 2 and len(body["items"]) == 1


def test_invalid_price_range_is_rejected(client):
    response = client.get("/api/v1/products", params={"min_price": 100, "max_price": 10})
    assert response.status_code == 400


def test_deleted_product_is_hidden(client, admin_headers, product):
    assert client.delete(f"/api/v1/products/{product.id}", headers=admin_headers).status_code == 204
    assert client.get(f"/api/v1/products/{product.id}").status_code == 404


def test_get_category_includes_its_products(client, db, category):
    books = Category(name="Books")
    db.add_all([
        Product(name="Phone", price=Decimal("500"), stock=3, category=category),
        Product(name="Laptop", price=Decimal("1200"), stock=2, category=category),
        Product(name="Old Phone", price=Decimal("50"), stock=1, category=category, is_active=False),  # hidden
        Product(name="Clean Code", price=Decimal("34.50"), stock=5, category=books),  # other category
    ])
    db.commit()

    response = client.get(f"/api/v1/categories/{category.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Electronics"
    assert sorted(p["name"] for p in body["products"]) == ["Laptop", "Phone"]  # no hidden or other-category products

    assert client.get("/api/v1/categories/999").status_code == 404


def test_cannot_delete_a_category_that_has_products(client, admin_headers, product):
    response = client.delete(f"/api/v1/categories/{product.category_id}", headers=admin_headers)
    assert response.status_code == 409


def test_hidden_products_also_block_category_delete(client, db, admin_headers, product):
    # get_category() only loads VISIBLE products, but hidden ones still point to the category.
    product.is_active = False
    db.commit()

    assert client.get(f"/api/v1/categories/{product.category_id}").json()["products"] == []
    response = client.delete(f"/api/v1/categories/{product.category_id}", headers=admin_headers)
    assert response.status_code == 409


def test_upload_product_image(client, admin_headers, product, tmp_path, monkeypatch):
    # Save the file in a temporary folder instead of the real uploads/ folder.
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    (tmp_path / "products").mkdir()

    response = client.post(
        f"/api/v1/products/{product.id}/image",
        files={"image": ("photo.png", b"fake-png-bytes", "image/png")},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["image_url"].startswith("/uploads/products/")

    response = client.post(
        f"/api/v1/products/{product.id}/image",
        files={"image": ("notes.txt", b"hello", "text/plain")},
        headers=admin_headers,
    )
    assert response.status_code == 400
