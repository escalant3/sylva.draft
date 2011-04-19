var GRAPHGAMEL = {
    'can_add': false,
    'can_edit': false,
    'can_delete': false,
    'special_fields': [],
    'permission_error': 'Your user has not privilegies to perform that action',
    'internalfield_error': ' is a internal field and cannot be modified by the user',
    'requiredfield_error': ' is a required property and cannot be deleted',
    'populate_table': function(table_id, properties) {
        table = document.getElementById(table_id);
        table.innerHTML = "";
        i = 1;
        this.special_fields = [];
        for (var key in properties) {
            if (key.length > 0) {
                tr = document.createElement('tr');
                td = document.createElement('td');
                td.appendChild(document.createTextNode(key));
                tr.appendChild(td);
                td = document.createElement('td');
                info = properties[key];
                if (this.isURL(info)) {
                    t = document.createTextNode('Open link');
                    a = document.createElement('a');
                    a.setAttribute('href', info);
                    a.setAttribute('target', '_blank');
                    a.appendChild(t);
                    td.appendChild(a);
                } else {
                    td.appendChild(document.createTextNode(info));
                }
                tr.appendChild(td);
                if (this.can_edit) {
                    td = document.createElement('td');
                    td.innerHTML = '<a class="changelink" onClick="GRAPHGAMEL.modify_property(\'' + key + '\')">Edit</a>';
                    tr.appendChild(td);
                }
                if (this.can_delete) { 
                    td = document.createElement('td');
                    td.innerHTML = '<a class="deletelink" onClick="GRAPHGAMEL.delete_property(\'' + key + '\')">Delete</a>';
                    tr.appendChild(td);
                }
                tr.className = "row" + i%2;
                table.appendChild(tr);
                i++;
            } else if (key[0] == "_") {
                this.special_fields.push(key);
            }
        }
    },

    'add_property':function() {
        property_key = document.getElementById('new_property_key').value;
        property_value = document.getElementById('new_property_value').value;
        $.ajax({url: location.href + "add_property",
                dataType: "json",
                type: "GET",
                data: {property_key: property_key,
                        property_value: property_value},
                success: function(response){
                            if (response['success']) {
                                GRAPHGAMEL.populate_table('properties_table', response['properties']);
                                document.getElementById('new_property_key').value = "";
                                document.getElementById('new_property_value').value = "";
                            } else {
                                GRAPHGAMEL.error(response);
                            }
                        },
                });
    },

    'modify_property': function(property) {
        new_value = prompt("New value");
        $.ajax({url: location.href + "modify_property",
            dataType: "json",
            type: "GET",
            data: {property_key: property,
                    property_value: new_value},
            success: function(response){
                        if (response['success']) {
                            GRAPHGAMEL.populate_table('properties_table', response['properties']);
                        } else {
                            GRAPHGAMEL.error(response);
                        }
                    }});
    },

    'delete_property': function(property) {
        $.ajax({url: location.href + "delete_property",
                dataType: "json",
                type: "GET",
                data: {property_key: property},
                success: function(response){
                            if (response['success']) {
                                GRAPHGAMEL.populate_table('properties_table', response['properties']);
                            } else {
                                GRAPHGAMEL.error(response);
                            }
                        }});
    },

    'populate_select': function(select, data_source, blank_option) {
        if (blank_option) {
            select.options[0] = new Option("---", "");
            i = 1;
        } else {
            i = 0;
        }
        for (var key in data_source) {
            select.options[i] = new Option(key, key);
            i++;
        }
    },

    'delete_node': function() {
        if (window.confirm("This will delete the node and all its relationships. Are you sure?")) {
            $.ajax({url: location.href + "delete_node",
                    dataType: "json",
                    success: function() {;}
                    });
        }
    },

    'get_autocompletion_objects': function(type_field, value_field) {
        graph_id = location.pathname.split("/")[1];
        url = "/" + graph_id + "/get_autocompletion_objects";
        $.ajax({url: url,
            data: {node_type: document.getElementById(type_field).value},
            dataType: "json",
            success: function(response) {
                $("input#"+value_field).flushCache();
                $("#"+value_field).autocomplete(response);
            }
        });
    },

    'populate_embed_objects': function(list, properties) {
        for(i=0;i<list.length;i++) {
            element = list[i][0]
            key = list[i][1];
            if (this.special_fields.indexOf(key) != -1 ) {
                document.getElementById(element).innerHTML = properties[key];
            }
        }
    },

    'isURL': function(data) {
        if (!data.hasOwnProperty('match')) return false;
        return ((data.match('^http://') == 'http://') || (data.match('^https://') == 'https://'));
    },

    'error': function(response) {
        if (response['nopermission']) {
            alert(GRAPHGAMEL.permission_error);
        } else if (response['internalfield']) {
            alert(response['internalfield'] + GRAPHGAMEL.internalfield_error);
        } else if (response['required']) {
            alert(response['required'] + GRAPHGAMEL.requiredfield_error);
        } else {
            alert('An uknown error ocurred')
        }
    }

}
