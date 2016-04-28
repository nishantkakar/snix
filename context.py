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
        self._manifest_config = {}
        self._manifest_items = []
        self._manifest_repos = []
        self._manifest_custom_scripts = []

    # TODO navigate all includes.
    # make sure it doesn' have cycles.
    def _construct(self):
        with open(self._file, 'r') as candidate:
            _data = json.load(candidate)
        with open(os.path.join(_data['config']['snix_root'],'_snix','schema.json'), 'r') as schema:
            _schema = json.load(schema)
            Draft4Validator(_schema).validate(_data)
        self._manifest_config = _data['config']

        if 'includes' in _data:
            self._collect_includes(_data)
        if 'items' in _data:
            map(lambda i:self._manifest_items.append(i), _data['items'])
        if 'repos' in _data:
            map(lambda i:self._manifest_repos.append(i), _data['repos'])
        if 'customScripts' in _data:
            map(lambda i:self._manifest_custom_scripts.append(i), _data['customScripts'])


    def _collect_includes(self, _data):
        _root = _data['config']['snix_root']
        for include in _data['includes']:
            _repo = include['upstreamRepo']
            _dir = _repo.split('/')[-1].split('.')[0]
            if not os.path.exists(_dir):
                includeContext={}
                includeContext['snix_root']= _root
                includeContext['repo_location']= _repo
                Repo(includeContext).clone()
            grp_dir = include['pathRelativeToGroupManifestDir']
            _include_file = os.path.join(_root, _dir, grp_dir,grp_dir+'.snix')
        self._collect_from_file(_include_file)

    def _collect_from_file(self, _include_file):
        with open(_include_file, 'r') as candidate:
            _data = json.load(candidate)
        with open(os.path.join(self._manifest_config['snix_root'],'_snix','schema.json'), 'r') as schema:
            _schema = json.load(schema)
            Draft4Validator(_schema).validate(_data)
        if 'include' in _data:
            self._collect_includes(_data)
        if 'items' in _data:
            map(lambda i:self._manifest_items.append(i), _data['items'])
        if 'repos' in _data:
            map(lambda i:self._manifest_repos.append(i), _data['repos'])
        if 'customScripts' in _data:
            map(lambda i:self._manifest_custom_scripts.append(i), _data['customScripts'])
        # self._manifest_items.udpate(_data['items'])
        # self._manifest_repos.udpate(_data['repos'])
        # self._manifest_custom_scripts.update(_data['customScripts'])

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


