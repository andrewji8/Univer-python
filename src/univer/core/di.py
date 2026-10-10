"""Dependency injection container inspired by the Univer TypeScript DI system."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol


class Service(Protocol):
    def start(self) -> None: ...
    def destroy(self) -> None: ...


class DIContainer:
    """Simple service container. Each service is registered by type and resolved on demand."""

    def __init__(self) -> None:
        self._registry: dict[type[Any], Any] = {}
        self._factories: dict[type[Any], Callable[[], Any]] = {}

    def register(
        self, cls: type[Any], instance: Any | None = None, *, singleton: bool = True
    ) -> None:
        if instance is not None:
            self._registry[cls] = instance
        else:
            self._factories[cls] = lambda: self._resolve_dependencies(cls)
        if singleton and cls not in self._registry:
            self._registry[cls] = self._factories[cls]()

    def _resolve_dependencies(self, cls: type[Any]) -> Any:
        import inspect
        import typing

        try:
            hints = typing.get_type_hints(cls.__init__)
        except Exception:
            hints = {}
        sig = inspect.signature(cls.__init__)
        params = list(sig.parameters.items())[1:]  # skip self
        kwargs: dict[str, Any] = {}
        for name, param in params:
            ann = hints.get(name, param.annotation)
            if ann is inspect.Parameter.empty:
                continue
            if not self.has(ann):
                continue
            kwargs[name] = self.get(ann)
        return cls(**kwargs)

    def get(self, cls: type[Any]) -> Any:
        if cls not in self._registry:
            if cls in self._factories:
                self._registry[cls] = self._factories[cls]()
            else:
                raise KeyError(f"Service {cls.__name__} not registered")
        return self._registry[cls]

    def has(self, cls: type[Any]) -> bool:
        return cls in self._registry or cls in self._factories

    def destroy_all(self) -> None:
        for svc in list(self._registry.values()):
            if hasattr(svc, "destroy"):
                svc.destroy()
        self._registry.clear()
        self._factories.clear()


class ServiceProvider:
    """Fluent wrapper around DIContainer for plugin registration style."""

    def __init__(self, container: DIContainer) -> None:
        self._c = container

    def get(self, cls: type[Any]) -> Any:
        return self._c.get(cls)

    def provides(
        self, cls: type[Any], impl: type[Any] | None = None, *, singleton: bool = True
    ) -> None:
        if impl is None:
            impl = cls
        self._c.register(impl, singleton=singleton)
