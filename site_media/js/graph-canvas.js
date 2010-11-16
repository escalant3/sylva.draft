function RaphaelGraph(_data) {
    this.width = window.innerWidth * 0.85;
    this.height = window.innerHeight * 0.95;
    this.paper = Raphael("canvas", this.width, this.height);
    this.data = _data;
    this.elements = {};
    raphael_object = this;
    this.paper.raphael_object = this;
}

RaphaelGraph.prototype.NODE_SIZE = 10;
RaphaelGraph.prototype.NODE_ANIMATION_TIME = 250;
RaphaelGraph.prototype.XMARGIN = 5;
RaphaelGraph.prototype.YMARGIN = 5;
RaphaelGraph.prototype.show_labels = false;
RaphaelGraph.prototype.node_label_field = "";
RaphaelGraph.prototype.node_label_field = "";
RaphaelGraph.prototype.multiselection = false;
RaphaelGraph.prototype.multiselection_table = [];
RaphaelGraph.prototype.events_enabled = true;
RaphaelGraph.prototype.default_node_color = "#f00";
RaphaelGraph.prototype.font_color = "#000";

RaphaelGraph.prototype.draw = function draw(layout) {
    nodes = this.data.nodes;
    edges = this.data.edges;
    width = this.width - 2 * this.NODE_SIZE;
    height = this.height - 2 * this.NODE_SIZE;
    switch (layout) {
        case "random": GraphLayout.random_layout(nodes, width, height);break;
        case "spring": GraphLayout.spring_layout(nodes,edges,25,width,height);break;
        case "circular": GraphLayout.circular_layout(nodes, width, height);break;
        case "ARF": GraphLayout.ARF_layout(nodes,edges,25,width,height);break;
    }
    this.render();
}

RaphaelGraph.prototype.render = function render() {
    this.paper.clear();
    this.elements = {};
    for (var node in this.data.nodes) {
        node_dict = this.data.nodes[node];
        if (!node_dict.hasOwnProperty('_visible') || node_dict['_visible'] == true) {
            this.draw_node(this.data.nodes[node]);
        }
    };
    for (var e in this.data.edges) {
        edge = this.data.edges[e]
        node1_dict = this.data.nodes[edge.node1];
        node2_dict = this.data.nodes[edge.node2];
        if ((!node1_dict.hasOwnProperty('_visible') || node1_dict['_visible']) && 
            (!node2_dict.hasOwnProperty('_visible') || node2_dict['_visible'])) {
            this.draw_edge(edge);
        }
    };
}

RaphaelGraph.prototype.draw_node = function draw_node(node) {
    var c = this.paper.circle(node._xpos, node._ypos, this.NODE_SIZE);
    this.elements[node.id] = {};
    this.elements[node.id]["object"] = c;
    this.elements[node.id]["edges"] = {};
    if (node.hasOwnProperty("color")) {
        c.attr("fill", node["color"]);
    } else {
        c.attr("fill", this.default_node_color);
    }
    raphael = this;
    if (this.events_enabled) {
        c.node.onclick = function() {
            selected_node = node.id;
            selected_edge = null;
            info_html = raphael.info_as_table(node);
            if (!raphael.multiselection) {
                MenuControl.toggle('element_info_menu');
                raphael.show_node_action_box(node._xpos + raphael.XMARGIN,
                                    node._ypos + raphael.YMARGIN);
            } else {
                raphael.multiselection_table.push(selected_node);
                raphael.show_node_multiselection_box();
            };
        };
        c.node.onmouseover = function () {
            c.animate({"scale": "2 2"}, raphael.NODE_ANIMATION_TIME);
        };
        c.node.onmouseout = function () {
            c.animate({"scale": "1 1"}, raphael.NODE_ANIMATION_TIME);
        };

        function move(dx, dy) {
            this.update(dx - (this.dx || 0), dy - (this.dy || 0));
            this.dx = dx;
            this.dy = dy;
        }

        function up() {
            this.dx = this.dy = 0;
        }

        c.update = function (dx, dy) {
            x = this.attr("cx") + dx;
            y = this.attr("cy") + dy;
            this.attr({cx: x, cy: y});
            node_dragged = raphael.data.nodes[node.id]
            node_dragged._xpos = x;
            node_dragged._ypos = y;
            edges = raphael.elements[node.id].edges;
            for (var node_id in edges) {
                edges[node_id].remove();
                edge = {};
                edge.node1 = node.id;
                edge.node2 = node_id;
                raphael.draw_edge(edge, false);
            }
        }
        c.drag(move, up);
    }
    if (this.show_labels == true) {
        var t = this.paper.text(node._xpos-this.NODE_SIZE,
                                node._ypos-this.NODE_SIZE,
                                node[this.node_label_field]);
        t.attr({fill:this.font_color});
    }
};

RaphaelGraph.prototype.draw_edge = function draw_edge(edge) {
    node1 = this.data.nodes[edge.node1];
    node2 = this.data.nodes[edge.node2];
    string_path = "M" + node1._xpos + " " + node1._ypos + 
                    "L" + node2._xpos + " " + node2._ypos;
    var e = this.paper.path(string_path);
    this.elements[edge.node1]["edges"][edge.node2] = e;
    this.elements[edge.node2]["edges"][edge.node1] = e;
    raphael = this;

    if (this.events_enabled) {
        e.node.onclick = function (event) {
            selected_node = null;
            selected_edge = edge.ID;
            MenuControl.toggle('element_info_menu');
            info_html = raphael.info_as_table(edge);
            xpos = event.clientX;
            ypos = event.clientY;
            raphael.show_edge_action_box(xpos, ypos);
        }
        e.node.onmouseover = function () {
            e.attr("stroke", "red");
        };
        e.node.onmouseout = function () {
            e.attr("stroke", "black");
        };
        e.attr("stroke", "black");
        e.toBack();
    }
    if (this.show_labels == true) {
        central_point_x = (node1._xpos + node2._xpos)/2;
        central_point_y = (node1._ypos + node2._ypos)/2;
        var t = this.paper.text(central_point_x,
                                central_point_y,
                                edge[this.edge_label_field]);
        t.attr({fill:this.font_color});
    }
};

RaphaelGraph.prototype.show_node_action_box = function show_node_action_box(xpos, ypos) {
    document.getElementById('floating_node_menu').style.display='block';
    document.getElementById('floating_edge_menu').style.display='none';
};

RaphaelGraph.prototype.show_edge_action_box = function show_edge_action_box(xpos, ypos) {
    document.getElementById('floating_edge_menu').style.display='block';
    document.getElementById('floating_node_menu').style.display='none';
};

RaphaelGraph.prototype.show_node_multiselection_box = function show_node_multiselection_box() {
    document.getElementById('floating_multinode_menu').style.top = "10px";
    document.getElementById('floating_multinode_menu').style.left = "10px";
    document.getElementById('floating_multinode_menu').style.display = "block";
}

RaphaelGraph.prototype.info_as_table = function info_as_table(element) {
    html_table = "<table>";
    for (var field in element) {
        if (field.length && field[0]!="_") {
            element_value = element[field];
            if (element[field] instanceof Object) {
                element_value = "";
                for (var j in element[field]) {
                    element_value += "<p>" + j + ": " + element[field][j] + "</p>";
                }
            } else {
                element_value = element[field];
            }
            html_table += "<tr><td class=\"label\">" + field +
                        ":</td><td class=\"data\">" + element_value + 
                        "</td></tr>";
            }
    }
    html_table += "</table>";
    document.getElementById("infoTable").innerHTML = html_table;
}

RaphaelGraph.prototype.toggle_labels = function toggle_labels(label_field) {
    this.node_label_field = label_field;
    this.edge_label_field = label_field;
    this.show_labels = !this.show_labels;
    raphael_object.render()
}

RaphaelGraph.prototype.remove_node = function remove_node(node) {
    node_edges = this.elements[node]["edges"];
    for (var i in node_edges) {
        node_edges[i].remove();
    }
    this.elements[node]["object"].remove();
}

RaphaelGraph.prototype.remove_edge = function remove_edge(node1, node2) {
    this.elements[node1]["edges"][node2].remove();
    delete this.elements[node1]["edges"][node2];
    delete this.elements[node2]["edges"][node1];
}

RaphaelGraph.prototype.update = function update(_data) {
    GraphLayout.random_layout(_data.nodes, this.width, this.height);
    for (var i in _data.nodes) {
        if (this.data.nodes[i] == undefined) {
            this.data.nodes[i]= _data.nodes[i];
        }
    }
    this.data.edges = _data.edges;
    this.render();
}

RaphaelGraph.prototype.set_size = function set_size(width, height) {
    this.width = width;
    this.height = height;
    this.paper.setSize(width, height);
}

RaphaelGraph.prototype.delete_node = function delete_node(selected_node) {
    delete this.data.nodes[selected_node];
    edges = this.data.edges;
    for (var e in edges) {
        if (edges[e].node1 == selected_node || edges[e].node2 == selected_node) {
            delete edges[e];
        }
    }
    this.render();
}

RaphaelGraph.prototype.toggle_nodes = function toggle_nodes(node_type) {
    for (var node_id in this.data.nodes) {
        node = this.data.nodes[node_id];
        if (node["type"] == node_type) {
            if (node.hasOwnProperty("_visible")) {
                node["_visible"] = !node["_visible"];
            } else {
                node["_visible"] = false;
            }
        }
    }
    raphael.render();
}