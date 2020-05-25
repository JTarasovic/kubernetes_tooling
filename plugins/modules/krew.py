#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
from ansible.module_utils.basic import AnsibleModule
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: krew

short_description: This is my test module

version_added: "2.4"

description:
    - "This is my longer description explaining my test module"

options:
    name:
        description:
            - This is the message to send to the test module
        required: true
    new:
        description:
            - Control to demo if the result of this module is changed or not
        required: false

extends_documentation_fragment:
    - azure

author:
    - Your Name (@yourhandle)
'''

EXAMPLES = '''
# Pass in a message
- name: Test with a message
  my_test:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_test:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_test:
    name: fail me
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
    returned: always
message:
    description: The output message that the test module generates
    type: str
    returned: always
'''


def get_installed_packages(module, cmd):
    # make sure index is updated or krew will error
    module.run_command(cmd + " update", check_rc=True)

    # krew detects if stdout is a pipe and changes its output
    # to only be the list of plugins (but not the version)
    _, stdout, stderr = module.run_command(cmd + "  list", check_rc=True)
    return [s for s in stdout.split('\n') if s != '']


# not commutative
# for figuring out what plugins need to be installed
def set_difference(a, b):
    return list(set(a) - set(b))


# for figuring out what plugins should be removed
def set_intersection(a, b):
    return list(set(a) & set(b))


def do_action(module, cmd, action, plugins):
    install_cmd = cmd + action % " ".join(plugins)
    _, stdout, stderr = module.run_command(install_cmd, check_rc=True)


def run_module():
    module_args = dict(
        plugins=dict(type='list', elements='str',
                     aliases=['name'], required=True),
        state=dict(type='str', default='present',
                   choices=['absent', 'present'])
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    result = dict(
        changed=False,
        message=''
    )

    # verify krew is installed
    krew_cmd = module.get_bin_path("kubectl-krew", True)

    plugins = module.params['plugins']
    installed_plugins = get_installed_packages(module, krew_cmd)

    if module.params['state'] == 'absent':
        action = " uninstall %s"
        action_list = set_intersection(plugins, installed_plugins)

    else:
        action = " install %s"
        action_list = set_difference(plugins, installed_plugins)

    if module.check_mode:
        result['message'] = "would" + action % ", ".join(action_list)
        result['changed'] = len(action_list) > 0

        module.exit_json(**result)

    if len(action_list) == 0:
        result['message'] = "no action to take"
        module.exit_json(**result)

    result['changed'] = True
    do_action(module, krew_cmd, action, action_list)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
