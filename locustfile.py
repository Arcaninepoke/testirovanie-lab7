from locust import HttpUser, task

class OpenBNCUser(HttpUser):
    wait_time = 2

    @task(3)
    def get_system_info(self):
        self.client.get(
            "/redfish/v1/systems/system",
            auth=("root", "OpenBmc"),
            verify=False
        )

    @task(2)
    def get_power_state(self):
        self.client.get(
            "/redfish/v1/Chassis/chassis",
            auth=("root", "OpenBmc"),
            verify=False
        )

    @task(1)
    def get_service_root(self):
        self.client.get(
            "/redfish/v1/",
            auth=("root", "OpenBmc"),
            verify=False
        )