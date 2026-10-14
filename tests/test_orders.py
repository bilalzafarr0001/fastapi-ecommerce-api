import pytest
from fastapi import WebSocketDisconnect

from tests.conftest import auth_headers, create_user


def place_order(client, headers, product_id, quantity=2):
    return client.post(
        "/api/v1/orders",
        json={"product_id": product_id, "quantity": quantity, "shipping_address": "221B Baker Street, London"},
        headers=headers,
    )


def test_create_order_reduces_stock(client, db, customer_headers, product):
    response = place_order(client, customer_headers, product.id, quantity=2)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert body["product"] == {"id": product.id, "name": "Headphones"}
    assert body["unit_price"] == "19.99"
    assert body["total_amount"] == "39.98"

    db.refresh(product)
    assert product.stock == 8


def test_order_fails_when_stock_is_too_low(client, db, customer_headers, product):
    response = place_order(client, customer_headers, product.id, quantity=50)

    assert response.status_code == 400
    db.refresh(product)
    assert product.stock == 10  # nothing was changed


def test_shipping_address_is_cleaned_and_validated(client, customer_headers, product):
    response = client.post(
        "/api/v1/orders",
        json={"product_id": product.id, "quantity": 1, "shipping_address": "  221B   Baker Street  "},
        headers=customer_headers,
    )
    assert response.status_code == 201
    assert response.json()["shipping_address"] == "221B Baker Street"  # extra spaces removed

    response = client.post(
        "/api/v1/orders",
        json={"product_id": product.id, "quantity": 1, "shipping_address": "            "},  # only spaces
        headers=customer_headers,
    )
    assert response.status_code == 422


def test_customer_cannot_see_someone_elses_order(client, db, customer_headers, product):
    order_id = place_order(client, customer_headers, product.id).json()["id"]
    other_customer = create_user(db, "other@example.com")

    response = client.get(f"/api/v1/orders/{order_id}", headers=auth_headers(other_customer))
    assert response.status_code == 404


def test_cancel_order_restores_stock(client, db, customer_headers, product):
    order_id = place_order(client, customer_headers, product.id, quantity=3).json()["id"]

    response = client.post(f"/api/v1/orders/{order_id}/cancel", headers=customer_headers)

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    db.refresh(product)
    assert product.stock == 10


def test_order_status_flow(client, customer_headers, admin_headers, product):
    order_id = place_order(client, customer_headers, product.id).json()["id"]
    url = f"/api/v1/orders/{order_id}/status"

    # Customers can't change the status
    assert client.patch(url, json={"status": "paid"}, headers=customer_headers).status_code == 403

    for new_status in ["paid", "shipped", "delivered"]:
        response = client.patch(url, json={"status": new_status}, headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["status"] == new_status

    # A delivered order can't go back to pending
    assert client.patch(url, json={"status": "pending"}, headers=admin_headers).status_code == 400


def test_review_requires_a_delivered_order(client, customer_headers, admin_headers, product):
    review_url = f"/api/v1/products/{product.id}/reviews"
    review = {"rating": 5, "comment": "Great!"}

    # Never bought it -> forbidden
    assert client.post(review_url, json=review, headers=customer_headers).status_code == 403

    order_id = place_order(client, customer_headers, product.id).json()["id"]
    for new_status in ["paid", "shipped", "delivered"]:
        client.patch(f"/api/v1/orders/{order_id}/status", json={"status": new_status}, headers=admin_headers)

    response = client.post(review_url, json=review, headers=customer_headers)
    assert response.status_code == 201
    assert response.json()["user"]["full_name"] == "Test User"

    # Only one review per product
    assert client.post(review_url, json=review, headers=customer_headers).status_code == 409

    summary = client.get(f"{review_url}/summary").json()
    assert summary == {"product_id": product.id, "average_rating": 5.0, "review_count": 1}


def test_dashboard_is_admin_only(client, customer_headers, admin_headers, product):
    assert client.get("/api/v1/dashboard/stats", headers=customer_headers).status_code == 403

    place_order(client, customer_headers, product.id, quantity=2)
    stats = client.get("/api/v1/dashboard/stats", headers=admin_headers).json()
    assert stats["total_orders"] == 1
    assert stats["orders_by_status"]["pending"] == 1
    assert stats["total_revenue"] == "39.98"


def test_customer_gets_live_notification(client, customer, customer_headers, admin_headers, product):
    order_id = place_order(client, customer_headers, product.id).json()["id"]
    token = customer_headers["Authorization"].removeprefix("Bearer ")

    with client.websocket_connect(f"/api/v1/notifications/ws?token={token}") as websocket:
        client.patch(f"/api/v1/orders/{order_id}/status", json={"status": "paid"}, headers=admin_headers)
        message = websocket.receive_json()

    assert message == {"event": "order_status_changed", "order_id": order_id, "status": "paid"}


def test_websocket_rejects_invalid_token(client):
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/api/v1/notifications/ws?token=not-a-real-token") as websocket:
            websocket.receive_json()
