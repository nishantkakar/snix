#!/usr/bin/env python
import json
import os
import singleton
import snixCore
from jsonschema import Draft4Validator
from item import Item
from repo import Repo
from script import Script


class Context:
    """A parser that will build an in-memory representation of a snix manifest."""
    __metaclass__ = singleton.Singleton

    @staticmethod
    def construct_from(manifest_file):
        context = Context(manifest_file)
        context._construct()
        return context

    def __init__(self, _file):
        if not os.path.isfile(_file):
            snixCore.abort("%s is not a valid file path!" % _file)
        self._file = _file

    # TODO navigate all includes.
    # make sure it doesn' have cycles.
    def _construct(self):
        with open(self._file, 'r') as candidate:
            _data = json.load(candidate)
            # if 'include' in _data:
            #     _collect_includes
            self._manifest_config = _data['config']
            self._manifest_items = _data['items']
            self._manifest_repos = _data['repos']
            self._manifest_custom_scripts = _data['customScripts']
            with open(os.path.join(self._manifest_config['snix_root'],'_snix','schema.json'), 'r') as schema:
                _schema = json.load(schema)
                Draft4Validator(_schema).validate(_data)

    def __str__(self):
        items = [''.join("{0} via {1}".format(item['names'], item['via'])) for item in iter(self._manifest_items)]
        return '\n'.join(["\nItems to install: {0}".format(items),
                          "Repositories to clone:{0}".format(json.dumps(self._manifest_repos, indent=2)),
                          "Custom scripts to execute:{0}".format(json.dumps(self._manifest_custom_scripts, indent=2)),
                          "Configuration:{0}".format(json.dumps(self._manifest_config, indent=2))])

    # TODO: make this take in a filter.
    def get_items(self):
        def _build_item(name, via, config):
            item_context = {'name': name, 'via': via}
            item_context.update(config)
            return Item(item_context)

        all_items = []
        for item in self._manifest_items:
            # if 'name' in item:
            #     all_items.append(_build_item(item['name'], item['via'], self._manifest_config))
            # elif 'names' in item:
            for name in item['names']:
                all_items.append(_build_item(name, item['via'], self._manifest_config))
        return all_items

    def get_repos(self):
        all_repos=[]
        for repo in self._manifest_repos:
            repo_context = {'repo_location': repo}
            repo_context.update(self._manifest_config)
            all_repos.append(Repo(repo_context))
        return all_repos

    def get_custom_scripts(self):
        all_scripts=[]
        for script in self._manifest_custom_scripts:
            custom_script_context = {'script_location': script}
            custom_script_context.update(self._manifest_config)
            all_scripts.append(Script(custom_script_context))
        return all_scripts
