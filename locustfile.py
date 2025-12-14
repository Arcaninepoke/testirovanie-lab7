from locust import HttpUser, task, between
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class RedfishUser(HttpUser):
    """Пользователь для нагрузочного тестирования Redfish API"""
    
    host = "https://localhost:2443"
    wait_time = between(1, 3)
    
    def on_start(self):
        """Инициализация пользователя при начале теста"""
        self.credentials = ("root", "0penBmc")
    
    @task
    def fetch_system_information(self):
        """Получение общей информации о системе"""
        self.client.get(
            "/redfish/v1/Systems/system",
            auth=self.credentials,
            verify=False,
            name="01_System_Information"
        )
    
    @task
    def verify_power_state(self):
        """Проверка текущего состояния питания системы"""
        with self.client.get(
            "/redfish/v1/Systems/system",
            auth=self.credentials,
            verify=False,
            name="02_Power_State_Verification",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    power_state = response.json().get("PowerState")
                    valid_power_states = {"On", "Off", "PoweringOn", "PoweringOff"}
                    
                    if power_state in valid_power_states:
                        response.success()
                    else:
                        response.failure(f"Недопустимое состояние питания: {power_state}")
                except ValueError:
                    response.failure("Некорректный JSON-ответ")
            else:
                response.failure(f"Ошибка HTTP: {response.status_code}")