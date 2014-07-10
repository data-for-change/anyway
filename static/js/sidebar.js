var ICONS_PREFIX = "/static/img/menu icons/";
var CHECKBOX_ICONS = [
    ["deadly-unchecked.png", "severe-unchecked.png", "medium-unchecked.png"],
    ["deadly-checked.png",   "severe-checked.png",   "medium-checked.png"],
    ["deadly-hover.png",     "severe-hover.png",     "medium-hover.png"]
];

var SidebarView = Backbone.View.extend({
    className: "info-window",
    events: {
        "click .current-view li" : "clickEntry",
    },
    initialize: function(options) {
        this.map = options.map;
        google.maps.event.addListener(this.map, "center_changed", _.bind(this.updateMarkerList, this));

    },
    render: function() {
        this.$el.append($("#sidebar-template").html());
        this.$currentViewList = this.$el.find(".current-view");
        var self = this;
        this.$el.find("img.checkbox-image")
            .each(function() {
                self.updateCheckboxIcon($(this));
            })
            .click(function() {
                $(this).data("checked", !$(this).data("checked"));
                self.updateCheckboxIcon($(this));
                self.updateLayers();
            })
            .mouseover(function() {
                self.updateCheckboxIcon($(this), "hover");
            })
            .mouseout(function() {
                self.updateCheckboxIcon($(this));
            });
        return this;
    },
    updateMarkerList: function() {
        var bounds = this.map.getBounds();
        this.$currentViewList.empty();

        var sortedMarkerList = app.markerList.slice(0);
        sortedMarkerList.sort( // sort by date in descending order
            function(a,b){
                return (moment(a.model.get("created")) < moment(b.model.get("created")) ? 1 : -1);
            });

        for (var i = 0; i < sortedMarkerList.length; i++) {
            if (bounds.contains(sortedMarkerList[i].marker.getPosition()) ){
                var marker = sortedMarkerList[i].marker;
                var markerModel = sortedMarkerList[i].model;

                var entry = $("#list-entry li").clone();

                entry.find(".date").text(moment(markerModel.get("created")).format("LLLL"));
                entry.find(".type").text(SUBTYPE_STRING[markerModel.get("subtype")]);
                entry.data("marker", marker);
                this.$currentViewList.append(entry);
            }
        }
    },
    updateCheckboxIcon: function(img, hover) {
        var checked;
        if (hover == undefined) {
            checked = img.data("checked") ? 1 : 0;
        } else {
            checked = 2;
        }
        var dataType = img.data("type");
        var icon = ICONS_PREFIX + CHECKBOX_ICONS[checked][dataType-1];
        img.attr("src", icon);
    },
    updateLayers: function() {
        var layers = [];
        this.$el.find("img.checkbox-image").each(function() {
            layers[parseInt($(this).data("type"))] = $(this).data("checked");
        });
        app.model.set("layers", layers);
    },
    clickEntry: function(e) {
        var marker = $(e.target).data("marker") || $(e.target).parents("li").data("marker");
        marker.view.choose();
    }
});
