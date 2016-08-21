# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2016 Lionel Ott
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import importlib
import os

from gremlin.common import UiInputType
from gremlin.util import SingletonDecorator


@SingletonDecorator
class PluginManager(object):

    """Responsible for handling all plugins."""

    def __init__(self):
        """Creates a new instance loading plugins from the given location.
        """
        self._repositories = {}

    def register(self, category, folder):
        self._repositories[category] = PluginList(folder)

    def __getitem__(self, key):
        return self._repositories[key]


class PluginList(object):

    def __init__(self, folder):
        self._plugin_folder = folder
        self._repository = {}

        self._discover_plugins()

    @property
    def repository(self):
        return self._repository

    def _discover_plugins(self):
        print("Searching for plugins in: {}".format(self._plugin_folder))

        for root, dirs, files in os.walk(self._plugin_folder):
            for fname in files:
                try:
                    name, ext = os.path.splitext(fname)
                    # Disregard any files that aren't python code
                    if ext != ".py":
                        continue
                    # Attempt to load the file and if it looks like a proper
                    # action_plugins store it in the registry
                    # TODO: this module name generation needs to be more robust
                    plugin = importlib.import_module("{}.{}".format(
                        self._plugin_folder,
                        name
                    ))
                    if "version" in plugin.__dict__:
                        self._repository[plugin.name] = plugin.create
                        print("Loaded: {}".format(plugin.name))
                    else:
                        del plugin
                except Exception as e:
                    # Log an error and ignore the action_plugins if
                    # anything is wrong with it
                    print("Loading action_plugins '{}' failed due to: {}".format(fname, e))


@SingletonDecorator
class ActionPlugins(object):

    """Handles discovery and derivation of action plugins."""

    def __init__(self):
        self._plugins = {}
        self._type_action_map = {}
        self._action_name_to_type = {}
        self._action_type_to_name = {}

        self._discover_plugins()

        self._create_type_action_map()
        self._create_action_name_map()

    @property
    def repository(self):
        return self._plugins

    @property
    def type_action_map(self):
        return self._type_action_map

    @property
    def action_name_map(self):
        return self._action_name_to_type

    def _create_type_action_map(self):
        """Creates a lookup table of input types and their available actions."""
        self._type_action_map = {
            UiInputType.JoystickAxis: [],
            UiInputType.JoystickButton: [],
            UiInputType.JoystickHat: [],
            UiInputType.Keyboard: []
        }

        for entry in self._plugins.values():
            for input_type in entry.input_types:
                self._type_action_map[input_type].append(entry)

    def _create_action_name_map(self):
        for entry in self._plugins.values():
            self.action_name_map[entry.tag] = entry

    def _discover_plugins(self):
        for root, dirs, files in os.walk("action_plugins"):
            for fname in [v for v in files if v == "__init__.py"]:
                try:
                    folder, module = os.path.split(root)
                    if folder != "action_plugins":
                        continue

                    # Attempt to load the file and if it looks like a proper
                    # action_plugins store it in the registry
                    plugin = importlib.import_module("action_plugins.{}".format(module))
                    if "version" in plugin.__dict__:
                        self._plugins[plugin.name] = plugin.create
                        print("Loaded: {}".format(plugin.name))
                    else:
                        del plugin
                except Exception as e:
                    # Log an error and ignore the action_plugins if
                    # anything is wrong with it
                    print("Loading action_plugins '{}' failed due to: {}".format(fname, e))