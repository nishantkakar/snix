#!/usr/bin/env python
import json
import os
import singleton
import snixCore
from jsonschema import Draft4Validator
from item import Item
from repo import Repo
from script import Script
import ConfigParser


class snixContext:
    """A parser that will build an in-memory representation of a snix manifest."""
    __metaclass__ = singleton.Singleton

    @staticmethod
    def construct_from(manifest_file):
        sc = snixContext(manifest_file)
        sc._construct()
        return sc

    def __init__(self, _file):
        if not os.path.isfile(_file):
            snixCore.abort("%s is not a valid file path!" % _file)
        self._file = _file
        self._manifest_items = []
        self._manifest_repos = []
        self._manifest_custom_scripts = []

    # TODO navigate all includes.
    # make sure it doesn't have cycles.
    def _construct(self):
        snixConf = os.path.join(os.environ["HOME"],".snix","snix.conf")
        with open(self._file, 'r') as candidate:
            _data = json.load(candidate)
            parser = ConfigParser.ConfigParser()
            parser.read(snixConf)
            snixHome = parser.get("config", "snix.home")
        if 'includes' in _data:
            self._collect_includes(_data,snixHome)
        if 'items' in _data:
            map(lambda i:self._manifest_items.append(i), _data['items'])
        if 'repos' in _data:
            map(lambda i:self._manifest_repos.append(i), _data['repos'])
        if 'customScripts' in _data:
            map(lambda i:self._manifest_custom_scripts.append(i), _data['customScripts'])


    def _collect_includes(self, _data,_snixHome):
        
        for include in _data['includes']:
            _repo = include['upstreamRepo']
            _dir = _repo.split('/')[-1].split('.')[0]
            if not os.path.exists(_dir):
                includeContext={}
                includeContext['snix_root']= _snixHome
                includeContext['repo_location']= _repo
                Repo(includeContext).clone()
            grp_dir = include['pathRelativeToGroupManifestDir']
            _include_file = os.path.join(_snixHome, _dir, grp_dir,grp_dir+'.snix')
        self._collect_from_file(_include_file,_snixHome)

    def _collect_from_file(self, _include_file, _snixHome):
        with open(_include_file, 'r') as candidate:
            _data = json.load(candidate)
        if 'include' in _data:
            self._collect_includes(_data, _snixHome)
        if 'items' in _data:
            map(lambda i:self._manifest_items.append(i), _data['items'])
        if 'repos' in _data:
            map(lambda i:self._manifest_repos.append(i), _data['repos'])
        if 'customScripts' in _data:
            map(lambda i:self._manifest_custom_scripts.append(i), _data['customScripts'])

    def __str__(self):
        items = [''.join("{0} via {1}".format(item['names'], item['via'])) for item in iter(self._manifest_items)]
        return '\n'.join(["\nItems to install: {0}".format(items),
                          "Repositories to clone:{0}".format(json.dumps(self._manifest_repos, indent=2)),
                          "Custom scripts to execute:{0}".format(json.dumps(self._manifest_custom_scripts, indent=2))])

    # TODO: make this take in a filter.
    def get_items(self):
        def _build_item(name, via):
            item_context = {'name': name, 'via': via}
            return Item(item_context)

        all_items = []
        for item in self._manifest_items:
            for name in item['names']:
                all_items.append(_build_item(name, item['via']))
        return all_items

    def get_repos(self):
        all_repos=[]
        for repo in self._manifest_repos:
            repo_context = {'repo_location': repo}
            all_repos.append(Repo(repo_context))
        return all_repos

    def get_custom_scripts(self):
        all_scripts=[]
        for script in self._manifest_custom_scripts:
            custom_script_context = {'script_location': script}
            all_scripts.append(Script(custom_script_context))
        return all_scripts


