var RaphaelMenu = {
    'width': 200,
    'show_topics': function() {
        MenuControl.toggle('topics_menu');
    },
    'draw' : function(raphael_graph) {
        raphael_menu = Raphael("explorer_menu", this.width, raphael_graph.height);
        r = raphael_menu.rect(5,5,180,400,50);
        r.attr({"stroke":"#000",
                "stroke-width":5,
                "opacity":0.3,
                "fill":"#000"});
        t = raphael_menu.text(100,35,"Sylva");
        t.attr({"font-size": 40,
                "fill": "#ccc",
                "stroke-width":0.5,
                "stroke":"black"});
        
        // Buttons
        xInit = 20;
        yInit = 80;
        xStep = 80;
        yStep = 20;
        i=0;
        j=0;
        var topicsButton = new Button(raphael_menu, xInit+xStep*i, yInit+yStep*j, "Topics", this.show_topics);
        topicsButton.draw();
        j=1;
        var button2 = new Button(raphael_menu, xInit+xStep*i, yInit+yStep*j, "BTN2", undefined);
        //button2.draw();
        i=1;
        j=0;
        var button3 = new Button(raphael_menu, xInit+xStep*i, yInit+yStep*j, "BTN3", undefined);
        //button3.draw();
        j=1;
        var button4 = new Button(raphael_menu, xInit+xStep*i, yInit+yStep*j, "BTN4", undefined);
        //button4.draw();

        // Sliders
        xInit = 25;
        yInit = 150;
        yStep = 50
        i=0;
        labels = ["id", "", "ID", "type"]
        var labelControl = new DiscreteSlider(raphael_menu, "Label", xInit, yInit+i*yStep, labels, raphael, 'toggle_labels');
        labelControl.draw()
        i++;
        layouts = ["random", "circular", "spring", "ARF"];
        var layout = new DiscreteSlider(raphael_menu, "Layout", xInit, yInit+i*yStep, layouts, raphael, 'draw');
        layout.draw()
        i++;
        sizes = [Math.floor(raphael.width) + "x" + Math.floor(raphael.height),
                "800x800", "1024x768", "1280x800"];
        var canvasSizeControl = new DiscreteSlider(raphael_menu, "Canvas Size",
                    xInit, yInit+i*yStep, sizes, raphael, 'set_size');
        canvasSizeControl.draw();
        
    }
};


