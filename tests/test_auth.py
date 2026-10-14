from tests.conftest import PASSWORD


def test_register_creates_a_customer(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "Jane@Example.com", "full_name": "Jane Doe", "password": "Secret123"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "jane@example.com"  # stored in lowercase
    assert body["role"] == "customer"
    assert "password" not in body and "hashed_password" not in body


def test_register_rejects_duplicate_email(client, customer):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": customer.email, "full_name": "Someone", "password": "Secret123"},
    )
    assert response.status_code == 409


def test_register_rejects_weak_password(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "jane@example.com", "full_name": "Jane Doe", "password": "alllowercase"},
    )
    assert response.status_code == 422


def test_register_rejects_unknown_fields(client):
    # A customer must not be able to make themselves admin.
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "jane@example.com", "full_name": "Jane", "password": "Secret123", "role": "admin"},
    )
    assert response.status_code == 422


def test_login_returns_tokens(client, customer):
    response = client.post("/api/v1/auth/login", data={"username": customer.email, "password": PASSWORD})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"] and body["refresh_token"]


def test_login_accepts_the_swagger_authorize_form(client, customer):
    # Swagger's "Authorize" button also sends grant_type and scope: they are simply ignored.
    response = client.post(
        "/api/v1/auth/login",
        data={"grant_type": "password", "username": customer.email, "password": PASSWORD, "scope": ""},
    )
    assert response.status_code == 200


def test_login_with_wrong_password(client, customer):
    response = client.post("/api/v1/auth/login", data={"username": customer.email, "password": "Wrong12345"})
    assert response.status_code == 401


def test_protected_route_requires_a_token(client):
    assert client.get("/api/v1/users/me").status_code == 401


def test_me_returns_the_logged_in_user(client, customer, customer_headers):
    response = client.get("/api/v1/users/me", headers=customer_headers)
    assert response.status_code == 200
    assert response.json()["email"] == customer.email


def test_refresh_token_gives_new_tokens(client, customer):
    tokens = client.post("/api/v1/auth/login", data={"username": customer.email, "password": PASSWORD}).json()

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 200

    # A refresh token can NOT be used as an access token.
    response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {tokens['refresh_token']}"})
    assert response.status_code == 401


def test_customer_cannot_list_users(client, customer_headers):
    assert client.get("/api/v1/users", headers=customer_headers).status_code == 403


def test_admin_can_deactivate_a_user(client, customer, admin_headers):
    response = client.patch(f"/api/v1/users/{customer.id}", json={"is_active": False}, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["is_active"] is False

    # A disabled user can't log in anymore.
    response = client.post("/api/v1/auth/login", data={"username": customer.email, "password": PASSWORD})
    assert response.status_code == 403
