import pytest
import requests

BASE_URL = "https://localhost:2443/redfish/v1"
AUTH_DATA = {"UserName": "root", "Password": "0penBmc"}


class RedfishClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False
        self.auth_token = None

    def create_session(self):
        url = f"{BASE_URL}/SessionService/Sessions"
        response = self.session.post(url, json=AUTH_DATA, timeout=10)
        response.raise_for_status()
        self.auth_token = response.headers['X-Auth-Token']
        return self.auth_token

    def get_auth_headers(self):
        return {'X-Auth-Token': self.auth_token}

    def get(self, endpoint):
        url = f"{BASE_URL}/{endpoint.lstrip('/')}"
        return self.session.get(url, headers=self.get_auth_headers(), timeout=10)

    def post(self, endpoint, data=None):
        url = f"{BASE_URL}/{endpoint.lstrip('/')}"
        headers = {**self.get_auth_headers(), 'Content-Type': 'application/json'}
        return self.session.post(url, headers=headers, json=data, timeout=10)


@pytest.fixture
def redfish_client():
    client = RedfishClient()
    client.create_session()
    return client


def test_create_session():
    client = RedfishClient()
    token = client.create_session()
    assert token is not None


def test_system(redfish_client):
    response = redfish_client.get("Systems/system")
    assert response.status_code == 200
    data = response.json()
    assert 'Status' in data
    assert 'PowerState' in data


def test_power(redfish_client):
    response = redfish_client.post(
        "Systems/system/Actions/ComputerSystem.Reset",
        {"ResetType": "On"}
    )
    assert response.status_code in [200, 202, 204]
