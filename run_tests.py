#!/usr/bin/env python3
"""
Главный скрипт для запуска всех тестов системы
"""

import subprocess
import sys
import time
import json
from pathlib import Path

def run_command(cmd, description):
    """Запуск команды с выводом результата"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    
    start_time = time.time()
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        end_time = time.time()
        
        print(f"Команда: {cmd}")
        print(f"Время выполнения: {end_time - start_time:.2f} секунд")
        print(f"Exit code: {result.returncode}")
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        return result.returncode == 0, end_time - start_time
        
    except Exception as e:
        print(f"Ошибка выполнения команды: {e}")
        return False, 0

def main():
    """Главная функция запуска тестов"""
    print("🧪 ЗАПУСК КОМПЛЕКСНОГО ТЕСТИРОВАНИЯ СИСТЕМЫ")
    print("=" * 60)
    
    # Результаты тестирования
    results = {
        "unit_tests": {},
        "integration_tests": {},
        "load_tests": {},
        "security_tests": {},
        "overall": {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "total_time": 0
        }
    }
    
    # 1. Unit тесты
    print("\n📋 ЭТАП 1: Unit тесты")
    
    unit_test_files = [
        ("llm/test_api.py", "LLM API тесты"),
        ("db/test_models.py", "Database Models тесты"),
        ("worker/test_tasks.py", "Worker Tasks тесты"),
        ("ui/test_app.py", "UI App тесты")
    ]
    
    for test_file, description in unit_test_files:
        success, duration = run_command(
            f"python3 -m pytest {test_file} -v --tb=short",
            description
        )
        results["unit_tests"][test_file] = {
            "success": success,
            "duration": duration,
            "description": description
        }
        results["overall"]["total_time"] += duration
    
    # 2. Integration тесты
    print("\n📋 ЭТАП 2: Integration тесты")
    
    success, duration = run_command(
        "python3 -m pytest tests/test_integration.py -v --tb=short",
        "Integration тесты полного flow"
    )
    results["integration_tests"]["full_flow"] = {
        "success": success,
        "duration": duration,
        "description": "Integration тесты полного flow"
    }
    results["overall"]["total_time"] += duration
    
    # 3. Load тесты
    print("\n📋 ЭТАП 3: Load тесты")
    
    success, duration = run_command(
        "python3 -m pytest tests/test_load.py -v --tb=short",
        "Load тесты производительности"
    )
    results["load_tests"]["performance"] = {
        "success": success,
        "duration": duration,
        "description": "Load тесты производительности"
    }
    results["overall"]["total_time"] += duration
    
    # 4. Security тесты
    print("\n📋 ЭТАП 4: Security тесты")
    
    success, duration = run_command(
        "python3 -m pytest tests/test_security.py -v --tb=short",
        "Security тесты безопасности"
    )
    results["security_tests"]["security"] = {
        "success": success,
        "duration": duration,
        "description": "Security тесты безопасности"
    }
    results["overall"]["total_time"] += duration
    
    # 5. Интеграционный тест системы
    print("\n📋 ЭТАП 5: Интеграционный тест системы")
    
    success, duration = run_command(
        "python3 integration_test.py",
        "Интеграционный тест системы"
    )
    results["integration_tests"]["system"] = {
        "success": success,
        "duration": duration,
        "description": "Интеграционный тест системы"
    }
    results["overall"]["total_time"] += duration
    
    # Подсчет результатов
    all_tests = []
    for category in ["unit_tests", "integration_tests", "load_tests", "security_tests"]:
        for test_name, test_result in results[category].items():
            all_tests.append(test_result)
    
    results["overall"]["total_tests"] = len(all_tests)
    results["overall"]["passed_tests"] = sum(1 for test in all_tests if test["success"])
    results["overall"]["failed_tests"] = sum(1 for test in all_tests if not test["success"])
    
    # Вывод итогового отчета
    print("\n" + "="*60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
    print("="*60)
    
    print(f"Общее время тестирования: {results['overall']['total_time']:.2f} секунд")
    print(f"Всего тестов: {results['overall']['total_tests']}")
    print(f"Пройдено: {results['overall']['passed_tests']}")
    print(f"Провалено: {results['overall']['failed_tests']}")
    
    success_rate = (results['overall']['passed_tests'] / results['overall']['total_tests'] * 100) if results['overall']['total_tests'] > 0 else 0
    print(f"Процент успешности: {success_rate:.1f}%")
    
    # Детальный отчет по категориям
    print("\n📋 Детальный отчет:")
    
    for category, tests in results.items():
        if category == "overall":
            continue
            
        print(f"\n{category.upper()}:")
        for test_name, test_result in tests.items():
            status = "✅ ПРОЙДЕН" if test_result["success"] else "❌ ПРОВАЛЕН"
            print(f"  {test_result['description']}: {status} ({test_result['duration']:.2f}s)")
    
    # Сохранение отчета
    report_file = "test_results.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Отчет сохранен в: {report_file}")
    
    # Создание markdown отчета
    create_markdown_report(results)
    
    # Итоговый статус
    if results['overall']['failed_tests'] == 0:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        return 0
    else:
        print(f"\n⚠️ ПРОВАЛЕНО ТЕСТОВ: {results['overall']['failed_tests']}")
        return 1

def create_markdown_report(results):
    """Создание markdown отчета"""
    report_content = f"""# Отчет о тестировании системы

**Дата:** {time.strftime('%Y-%m-%d %H:%M:%S')}  
**Общее время:** {results['overall']['total_time']:.2f} секунд

## Общая статистика

- **Всего тестов:** {results['overall']['total_tests']}
- **Пройдено:** {results['overall']['passed_tests']}
- **Провалено:** {results['overall']['failed_tests']}
- **Процент успешности:** {(results['overall']['passed_tests'] / results['overall']['total_tests'] * 100) if results['overall']['total_tests'] > 0 else 0:.1f}%

## Результаты по категориям

### Unit тесты
"""
    
    for test_name, test_result in results['unit_tests'].items():
        status = "✅ ПРОЙДЕН" if test_result["success"] else "❌ ПРОВАЛЕН"
        report_content += f"- **{test_result['description']}:** {status} ({test_result['duration']:.2f}s)\n"
    
    report_content += "\n### Integration тесты\n"
    for test_name, test_result in results['integration_tests'].items():
        status = "✅ ПРОЙДЕН" if test_result["success"] else "❌ ПРОВАЛЕН"
        report_content += f"- **{test_result['description']}:** {status} ({test_result['duration']:.2f}s)\n"
    
    report_content += "\n### Load тесты\n"
    for test_name, test_result in results['load_tests'].items():
        status = "✅ ПРОЙДЕН" if test_result["success"] else "❌ ПРОВАЛЕН"
        report_content += f"- **{test_result['description']}:** {status} ({test_result['duration']:.2f}s)\n"
    
    report_content += "\n### Security тесты\n"
    for test_name, test_result in results['security_tests'].items():
        status = "✅ ПРОЙДЕН" if test_result["success"] else "❌ ПРОВАЛЕН"
        report_content += f"- **{test_result['description']}:** {status} ({test_result['duration']:.2f}s)\n"
    
    report_content += f"""

## Заключение

"""
    
    if results['overall']['failed_tests'] == 0:
        report_content += "🎉 **ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!**\n\nСистема готова к продакшену."
    else:
        report_content += f"⚠️ **ПРОВАЛЕНО ТЕСТОВ: {results['overall']['failed_tests']}**\n\nТребуется доработка перед продакшеном."
    
    # Сохранение markdown отчета
    with open("TEST_REPORT.md", 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print("📄 Markdown отчет сохранен в: TEST_REPORT.md")

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

