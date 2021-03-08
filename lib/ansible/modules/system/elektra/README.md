# ansible-libelektra

This is an Ansible module for [Elektra](https://github.com/ElektraInitiative/libelektra).

## Installation

The easiest way is to [install a current version of Ansible](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html) and then use this [alternative repository](https://github.com/ElektraInitiative/ansible-libelektra) instead.

If this causes some problems, just cloning this whole repository and then follow [the instructions to run Ansible from source](https://docs.ansible.com/ansible/2.9/installation_guide/intro_installation.html#running-ansible-from-source-devel).

> **Note**: When following the instructions, use
> ```sh
> git clone https://github.com/ElektraInitiative/ansible.git
> ```
> instead of
> ```sh
> git clone https://github.com/ansible/ansible.git
> ```
>

## Example Playbooks

The module lets you set values in the KDB.
This process is idempotent, i.e. only if the stored values differ from the ones in the playbook, will the KDB be modified.
The change detection happens on a per-task basis.
If a single key with in a task needs an update, the all the keys in this task will be updated.

```yml
- name: elektra module example
  hosts: localhost
  connection: local
  tasks:
    - name: set example values
      elektra:
        # Despite the name, this does not have to be a real mountpoint in the KDB.
        # If no plugin is specified, the value is only used as the base key for the keys object.
        mountpoint: /test/example
        # The keys object contains the data that should be present below the mountpoint.
        keys:
          fruit:
            cherry:
              value: cola
            apple:
              value: pie
            berries:
                raspberry:
                  value: pi
                blueberry:
                  value: muffin
          vegtables:
            tomato:
              value: ketchup
            potato:
              value: fries

```

You can also specify metadata (if the underlying storage format supports it).
In most cases, you should use a specification for metadata instead.

```yml
- name: elektra module example
  hosts: localhost
  connection: local
  tasks:
    - name: set example fruits
      elektra:
        mountpoint: /test/example/fruit
        keys:
          cherry:
            value: cola
            meta:
              # This adds the type metakey with value string to the key /test/example/fruit/cherry
              type: string
          apple:
            value: pie
          berries:
              raspberry:
                value: pi
              blueberry:
                value: muffin
    - name: set example vegtables
      elektra:
        mountpoint: /test/example/vegtables
        keys:
          tomato:
              value: ketchup
          potato:
              value: fries

```