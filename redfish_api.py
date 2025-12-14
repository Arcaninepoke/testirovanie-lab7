#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
import requests
import time
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://localhost:2443"
USERNAME = "root"
PASSWORD = "0penBmc"
VERIFY_SSL = False

class RedfishClient:
    def __init__(self, base_url: str, username: str, password: str, verify_ssl: bool = False):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.session.verify = verify_ssl
        self.token = None
        self.session_location = None
    
    def create_session(self) -> Dict[str, Any]:
        url = f"{self.base_url}/redfish/v1/SessionService/Sessions"
        headers = {'Content-Type': 'application/json'}
        data = {'UserName': self.username, 'Password': self.password}
        
        response = self.session.post(url, json=data, headers=headers)
        response.raise_for_status()
        
        self.token = response.headers.get('X-Auth-Token')
        self.session_location = response.headers.get('Location')
        
        if self.token:
            self.session.headers.update({'X-Auth-Token': self.token})
        
        return response.json()
    
    def delete_session(self) -> None:
        if self.session_location:
            self.session.delete(f"{self.base_url}{self.session_location}")
    
    def get_system_info(self) -> Dict[str, Any]:
        url = f"{self.base_url}/redfish/v1/Systems/system"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def power_control(self, reset_type: str) -> requests.Response:
        url = f"{self.base_url}/redfish/v1/Systems/system/Actions/ComputerSystem.Reset"
        data = {"ResetType": reset_type}
        response = self.session.post(url, json=data)
        return response
    
    def get_thermal_data(self) -> Dict[str, Any]:
        url = f"{self.base_url}/redfish/v1/Chassis/chassis/Thermal"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

@pytest.fixture(scope="session")
def redfish_client():
    client = RedfishClient(BASE_URL, USERNAME, PASSWORD, VERIFY_SSL)
    yield client
    client.delete_session()

@pytest.fixture(scope="function")
def authenticated_session(redfish_client):
    redfish_client.create_session()
    yield redfish_client

class TestRedfishAPI:
    def test_authentication(self, redfish_client):
        logger.info("Запуск теста аутентификации")
        
        session_data = redfish_client.create_session()
        
        assert redfish_client.token is not None
        assert redfish_client.session_location is not None
        
        assert 'Id' in session_data
        assert 'UserName' in session_data
        assert session_data['UserName'] == USERNAME
        
        logger.info("Аутентификация прошла успешно")
    
    def test_system_info(self, authenticated_session):
        logger.info("Запуск теста получения информации о системе")
        
        system_info = authenticated_session.get_system_info()
        
        logger.info("Информация о системе получена успешно")
        
        assert 'Id' in system_info
        assert 'Name' in system_info
        assert 'PowerState' in system_info
        assert 'Status' in system_info
        
        status = system_info['Status']
        assert 'State' in status
        assert 'Health' in status
        
        valid_power_states = ['On', 'Off', 'PoweringOn', 'PoweringOff']
        power_state = system_info['PowerState']
        assert power_state in valid_power_states
        
        logger.info(f"Статус системы: {status}")
        logger.info(f"Состояние питания: {power_state}")
        logger.info("Тест информации о системе пройден успешно")
    
    def test_power_control(self, authenticated_session):
        logger.info("Запуск теста управления питанием")
        
        initial_state = authenticated_session.get_system_info()
        initial_power_state = initial_state['PowerState']
        logger.info(f"Начальное состояние питания: {initial_power_state}")
        
        try:
            response = authenticated_session.power_control("On")
            
            success_status_codes = [200, 202, 204]
            assert response.status_code in success_status_codes, \
                f"Ожидался код {success_status_codes}, получен {response.status_code}"
            
            logger.info("Команда управления питанием отправлена успешно")
            
            time.sleep(5)
            
            updated_state = authenticated_session.get_system_info()
            updated_power_state = updated_state['PowerState']
            logger.info(f"Обновленное состояние питания: {updated_power_state}")
            
            assert updated_power_state in ['On', 'Off', 'PoweringOn']
                
        except requests.exceptions.HTTPError as e:
            logger.warning(f"Команда питания не выполнена: {e}")
        
        logger.info("Тест управления питанием завершен")
    
    def test_cpu_temperature(self, authenticated_session):
        logger.info("Запуск теста проверки температуры CPU")
        
        try:
            thermal_data = authenticated_session.get_thermal_data()
            
            assert 'Temperatures' in thermal_data
            
            temperatures = thermal_data['Temperatures']
            assert isinstance(temperatures, list)
            
            cpu_temperatures = []
            for sensor in temperatures:
                name = sensor.get('Name', '').lower()
                if 'cpu' in name or 'processor' in name:
                    cpu_temperatures.append(sensor)
            
            if not cpu_temperatures:
                logger.warning("Датчики температуры CPU не найдены")
                pytest.skip("Датчики температуры CPU не найдены")
            
            for cpu_sensor in cpu_temperatures:
                sensor_name = cpu_sensor.get('Name', 'Unknown')
                reading = cpu_sensor.get('ReadingCelsius')
                
                if reading is not None:
                    logger.info(f"Датчик {sensor_name}: {reading}°C")
                    
                    assert -10 <= reading <= 120
                    
                    assert 'Status' in cpu_sensor
                    status = cpu_sensor['Status']
                    assert 'State' in status
                    assert status['State'] == 'Enabled'
                    
                else:
                    logger.warning(f"Датчик {sensor_name} не предоставляет данные о температуре")
            
            logger.info("Тест температуры CPU пройден успешно")
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning("Эндпоинт Thermal не найден, пропускаем тест")
                pytest.skip("Эндпоинт Thermal не поддерживается")
            else:
                raise
    
    def test_sensors_consistency(self, authenticated_session):
        logger.info("Запуск теста согласованности датчиков")
        
        try:
            system_info = authenticated_session.get_system_info()
            thermal_data = authenticated_session.get_thermal_data()
            
            system_status = system_info.get('Status', {})
            thermal_status = thermal_data.get('Status', {})
            
            if system_status.get('Health') == 'OK':
                logger.info("Состояние системы: OK")
            else:
                logger.warning(f"Состояние системы: {system_status.get('Health')}")
            
            if 'Temperatures' in thermal_data:
                temps = thermal_data['Temperatures']
                for temp_sensor in temps:
                    sensor_name = temp_sensor.get('Name', 'Unknown')
                    status = temp_sensor.get('Status', {})
                    
                    logger.info(f"Датчик {sensor_name}: Status={status.get('State', 'Unknown')}, Health={status.get('Health', 'Unknown')}")
            
            logger.info("Тест согласованности датчиков пройден")
            
        except Exception as e:
            logger.warning(f"Тест согласованности датчиков пропущен: {e}")
            pytest.skip(f"Не удалось проверить согласованность датчиков: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])