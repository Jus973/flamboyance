"""Shared types — imported by the rest of the project. Do NOT refactor."""

from dataclasses import dataclass


@dataclass
class User:
    id: int
    name: str
    email: str


@dataclass
class Order:
    id: int
    user_id: int
    total_cents: int
