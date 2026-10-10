"""Plugin system — mirrors the Univer plugin architecture."""

from __future__ import annotations

from typing import Any, Protocol


class Plugin(Protocol):
    id: str
    name: str

    def install(self, context: PluginContext) -> None: ...
    def uninstall(self, context: PluginContext) -> None: ...


class PluginContext:
    """Context passed to plugins during install/uninstall."""

    def __init__(self, container: Any) -> None:
        self._container = container

    @property
    def services(self) -> Any:
        from univer.core.di import ServiceProvider

        return ServiceProvider(self._container)


class PluginRegistry:
    """Registry that holds all installed plugins and coordinates lifecycle."""

    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}

    def register(self, plugin: Plugin) -> None:
        if plugin.id in self._plugins:
            raise ValueError(f"Plugin {plugin.id!r} already registered")
        self._plugins[plugin.id] = plugin

    def install_all(self, context: PluginContext) -> None:
        for p in self._plugins.values():
            p.install(context)

    def uninstall_all(self, context: PluginContext) -> None:
        for p in reversed(list(self._plugins.values())):
            p.uninstall(context)

    def get(self, plugin_id: str) -> Plugin:
        return self._plugins[plugin_id]

    @property
    def plugin_ids(self) -> list[str]:
        return list(self._plugins.keys())
