#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
import requests
import warnings

# Отключаем предупреждения о SSL сертификатах
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

def pytest_configure(config):
    """Конфигурация pytest"""
    config.addinivalue_line(
        "markers", "slow: маркировка медленных тестов"
    )

def pytest_sessionstart(session):
    """Действия при старте тестовой сессии"""
    print("\n" + "="*50)
    print("Запуск тестов Redfish API")
    print("="*50)

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Логирование результатов тестов"""
    outcome = yield
    rep = outcome.get_result()
    
    if rep.when == "call" and rep.failed:
        print(f"\nТест {item.name} ПРОВАЛЕН: {rep.longrepr}")
    elif rep.when == "call" and rep.passed:
        print(f"\nТест {item.name} ПРОЙДЕН")