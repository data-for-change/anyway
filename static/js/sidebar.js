var ICONS_PREFIX = "/static/img/menu icons/";
var CHECKBOX_ICONS = [
    ["deadly-unchecked.png", "severe-unchecked.png", "medium-unchecked.png", "location-acc-unchecked.png"],
    ["deadly-checked.png",   "severe-checked.png",   "medium-checked.png",   "location-acc-checked.png"],
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

        this.$el.find("img.checkbox-severity, img.checkbox-accuracy")
            .each(function() {
                self.updateCheckboxIcon($(this));
            });

        this.$el.find("img.checkbox-severity").parent()
            .mouseover(function() {
                self.updateCheckboxIcon($("img", this), "hover");
            })
            .mouseout(function() {
                self.updateCheckboxIcon($("img", this));
            });

        this.$el.find("img.checkbox-severity").parent().click(function() {
                var checkboxImg = $("img", this);
                checkboxImg.data("checked", !checkboxImg.data("checked"));
                self.updateCheckboxIcon(checkboxImg);
                self.updateLayers();
            });

        this.$el.find("img.checkbox-accuracy").parent()
            .click(function() {
                var checkboxImg = $("img", this);
                checkboxImg.data("checked", !checkboxImg.data("checked"));
                self.updateCheckboxIcon(checkboxImg);


                self.updateShowByAccuracy();
            });
        return this;
    },
    updateMarkerList: function(markersList) {
        // Set the marker list to empty array if it's not defined
        markersList = markersList || [];

        var bounds = this.map.getBounds();

        // Sort by decending order the marker list
        markersList = _.sortBy(markersList, function(marker) {
            return -1 * moment(marker.model.get("created")).unix();
        });


        var $viewList = $('<ul/>');

        for (var i = 0; i < markersList.length; i++) {
            var markerView = markersList[i];
            var marker = markerView.marker;

            if (bounds.contains(marker.getPosition()) ){
                var markerModel = markerView.model;

                var entryHtml = this.sidebarItemTemplate({
                    created: moment(markerModel.get("created")).format("LLLL"),
                    type: SUBTYPE_STRING[markerModel.get("subtype")],
                    icon: markerView.getIcon()
                });

                var $entry = $(entryHtml);
                $entry.data("marker", marker);

                $viewList.append($entry);
            }
        }

        this.$currentViewList.empty().append($viewList.find("li"));

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
        this.$el.find("img.checkbox-accuracy").each(function() {
            app.model.set("showInaccurateMarkers", $(this).data("checked"));
        });
    }
});
