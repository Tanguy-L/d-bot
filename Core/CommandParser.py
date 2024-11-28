import re
import inspect

import Core.Commands

class VCMCommandParser():
    __registered_cmd = []

    def __init__(self, command_prefix='!') -> None:
        self.command_prefix = command_prefix

    def command(self, name=None):
        def decorator(f):
            cmd_name = name if name != None else f.__name__
            cmd_args_count = len(inspect.getfullargspec(f).args)
            self.__registered_cmd.append(Core.Commands.VCMCommand(cmd_name, cmd_args_count, f))
            return f
        return decorator

    def parse(self, input) -> Core.Commands.VCMCommand:
        if self.__is_a_cmd(input) is not True:
            return

        name = re.findall(rf'{self.command_prefix}(\S+)', input)[0]
        args = re.findall(r'"(.+?)"|(\S+){1}', input.strip(self.command_prefix + name))

        for index, arg in enumerate(args):
            args[index] = arg[0] if arg[0] != '' else arg[1]

        if self.__check_cmd_validity(name, args) is True:
            cmd = self.__get_cmd(name)
            cmd.args = args
            return cmd
        return

    def __is_a_cmd(self, input):
        return input[:1] == self.command_prefix

    def __check_cmd_validity(self, cmd_name, cmd_args) -> bool:
        for cmd in self.__registered_cmd:
            if cmd.check_requirement(cmd_name, cmd_args):
                return True
        return False
    
    def __get_cmd(self, cmd_name) -> Core.Commands.VCMCommand:
        for cmd in self.__registered_cmd:
            if cmd.name == cmd_name:
                return cmd
        return None