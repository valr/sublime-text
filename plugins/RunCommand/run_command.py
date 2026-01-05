import html
import re
import subprocess
from dataclasses import dataclass, fields
from typing import List, Optional

import sublime
import sublime_plugin
from sublime_types import Event


@dataclass
class CommandArguments:
    command: str
    cwd: Optional[str] = None
    timeout: int = 30
    source: str = "selection"
    target: str = "selection"


class CommandInputHandler(sublime_plugin.TextInputHandler):
    """
    Handles the input of a command.
    """

    def placeholder(self) -> str:
        return "command"

    def next_input(self, args: dict) -> Optional[sublime_plugin.CommandInputHandler]:
        command = args["command"]
        arguments = self.extract_arguments_from_command(command)
        if arguments:
            return ArgumentInputHandler(command, arguments)

    @staticmethod
    def extract_arguments_from_command(command: str) -> List[str]:
        return re.findall(r"\$\{arg_.+?\}", command)


class ArgumentInputHandler(sublime_plugin.TextInputHandler):
    """
    Handles the input of an argument.
    """

    def __init__(self, command: str, arguments: List[str]):
        super().__init__()
        self.command = command
        self.argument = arguments[0]
        self.next_arguments = arguments[1:]

        # An argument has the following format: ${arg_xxx} or ${arg_xxx|yyy} where
        # xxx is the argument name and yyy is the argument default value (optional).

        try:
            self.argument_name = self.argument[6 : self.argument.rindex("|")]
        except ValueError:
            self.argument_name = self.argument[6:-1]

        try:
            self.argument_default_value = self.argument[self.argument.rindex("|") + 1 : -1]
        except ValueError:
            self.argument_default_value = ""

    def name(self) -> str:
        return self.argument

    def placeholder(self) -> str:
        return self.argument_name

    def initial_text(self) -> str:
        return self.argument_default_value

    def preview(self, text: str) -> sublime.Html:
        command = html.escape(self.command).replace(self.argument, "<b>" + (text if text else self.argument) + "</b>")
        return sublime.Html(
            "<b><i>argument</i></b>: " + self.argument_name + "<br><b><i>command preview</i></b>: " + command
        )

    def confirm(self, text: str, event: Optional[Event] = None):
        self.value = text

    def next_input(self, args: dict) -> Optional[sublime_plugin.CommandInputHandler]:
        if self.next_arguments:
            return ArgumentInputHandler(self.command.replace(self.argument, self.value), self.next_arguments)


class RunCommandCommand(sublime_plugin.TextCommand):
    def input(self, args: dict) -> Optional[sublime_plugin.CommandInputHandler]:
        command = args.get("command")
        if not command:
            return CommandInputHandler()

        arguments = CommandInputHandler.extract_arguments_from_command(command)
        if arguments:
            return ArgumentInputHandler(command, arguments)

    def run(self, edit: sublime.Edit, **kwargs):
        keys = {f.name for f in fields(CommandArguments)}
        items_in = {k: v for k, v in kwargs.items() if k in keys}
        items_out = {k: v for k, v in kwargs.items() if k not in keys}

        # if the command to execute has not been provided in .sublime-commands,
        # it has been provided via the command input handler
        cmd_args = CommandArguments(**items_in)

        # replace the arguments in format ${arg_xxx} or ${arg_xxx|yyy}
        # by the corresponding value provided via the argument input handler
        for arg, value in items_out.items():
            cmd_args.command = cmd_args.command.replace(arg, value)

        # current working directory where the command will be executed
        # the variables starting with "$" are the ones accepted by the extract_variables
        # function defined in https://www.sublimetext.com/docs/3/api_reference.html
        if cmd_args.cwd and len(cmd_args.cwd) > 0 and cmd_args.cwd[0] == "$":
            window = self.view.window()
            if window:
                cmd_args.cwd = window.extract_variables().get(cmd_args.cwd[1:])

        if cmd_args.source == "selection":
            regions = self.view.sel()
        elif cmd_args.source == "window":
            regions = [sublime.Region(0, self.view.size())]
        else:
            regions = [None]

        for region in regions:
            self.run_command(
                cmd_args.command,
                cmd_args.cwd,
                cmd_args.timeout,
                edit,
                region,
                cmd_args.target,
            )

    def run_command(
        self,
        command: str,
        cwd: Optional[str],
        timeout: float,
        edit: sublime.Edit,
        region: Optional[sublime.Region],
        target: str,
    ):
        try:
            process = subprocess.Popen(
                command,
                bufsize=-1,
                cwd=cwd,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            try:
                stdin = self.view.substr(region).encode("utf-8") if region is not None else b""
                stdout, stderr = process.communicate(stdin, timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
                sublime.error_message(f"The command '{command}' has timed out.")
                return
        except subprocess.SubprocessError as err:
            sublime.error_message(str(err))
            return

        if stderr:
            sublime.error_message(stderr.decode("utf-8"))
            return

        if target == "selection" and region is not None:
            if stdin != stdout:
                self.view.replace(edit, region, stdout.decode("utf-8"))
        elif target == "window":
            window = self.view.window()
            if window:
                view = window.new_file()
                view.set_name(command)
                view.set_scratch(True)
                view.run_command("append", {"characters": stdout.decode("utf-8")})
