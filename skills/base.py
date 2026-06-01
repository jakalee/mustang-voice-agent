"""스킬 기본 인터페이스"""
from typing import Any


SKILL_DEFINITION: dict = {}


def execute(params: dict) -> Any:
    raise NotImplementedError
