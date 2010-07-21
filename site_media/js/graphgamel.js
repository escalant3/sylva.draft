var GRAPHGAMEL = {
    'populate_table': function(table_id, properties, controls) {
        table = document.getElementById('properties_table');
        table.innerHTML = "";
        i = 1;
        for (var key in properties) {
            if (key.length > 0 && key[0] != "_") {
                tr = document.createElement('tr');
                td = document.createElement('td');
                td.appendChild(document.createTextNode(key));
                tr.appendChild(td);
                td = document.createElement('td');
                td.appendChild(document.createTextNode(properties[key]));
                tr.appendChild(td);
                if (controls) {
                    td = document.createElement('td');
                    td.innerHTML = '<a class="changelink" onClick="GRAPHGAMEL.modify_property(\'' + key + '\')">Edit</a>';
                    tr.appendChild(td);
                    td = document.createElement('td');
                    td.innerHTML = '<a class="deletelink" onClick="GRAPHGAMEL.delete_property(\'' + key + '\')">Delete</a>';
                    tr.appendChild(td);
                }
                tr.className = "row" + i%2;
                table.appendChild(tr);
                i++;
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
                            } else {
                                alert('Unable to add property')
                            }
                        }});
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
                            alert('Unable to edit property')
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
                                alert('Unable to delete property');
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
                    success: function() {console.log('Success');}
                    });
        }
    }

}
