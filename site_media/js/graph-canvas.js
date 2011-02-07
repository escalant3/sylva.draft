function RaphaelGraph(_data) {
    this.width = Math.min(window.innerWidth * 0.75, 1600);
    this.height = Math.min(window.innerHeight * 0.95, 800);
    this.paper = Raphael("canvas", this.width, this.height);
    this.data = _data;
    this.elements = {};
    this.labels = {};
    raphael_object = this;
    this.paper.raphael_object = this;
    counter = 0;
    this.info_box = undefined;
    this.showing_info_box = false;
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
RaphaelGraph.prototype.dragging = false;

RaphaelGraph.prototype.draw = function draw(layout) {
    for (var node in this.data.nodes) counter++;
    this.number_of_nodes = counter;
    this.NODE_SIZE = (this.width / 5) / this.number_of_nodes;
    GraphLayout.margin = this.NODE_SIZE;
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
    this.canvas = this.paper.rect(5,5,this.width-10,this.height-10,50);
    this.canvas.attr({"fill":"#EBEBEB",
                "stroke-width":5,
                "stroke":"#C0D4EE",
                "opacity":0.50});

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
    this.canvas.toBack();
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
    c.attr("stroke-width",this.NODE_SIZE/20);
    raphael = this;
    if (this.events_enabled) {
        c.node.onclick = function(position) {
            selected_node = node.id;
            selected_edge = null;
            info_html = raphael.info_as_table(node);
            if (raphael.dragging) {
                raphael.dragging = false;
                raphael.canvas.toBack();
            } else {
                if (!raphael.dragging && !raphael.multiselection) {
                    //MenuControl.toggle('element_info_menu');
                    raphael.show_node_action_box(position.clientX + raphael.XMARGIN,
                                        position.clientY + raphael.YMARGIN);
                } else {
                    raphael.enable_selection(node.id);
                    raphael.multiselection_table.push(selected_node);
                    //raphael.show_node_multiselection_box();
                };
            };
        };
        c.node.onmouseover = function () {
            c.attr("stroke","red");
        };
        c.node.onmouseout = function () {
            c.attr("stroke","black");
        };

        function move(dx, dy) {
            raphael.dragging = true;
            this.update(dx - (this.dx || 0), dy - (this.dy || 0));
            this.dx = dx;
            this.dy = dy;
        }

        function down() {
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
            for (var relation_id in edges) {
                for (var node_id in edges[relation_id]) {
                    edges[relation_id][node_id].remove();
                    edge = {};
                    edge.node1 = node.id;
                    edge.node2 = node_id;
                    edge.id = relation_id;
                    raphael.draw_edge(edge);
                }
           }
           raphael.draw_label(node_dragged);
 
        }
        c.drag(move, down);
    }
    this.draw_label(node);
};

RaphaelGraph.prototype.draw_edge = function draw_edge(edge) {
    node1 = this.data.nodes[edge.node1];
    node2 = this.data.nodes[edge.node2];
    string_path = "M" + node1._xpos + " " + node1._ypos + 
                    "L" + node2._xpos + " " + node2._ypos;
    var e = this.paper.path(string_path);
    e.attr({"stroke-width": this.NODE_SIZE/12,
            "stroke": "#000000"});
    if (this.elements[edge.node1]["edges"][edge.id] == undefined) 
        this.elements[edge.node1]["edges"][edge.id] = {};
    if (this.elements[edge.node2]["edges"][edge.id] == undefined) 
        this.elements[edge.node2]["edges"][edge.id] = {};
    this.elements[edge.node1]["edges"][edge.id][edge.node2] = e;
    this.elements[edge.node2]["edges"][edge.id][edge.node1] = e;
    raphael = this;

    if (this.events_enabled) {
        e.node.onclick = function (event) {
            selected_node = null;
            selected_edge = [edge.node1, edge.node2];
            //MenuControl.toggle('element_info_menu');
            //info_html = raphael.info_as_table(edge);
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
        if (this.labels[edge.node1+edge.id+edge.node2] != undefined)
            this.labels[edge.node1+edge.id+edge.node2].remove();
        central_point_x = (node1._xpos + node2._xpos)/2;
        central_point_y = (node1._ypos + node2._ypos)/2;
        var t = this.paper.text(central_point_x,
                                central_point_y,
                                edge[this.edge_label_field]);
        
        this.labels[edge.node1+edge.id+edge.node2] = t;
        this.labels[edge.node2+edge.id+edge.node1] = t;
        t.attr({fill:this.font_color});
    } else {
        this.labels[edge.node1+edge.id+edge.node2] = undefined;
        this.labels[edge.node2+edge.id+edge.node1] = undefined;
    }
};

RaphaelGraph.prototype.draw_label = function draw_label(node) {
    if (this.show_labels == true) {
        var t = this.paper.text(node._xpos-this.NODE_SIZE,
                                node._ypos-this.NODE_SIZE,
                                node[this.node_label_field]);
        t.attr({fill:this.font_color});
        if (this.labels[node.id] != undefined) 
             this.labels[node.id].remove();
        this.labels[node.id] = t;
    } else {
        this.labels[node.id] = undefined;
    }
};

RaphaelGraph.prototype.show_node_action_box = function show_node_action_box(xpos, ypos) {
    if (this.showing_info_box)
        this.info_box.remove();
    raphael = this;
    this.info_box = this.paper.set();
    this.showing_info_box = true;
    xpos = xpos-RaphaelMenu.width;
    r = this.paper.rect(xpos, ypos, 20, 20, 10);
    r.attr({"stroke":"#ADF1DA",
                "stroke-width":5,
                "opacity":0.75,
                "fill":"#000"});
    r.animate({"width":160, "height":200}, 200);
    r.node.onclick = function() {raphael.info_box.remove();};
    this.info_box.push(r);
    buttons = ["Delete", "Expand", "Multiselection"];
    functions = [delete_node, expand_node, multi_select];
    xpos += 20;
    for(i=0;i<buttons.length;i++)
        this.create_button(this.info_box, xpos, ypos+20+i*60, buttons[i],
        functions[i]);

    // Info box dragging
    function move(dx, dy) {
        raphael.info_box.update(dx - (this.dx || 0), dy - (this.dy || 0));
        this.dx = dx;
        this.dy = dy;
    }

    function down() {
        this.dx = this.dy = 0;
    }

    raphael.info_box.update = function (dx, dy) {
        x = raphael.info_box.attr("cx") + dx;
        y = raphael.info_box.attr("cy") + dy;
        raphael.info_box.attr({cx: x, cy: y});
    }
    raphael.info_box.drag(move, down);
};

RaphaelGraph.prototype.create_button = function(set, x, y, label, f) {
    var button = this.paper.set()
    raphael = this;
    var r = this.paper.rect(x,y,1,1,10);
    r.attr({"stroke":"#ADF1DA",
            "stroke-width":1,
            "opacity":0.75,
            "fill":"#fff"});
    r.animate({"width":120, "height":40}, 300);
    r.node.onmouseover = function() {r.attr({"fill":"yellow"})};
    r.node.onmouseout = function() {r.attr({"fill":"white"})};
    r.node.onclick = function() {raphael.showing_info_box=false;
                                f();};
    var t = this.paper.text(x+55,y+20,label).attr({"font-size":18,
                                         "fill": "black",
                                        "stroke-width":0.5,
                                        "stroke":"white"});
    t.node.onmouseover = r.node.onmouseover;
    t.node.onmouseout = r.node.onmouseout;
    t.node.onclick = r.node.onclick;
    set.push(r);
    set.push(t);
}

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
    this.NODE_SIZE = (this.width / 8) / this.number_of_nodes;
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

RaphaelGraph.prototype.delete_edge = function delete_edge(selected_edge) {
    node1 = selected_edge[0];
    node2 = selected_edge[1];
    for (var edge_id in this.data.edges) {
        edge = this.data.edges[edge_id];
        if ((edge.node1 == node1 && edge.node2 == node2) ||
            (edge.node1 == node2 && edge.node2 == node1)) {
                delete this.data.edges[edge_id];
                break;
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

RaphaelGraph.prototype.enable_selection = function enable_selection(node_id){
    c = this.elements[node_id]["object"];
    c.attr("stroke-width", this.NODE_SIZE/5);
}

RaphaelGraph.prototype.disable_selection = function disable_selection(node_id){
    c = this.elements[node_id]["object"];
    c.attr("stroke-width", this.NODE_SIZE/20);
}

