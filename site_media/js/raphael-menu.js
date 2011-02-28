var RaphaelMenu = {
    'width': 300,
    'draw' : function() {
        function draw_option(x,y,label,element) {
            menu_font = {"font-size": 30,
                    "fill": "#ccc",
                    "stroke-width":0.5,
                    "stroke":"black"};
            var t = raphael_menu.text(x,y,label);
            t.attr(menu_font);
            t.node.onmouseover = function() {t.attr("fill","#fff");
                                            t.animate({"font-size":50},100);};
            t.node.onmouseout = function() {t.attr("fill","#ccc");
                                            t.animate({"font-size":30},100);};
            t.node.onclick = function() {MenuControl.toggle(element);};

        }
        raphael_menu = Raphael("explorer_menu", this.width, 800);
        r = raphael_menu.rect(5,5,200,400,50);
        r.attr({"stroke":"#ADF1DA",
                "stroke-width":5,
                "opacity":0.5,
                "fill":"#C0D4EE"});
        t = raphael_menu.text(100,40,"Sylva");
        t.attr({"font-size": 50,
                "fill": "#ccc",
                "stroke-width":0.5,
                "stroke":"black"});
        start_position = 120;
        step = 50;
        menu_elements = ["Labels", "Topics", "Options"];
        dom_names = ["labels_menu", "topics_menu", "options_menu"];
        for(i=0;i<menu_elements.length;i++) {
            draw_option(100, start_position+i*step, menu_elements[i], dom_names[i]);
        }
        layouts = ["random", "circular", "spring", "ARF"];
        var layout = new DiscreteSlider(raphael_menu, "Layout", 30, start_position+i*step, layouts, raphael, 'draw');
        layout.draw()
    }
};


