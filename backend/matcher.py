"""
Модуль подбора наиболее совместимых участников команды для хакатонов.

Алгоритм учитывает:
1. Общие навыки студентов — насколько хорошо они смогут работать с похожими
   технологиями и инструментами.
2. Дополняющие навыки — насколько навыки одного участника расширяют набор
   навыков другого.
3. Синергию ролей — насколько хорошо роли участников сочетаются друг с другом.

Модуль использует только стандартную библиотеку Python 3.11+.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any, TypedDict


class CompatibilityResult(TypedDict):
    """Структура результата расчёта совместимости двух студентов."""

    candidate_id: int | None
    candidate_name: str
    candidate_role: str
    compatibility_percent: float
    common_skills: list[str]
    complementary_skills: list[str]


# Коэффициенты алгоритма.
# Навыки составляют 75% итоговой оценки, синергия ролей — 25%.
SKILLS_WEIGHT = 0.75
ROLES_WEIGHT = 0.25

# Внутри оценки навыков:
# 40% — общие навыки, 60% — разнообразие и дополнение навыков.
SHARED_SKILLS_WEIGHT = 0.40
COMPLEMENTARY_SKILLS_WEIGHT = 0.60

# Оценки синергии ролей находятся в диапазоне от 0 до 100.
# Для отсутствующих или неизвестных ролей используются нейтральные значения.
SAME_ROLE_SCORE = 35.0
UNKNOWN_ROLE_SCORE = 60.0
UNSPECIFIED_ROLE_SCORE = 50.0
DEFAULT_DIFFERENT_ROLE_SCORE = 65.0

# Сочетания ролей, которые особенно полезны при разработке проекта.
ROLE_SYNERGY: dict[frozenset[str], float] = {
    frozenset(("backend", "frontend")): 100.0,
    frozenset(("backend", "design")): 95.0,
    frozenset(("frontend", "design")): 90.0,
    frozenset(("backend", "data")): 85.0,
    frozenset(("backend", "devops")): 85.0,
    frozenset(("frontend", "data")): 75.0,
    frozenset(("backend", "qa")): 80.0,
    frozenset(("frontend", "qa")): 80.0,
}


def _get_text(value: Any) -> str:
    """
    Безопасно получает строковое значение.

    Нестроковые значения и отсутствующие поля заменяются пустой строкой.
    """
    return value.strip() if isinstance(value, str) else ""


def _get_profile_id(profile: Mapping[str, Any]) -> int | None:
    """
    Возвращает ID студента, если он корректный.

    Отсутствующий ID или значение неподходящего типа преобразуется в None.
    """
    value = profile.get("id")

    if isinstance(value, int) and not isinstance(value, bool):
        return value

    return None


def _normalize_skills(value: Any) -> dict[str, str]:
    """
    Нормализует список навыков.

    Удаляет лишние пробелы, игнорирует пустые и некорректные значения,
    сравнивает навыки без учёта регистра и удаляет дубликаты.

    Возвращает словарь:
        нормализованное_название: отображаемое_название
    """
    if not isinstance(value, (list, tuple, set)):
        return {}

    normalized: dict[str, str] = {}

    for skill in value:
        if not isinstance(skill, str):
            continue

        display_name = skill.strip()
        normalized_name = display_name.casefold()

        if normalized_name:
            normalized.setdefault(normalized_name, display_name)

    return normalized


def _normalize_role(role: str) -> str:
    """Приводит название роли к единому формату для сравнения."""
    return re.sub(r"\s+", " ", role.casefold()).strip()


def _get_role_family(role: str) -> str | None:
    """
    Определяет категорию роли.

    Поддерживаются английские и распространённые русские названия.
    Неизвестные роли возвращают None.
    """
    normalized = _normalize_role(role)
    compact = re.sub(r"[^a-zа-яё0-9]+", "", normalized)

    if any(
        keyword in compact
        for keyword in ("backend", "server", "бэкенд", "бэкэнд", "сервер")
    ):
        return "backend"

    if any(
        keyword in compact
        for keyword in ("frontend", "клиентскаяразработка", "фронтенд")
    ):
        return "frontend"

    if (
        "uiux" in compact
        or "designer" in compact
        or "design" in compact
        or "дизайн" in compact
        or "дизайнер" in compact
        or re.search(r"(?<![a-z0-9])(ui|ux)(?![a-z0-9])", normalized)
    ):
        return "design"

    if any(
        keyword in compact
        for keyword in ("data", "аналитик", "аналитика", "данных")
    ):
        return "data"

    if any(
        keyword in compact
        for keyword in ("devops", "sre", "инфраструктура")
    ):
        return "devops"

    if any(
        keyword in compact
        for keyword in ("qa", "тестировщик", "тестирование")
    ):
        return "qa"

    return None


def _calculate_role_score(role_a: str, role_b: str) -> float:
    """
    Рассчитывает оценку синергии двух ролей от 0 до 100.

    Одинаковые роли получают небольшой бонус, так как участники могут
    дублировать функции друг друга. Разные дополняющие роли получают
    повышенную оценку.
    """
    normalized_a = _normalize_role(role_a)
    normalized_b = _normalize_role(role_b)

    if not normalized_a or not normalized_b:
        return UNSPECIFIED_ROLE_SCORE

    if normalized_a == normalized_b:
        return SAME_ROLE_SCORE

    family_a = _get_role_family(role_a)
    family_b = _get_role_family(role_b)

    if family_a is None or family_b is None:
        return UNKNOWN_ROLE_SCORE

    if family_a == family_b:
        return SAME_ROLE_SCORE

    role_pair = frozenset((family_a, family_b))

    return ROLE_SYNERGY.get(role_pair, DEFAULT_DIFFERENT_ROLE_SCORE)


def calculate_compatibility(
    user_a: dict[str, Any],
    user_b: dict[str, Any],
) -> CompatibilityResult:
    """
    Рассчитывает совместимость двух студентов в процентах.

    Args:
        user_a: Исходный пользователь.
            Ожидаемые поля: id, name, role, skills.
        user_b: Кандидат для команды.
            Ожидаемые поля: id, name, role, skills.

    Returns:
        Словарь с информацией о кандидате:
            candidate_id: ID кандидата.
            candidate_name: Имя кандидата.
            candidate_role: Роль кандидата.
            compatibility_percent: Итоговая оценка от 0 до 100.
            common_skills: Общие навыки обоих пользователей.
            complementary_skills: Навыки кандидата, которых нет у user_a.

    Примечания:
        - Сравнение навыков не зависит от регистра и лишних пробелов.
        - Дубликаты навыков не влияют на результат.
        - Если навыки отсутствуют хотя бы у одного пользователя,
          оценка навыков считается нейтральной — 50 баллов.
        - Отсутствующие поля не вызывают исключений.
    """
    skills_a = _normalize_skills(user_a.get("skills"))
    skills_b = _normalize_skills(user_b.get("skills"))

    skills_a_set = set(skills_a)
    skills_b_set = set(skills_b)

    common_keys = skills_a_set & skills_b_set
    union_keys = skills_a_set | skills_b_set

    # Сохраняем исходный порядок навыков пользователя и кандидата.
    common_skills = [
        skills_a[key]
        for key in skills_a
        if key in common_keys
    ]

    complementary_skills = [
        skills_b[key]
        for key in skills_b
        if key not in skills_a_set
    ]

    # Расчёт оценки навыков.
    if not skills_a_set or not skills_b_set:
        skills_score = 50.0
    else:
        # Доля общих навыков относительно большего списка.
        shared_ratio = len(common_keys) / max(
            len(skills_a_set),
            len(skills_b_set),
        )

        # Доля навыков, которые расширяют общий набор команды.
        complementary_ratio = (
            len(union_keys) - len(common_keys)
        ) / len(union_keys)

        skills_score = 100.0 * (
            SHARED_SKILLS_WEIGHT * shared_ratio
            + COMPLEMENTARY_SKILLS_WEIGHT * complementary_ratio
        )

    # Расчёт синергии ролей.
    role_a = _get_text(user_a.get("role"))
    role_b = _get_text(user_b.get("role"))

    roles_score = _calculate_role_score(role_a, role_b)

    # Итоговая взвешенная оценка.
    compatibility = (
        skills_score * SKILLS_WEIGHT
        + roles_score * ROLES_WEIGHT
    )

    # Защита от возможного выхода за допустимый диапазон.
    compatibility = max(0.0, min(100.0, compatibility))

    return {
        "candidate_id": _get_profile_id(user_b),
        "candidate_name": _get_text(user_b.get("name")),
        "candidate_role": role_b,
        "compatibility_percent": round(compatibility, 1),
        "common_skills": common_skills,
        "complementary_skills": complementary_skills,
    }


def find_best_teammates(
    target_user: dict[str, Any],
    candidates: list[dict[str, Any]],
    top_n: int = 5,
) -> list[CompatibilityResult]:
    """
    Находит наиболее совместимых кандидатов для формирования команды.

    Функция:
        1. Исключает исходного пользователя из списка кандидатов.
        2. Рассчитывает совместимость с каждым оставшимся кандидатом.
        3. Сортирует результаты по убыванию процента совместимости.
        4. Возвращает не более top_n лучших кандидатов.

    Args:
        target_user: Пользователь, для которого подбирается команда.
        candidates: Список профилей потенциальных участников.
        top_n: Максимальное количество возвращаемых кандидатов.

    Returns:
        Отсортированный список результатов совместимости.

    Примечания:
        - Если top_n меньше или равен нулю, возвращается пустой список.
        - Пользователь исключается по совпадению ID или объекта.
        - При одинаковых оценках сохраняется исходный порядок кандидатов.
    """
    if not isinstance(top_n, int) or isinstance(top_n, bool) or top_n <= 0:
        return []

    target_id = _get_profile_id(target_user)
    results: list[CompatibilityResult] = []

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue

        candidate_id = _get_profile_id(candidate)

        # Не предлагаем пользователя самому себе.
        if candidate is target_user:
            continue

        if target_id is not None and candidate_id == target_id:
            continue

        result = calculate_compatibility(target_user, candidate)
        results.append(result)

    # Сортировка по убыванию совместимости.
    # Python сохраняет исходный порядок элементов с одинаковым ключом.
    results.sort(
        key=lambda item: item["compatibility_percent"],
        reverse=True,
    )

    return results[:top_n]


if __name__ == "__main__":
    """
    Демонстрация работы алгоритма на тестовых профилях студентов.
    Запуск: python backend/matcher.py
    """

    target_student: dict[str, Any] = {
        "id": 1,
        "name": "Александр Иванов",
        "role": "Backend Developer",
        "skills": [
            "Python",
            "FastAPI",
            "SQLite",
            "REST API",
            "Git",
        ],
    }

    students: list[dict[str, Any]] = [
        {
            "id": 2,
            "name": "Мария Смирнова",
            "role": "Frontend Developer",
            "skills": [
                "JavaScript",
                "TypeScript",
                "React",
                "HTML",
                "CSS",
                "Git",
            ],
        },
        {
            "id": 3,
            "name": "Дмитрий Козлов",
            "role": "UI/UX Designer",
            "skills": [
                "Figma",
                "UI Design",
                "UX Research",
                "Prototyping",
                "HTML",
            ],
        },
        {
            "id": 4,
            "name": "Екатерина Волкова",
            "role": "Backend Developer",
            "skills": [
                "Python",
                "Django",
                "PostgreSQL",
                "Docker",
                "Git",
            ],
        },
        {
            "id": 5,
            "name": "Илья Петров",
            "role": "Data Analyst",
            "skills": [
                "Python",
                "Pandas",
                "SQL",
                "Data Visualization",
                "Statistics",
            ],
        },
        {
            "id": 6,
            "name": "Анна Морозова",
            "role": "QA Engineer",
            "skills": [
                "Postman",
                "Pytest",
                "API Testing",
                "Python",
                "Git",
            ],
        },
        {
            "id": 7,
            "name": "Сергей Новиков",
            "role": "DevOps Engineer",
            "skills": [
                "Docker",
                "Linux",
                "CI/CD",
                "Git",
                "Nginx",
            ],
        },
    ]

    print()
    print("=" * 72)
    print("            IRIT TEAMFINDER — ПОДБОР УЧАСТНИКОВ КОМАНДЫ")
    print("=" * 72)
    print(
        f"Исходный пользователь: {target_student['name']}"
        f" ({target_student['role']})"
    )
    print(f"Навыки: {', '.join(target_student['skills'])}")
    print("-" * 72)

    best_teammates = find_best_teammates(
        target_user=target_student,
        candidates=students,
        top_n=5,
    )

    if not best_teammates:
        print("Подходящие кандидаты не найдены.")
    else:
        print("ТОП КАНДИДАТОВ:")
        print()

        for position, candidate in enumerate(best_teammates, start=1):
            print(
                f"{position}. {candidate['candidate_name']}"
                f" — {candidate['compatibility_percent']:.1f}%"
            )
            print(f"   Роль: {candidate['candidate_role'] or 'не указана'}")

            common = candidate["common_skills"]
            complementary = candidate["complementary_skills"]

            print(
                f"   Общие навыки: {', '.join(common) if common else 'нет'}"
            )
            print(
                "   Дополняющие навыки: "
                f"{', '.join(complementary) if complementary else 'нет'}"
            )
            print()

    print("=" * 72)
    print("Демонстрация завершена.")