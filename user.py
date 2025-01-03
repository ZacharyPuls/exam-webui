from dataclasses import dataclass
from uuid import UUID

import model
from nicegui import app
from serializable import Serializable


@dataclass
class User(Serializable):
    id: UUID
    name: str
    email: str

    async def new(self) -> None:
        pass

    async def save(self) -> None:
        pass

    @staticmethod
    async def load(from_value: model.User) -> any:
        return User(id=from_value.id, name=from_value.name, email=from_value.email)

    @staticmethod
    async def get_active() -> any:
        name = app.storage.user["user"]["name"]
        email = app.storage.user["user"]["preferred_username"]
        return await model.User.get(name=name, email=email)
