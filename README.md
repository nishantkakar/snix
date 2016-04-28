# snix
Snix is intended to be a simple tool to setup your unix environment.

***S***etup u***nix***

Got a new laptop ? Just joined the company or a team ?
**snix can help!**

##Why
Fundamentally, as computer science and software professionals, we strive find a better, faster solution to an existing problem.

i.e. optimize

An automated dev environment setup is an optimized way of a tedious manual process.

It's consistent, fast, and repeatable.

New hires can get started quickly.


##How
Built in python

Based on a simple DSL defined in JSON.

Bootstrap.

Define your manifest. You can also include your colleague/friend's manifest or a group manifest.

Run

##Future Enhancements:
- Better version management for installed s/w
- Setting up access keys with github.
- Build in some intelligence:
    - Take snapshot before starting and offer to reconcile with snix
    - Analyze user and team manifests to extract commonalities.
- Security. stop folks from doing the bad things like rm -rf.

### To get started
```bash
python <(curl -s https://raw.githubusercontent.com/yaise/snix/master/bootstrap.py)
```
