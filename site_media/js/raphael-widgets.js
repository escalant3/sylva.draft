function DiscreteSlider(r, label, xpos, ypos, values, object, method) {
    this.r = r;
    this.label = label;
    this.xpos = xpos;
    this.ypos = ypos;
    this.values = values;
    this.option = 0;
    this.object = object;
    this.method = method;
}

DiscreteSlider.prototype.draw = function() {
    var label = this.r.text(this.xpos+67, this.ypos-5,
                        this.label).
                        attr({fill: "#666", stroke: "none",
                        "font": '100 10px "Helvetica Neue", Helvetica, "Arial Unicode MS", Arial, sans-serif'});

    var bg = this.r.rect(this.xpos, this.ypos, 134, 26, 13).
                        attr({fill: "#666", stroke: "none"});
    var text = this.r.text(this.xpos+67, this.ypos+13,
                        this.values[this.option]).
                        attr({fill: "#fff", stroke: "none",
                        "font": '100 18px "Helvetica Neue", Helvetica, "Arial Unicode MS", Arial, sans-serif'});
    var rightc = this.r.circle(this.xpos+121, this.ypos+13, 10).
                        attr({fill: "#fff", stroke: "none"});
    var right = this.r.path("M" + (this.xpos+118) +","+
                        (this.ypos+8) +"l10,5 -10,5z").
                        attr({fill: "#000"});
    var leftc = this.r.circle(this.xpos+13, this.ypos+13, 10).
                        attr({fill: "#fff", stroke: "none"});
    var left = this.r.path("M" + (this.xpos+17) + ","+ (this.ypos+8) +
                        "l-10,5 10,5z").
                        attr({fill: "#000"});
    var slider = this;
    rightc.node.onclick = right.node.onclick = function () {
        slider.option++;
        if (slider.option == slider.values.length) slider.option--;
        slider.object[slider.method](slider.values[slider.option]);
        text.attr({text: slider.values[slider.option]});
    };
    leftc.node.onclick = left.node.onclick = function () {
        slider.option--;
        if (slider.option < 0) slider.option=0;
        slider.object[slider.method](slider.values[slider.option]);
        text.attr({text: slider.values[slider.option]});
    };
}

function Button(r, x, y, label, f) {
    this.r = r;
    this.xpos = x;
    this.ypos = y;
    this.label = label;
    this.f = f;
    this.style = {
        "btnStrokeColor": "ADF1DA",
        "btnStrokeWidth": 1,
        "btnOpacity": 0.75,
        "btnColor": "#FFF",
        "btnWidth": 70,
        "btnHeight": 15,
        "btnAngle": 10,
        "btnAnimationTime": 50,
        "btnFontSize": 10,
        "btnFontColor": "black",
        "btnFontStrokeColor": "white",
        "btnFontStrokeWidth": 0,
    }
}

Button.prototype.draw = function() {
    var rect = this.r.rect(this.xpos, this.ypos, 1,1,this.style.btnAngle);
    rect.attr({"stroke": this.style.btnStrokeColor,
            "stroke-width": this.style.btnStrokeWidth,
            "opacity": this.style.btnOpacity,
            "fill": this.style.btnColor});
    rect.animate({"width": this.style.btnWidth,
                "height": this.style.btnHeight},
                this.style.fwbtnAnimationTime);
    var t = this.r.text(this.xpos+35,this.ypos+8,this.label).attr({
                        "font-size": this.style.btnFontSize,
                        "fill": this.style.btnFontColor,
                        "stroke-width": this.style.btnFontStrokeWidth,
                        "stroke": this.style.btnFontStrokeColor});
    var button = this;
    t.node.onmouseover = rect.node.onmouseover = function() {
                            rect.attr({"fill":"yellow"})};
    t.node.onmouseout = rect.node.onmouseout = function() {
                            rect.attr({"fill":"white"})};
    t.node.onclick = rect.node.onclick = function() {button.f();};
}
