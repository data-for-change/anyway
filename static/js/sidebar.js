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
        this.sidebarItemTemplate = _.template($("#sidebarItemTemplate").text());

        google.maps.event.addListener(this.map, "center_changed", _.bind(this.updateMarkerList, this));

    },
    render: function() {
        this.$el.append($("#sidebar-template").html());
        this.$currentViewList = this.$el.find(".current-view");
        var self = this;
        this.$el.find("img.checkbox-severity")
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
        this.$el.find("input.checkbox-accuracy:checkbox")
            .click(function() {
                $(this).data("checked", !$(this).data("checked"));
                self.updateShowByAccuracy();
            });
        return this;
    },
    updateMarkerList: function() {
        var bounds = this.map.getBounds();

        var $viewList = $('<ul/>');

        for (var i = 0; i < app.markerList.length; i++) {
            var marker = app.markerList[i].marker;

            if (bounds.contains(marker.getPosition()) ){
                var markerModel = app.markerList[i].model;

                var entryHtml = this.sidebarItemTemplate({
                    created: moment(markerModel.get("created")).format("LLLL"),
                    type: SUBTYPE_STRING[markerModel.get("subtype")]
                });

                var $entry = $(entryHtml);
                $entry.data("marker", marker);

                $viewList.append($entry);
            }
        }

        this.$currentViewList.empty().append($viewList);
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
        this.$el.find("img.checkbox-severity").each(function() {
            layers[parseInt($(this).data("type"))] = $(this).data("checked");
        });
        app.model.set("layers", layers);
    },
    clickEntry: function(e) {
        var marker = $(e.target).data("marker") || $(e.target).parents("li").data("marker");
        marker.view.choose();
    },
    updateShowByAccuracy: function() {
        this.$el.find("input.checkbox-accuracy:checkbox").each(function() {
            app.model.set("showInaccurateMarkers", $(this).data("checked"));
        });
    }
});
