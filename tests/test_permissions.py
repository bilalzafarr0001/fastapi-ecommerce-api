"""
Every admin-only route must answer 403 to a customer.

The admin check lives inside each controller function (`check_admin`), so this
test makes sure none of them was forgotten. The ids don't even need to exist:
`check_admin` runs first, before any database lookup.
"""
import pytest

ADMIN_ONLY_ROUTES = [
    ("GET", "/api/v1/users", None),
    ("GET", "/api/v1/users/1", None),
    ("PATCH", "/api/v1/users/1", {"is_active": False}),
    ("POST", "/api/v1/categories", {"name": "Toys"}),
    ("PATCH", "/api/v1/categories/1", {"name": "Toys"}),
    ("DELETE", "/api/v1/categories/1", None),
    ("POST", "/api/v1/products", {"name": "Keyboard", "price": "9.99", "stock": 1, "category_id": 1}),
    ("PATCH", "/api/v1/products/1", {"stock": 1}),
    ("DELETE", "/api/v1/products/1", None),
    ("PATCH", "/api/v1/orders/1/status", {"status": "paid"}),
    ("GET", "/api/v1/dashboard/stats", None),
]


# parametrize -> pytest runs this test once for every route in the list
@pytest.mark.parametrize("method, url, body", ADMIN_ONLY_ROUTES)
def test_customer_gets_403_on_admin_routes(client, customer_headers, method, url, body):
    response = client.request(method, url, json=body, headers=customer_headers)
    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access required"}


def test_customer_cannot_upload_a_product_image(client, customer_headers):
    response = client.post(
        "/api/v1/products/1/image",
        files={"image": ("photo.png", b"fake-png-bytes", "image/png")},
        headers=customer_headers,
    )
    assert response.status_code == 403
