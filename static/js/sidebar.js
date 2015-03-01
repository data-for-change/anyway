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
        "mouseover .current-view li" : "hoverEntry",
        "mouseout .current-view li" : "unhoverEntry"
    },
    initialize: function(options) {
        this.map = options.map;
        this.sidebarItemTemplate = _.template($("#sidebarItemTemplate").text());

//        google.maps.event.addListener(this.map, "center_changed", _.bind(this.updateMarkerList, this));

    },
    render: function() {

        this.$el.append($("#sidebar-template").html());
        this.$currentViewList = this.$el.find(".current-view");
        var self = this;

        this.$el.find("img.checkbox-accuracy")
            .data("checked", SHOW_INACCURATE);

        this.$el.find("img.checkbox-severity")
            .each(function() {
                    $(this).data("checked", LAYERS[$(this).data("type")]);
                }
            );

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
                checkboxImg.data("checked", 1 - checkboxImg.data("checked"));
                self.updateCheckboxIcon(checkboxImg);
                self.updateLayers();
            });

        this.$el.find("img.checkbox-accuracy").parent()
            .click(function() {
                var checkboxImg = $("img", this);
                checkboxImg.data("checked", 1 - checkboxImg.data("checked"));
                self.updateCheckboxIcon(checkboxImg);
                self.updateShowByAccuracy();
            });

        return this;
    },
    updateMarkerList: function(markerList) {
        // Set the marker list to empty array if it's not defined
        markerList = markerList || [];
        console.log('got a call with ' + markerList.length + ' markers');

        var bounds = this.map.getBounds();

        // Sort by decending order the marker list
        markerList = _.sortBy(markerList, function(marker) {
            return -1 * moment(marker.model.get("created")).unix();
        });


        var $viewList = $('<ul/>');
        var markerCount = 0;

        for (var i = 0; i < markerList.length; i++) {
            var markerView = markerList[i];
            var marker = markerView.marker;

            if (bounds.contains(marker.getPosition()) ){
                var markerModel = markerView.model;

                var entryHtml = this.sidebarItemTemplate({
                    created: moment(markerModel.get("created")).format("LLLL"),
                    type: SUBTYPE_STRING[markerModel.get("subtype") - 1],
                    icon: markerView.getIcon()
                });

                var $entry = $(entryHtml);
                $entry.data("marker", marker);

                $viewList.append($entry);
                markerCount++;
            }
        }

        this.$currentViewList.empty().append($viewList.find("li"));

        this.$el.find(".current-view-count").text(markerCount);

    },
    updateCheckboxIcon: function(img, hover) {
        var checked;
        if (hover == undefined) {
            checked = img.data("checked");
        } else {
            checked = 2;
        }
        var dataType = img.data("type");
        var icon = ICONS_PREFIX + CHECKBOX_ICONS[checked][dataType-1];
        img.attr("src", icon);
    },
    updateLayers: function() {
        this.$el.find("img.checkbox-severity").each(function() {
            attr = SEVERITY_ATTRIBUTES[parseInt($(this).data("type"))];
            app.model.set(attr, $(this).data("checked"));
        });
    },
    clickEntry: function(e) {
        this.getMarker(e).view.choose();
    },
    hoverEntry: function(e) {
        this.getMarker(e).view.highlight();
    },
    unhoverEntry: function(e) {
        this.getMarker(e).view.unhighlight();
    },
    getMarker: function(e) {
        return $(e.target).data("marker") || $(e.target).parents("li").data("marker");
    },
    updateShowByAccuracy: function() {
        this.$el.find("img.checkbox-accuracy").each(function() {
            app.model.set("showInaccurateMarkers", $(this).data("checked"));
        });
    }
});
