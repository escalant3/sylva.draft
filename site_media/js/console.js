function SylvaConsole(widget, logWidget) {
    this.historyIndex = -1;
    this.historyLog = [];

    this.terminalWidget = widget;
    this.terminalLog = logWidget;
    this.terminalWidget.shell = this;
    this.terminalWidget.focus();

    this.shellCommands = {
        'ask': {
            'graph': {
                'clear': {
                    'object':raphael,
                    'action': 'clear',
                    'args': 0},
                'delete-node': {
                    'action': function(node_id) {
                        selected_node = node_id;
                        delete_node();
                    },
                    'args': 1},
            },
        },
    };
}


SylvaConsole.prototype.onKeyDown = function(e) {
    shell = this.shell;
    var KEY_UP = 38;
    var KEY_DOWN = 40;
    var KEY_ENTER = 13;
    
    var command = "";
    if (sessionStorage.getItem('historyLog') == "" || sessionStorage.getItem('historyLog') == null) {
        sessionStorage.setItem('historyLog', JSON.stringify([]));
    }
    this.historyLog = JSON.parse(sessionStorage.getItem('historyLog'));
    e = e ? e : window.event;
    var key = e.keyCode  ? e.keyCode : e.charCode ? e.charCode : e.which ? e.which : 0;
    switch (key) {
        case KEY_UP:
            if (shell.historyIndex == -1) {
                shell.historyIndex = shell.historyLog.length - 1;
            } else {
                shell.historyIndex = shell.historyIndex -1;
            }
            if (shell.historyIndex >= 0) {
                this.value = shell.historyLog[shell.historyIndex];
            }
            break;
        case KEY_DOWN:
            if (shell.historyIndex == -1) {
                shell.historyIndex = 0;
            } else {
                shell.historyIndex = shell.historyIndex + 1;
            }
            if (shell.historyIndex < shell.historyLog.length) {
                this.value = shell.historyLog[shell.historyIndex];
            }
            break;
        case KEY_ENTER:
            command = this.value;
            if (command != "") {
                shell.historyLog.push(command);
                sessionStorage.setItem('historyLog', JSON.stringify(shell.historyLog));
                shell.historyIndex = -1;
                shell.executeQuery(command);
                this.value = '';
            }
            break;
    }
}

SylvaConsole.prototype.executeQuery = function(_command) {
    commands = _command.split(' ');

    // Checks if the action is valid
    action = commands[0];
    if ((commands.length < 3) || (!this.shellCommands.hasOwnProperty(action))) {
        this.terminalLog.innerHTML = _command + " is not a valid action.";
        return;
    }

    // Checks if component is valid
    component = commands[1];
    if (!this.shellCommands[action].hasOwnProperty(component)) {
        this.terminalLog.innerHTML = component + " is not a valid component.";
        return;
    }

    // Checks if the command is valid for that component
    if (commands[2] == '[') {
        // Complex command
        complexCommand = commands.slice(3, -1);
        command = complexCommand[0];
        arguments = complexCommand.slice(1);
        if (!this.shellCommands[action][component].hasOwnProperty(command)) {
            this.terminalLog.innerHTML = command + " is not a valid command for this component.";
            return;
        }
        shellCommand = this.shellCommands[action][component][command];
        if (!shellCommand['args'] != (arguments.length-1)) {
            this.terminalLog.innerHTML = command + " takes exactly " + shellCommand['args'] + "arguments. " + (arguments.length) + " given.";
            return;
        }
        object = shellCommand['object'];
        if (object) {
            if (arguments.length == 0)
                object[shellCommand['action']]();
            else if (arguments.length == 1)
                object[shellCommand['action']](arguments[0]);
            else if (arguments.length == 2)
                object[shellCommand['action']](arguments[0], arguments[1]);
            else {
                this.terminalLog.innerHTML = "Too much arguments.";
                return;
            }
        }
        else {
            if (arguments.length == 0)
                shellCommand['action']();
            else if (arguments.length == 1)
                shellCommand['action'](arguments[0]);
            else if (arguments.length == 2)
                shellCommand['action'](arguments[0], arguments[1]);
            else {
                this.terminalLog.innerHTML = "Too much arguments.";
                return;
            }
        }
    } else {
        // Single command
        command = commands[2];
        if (!this.shellCommands[action][component].hasOwnProperty(command)) {
            this.terminalLog.innerHTML = command + " is not a valid command for this component.";
            return;
        }
        // Execute
        shellCommand = this.shellCommands[action][component][command];
        object = shellCommand['object'];
        if (object)
            object[shellCommand['action']]();
        else {
            shellCommand['action']();
        }
    }

   this.terminalLog.innerHTML = "Done!";
}
