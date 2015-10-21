var CLUSTER_MODE_SIDEBAR_TEXT = 'התקרב על מנת לצפות ברשימת התאונות';
var markerCount = 0;

var SidebarView = Backbone.View.extend({
    className: "info-window",
    events: {
        "click .current-view li" : "clickEntry",
    },
    initialize: function(options) {
        this.map = options.map;
        this.sidebarItemTemplate = _.template($("#sidebarItemTemplate").text());
    },
    render: function() {
        this.$el.append($("#sidebar-template").html());
        this.$currentViewList = this.$el.find(".current-view");
        var self = this;
        return this;
    },
    showClusterMessage: function() {
        this.$currentViewList.empty();
        this.$el.find(".current-view-count").text('');
        this.$el.find(".current-view").append('<li>' + CLUSTER_MODE_SIDEBAR_TEXT +'</li>');
    },
    reloadMarkerList: function(markerList) {
        // Set the marker list to empty array if it's not defined
        markerList = markerList || [];
        markerCount = 0;
        var bounds = this.map.getBounds();

        // Sort by decending order the marker list
        markerList = _.sortBy(markerList, function(marker) {
            return -1 * moment(marker.model.get("created")).unix();
        });

        var $viewList = $('<ul/>');


        for (var i = 0; i < markerList.length; i++) {
            var markerView = markerList[i];
            var marker = markerView.marker;

            if (bounds.contains(marker.getPosition()) ){
                var markerModel = markerView.model;
                if (markerModel.get("type") == MARKER_TYPE_DISCUSSION) {
                    continue;
                }

                var iconUrl = markerView.getIcon();
                if (isRetina){
                    iconUrl = iconUrl.url;
                }

                var entryHtml = this.sidebarItemTemplate({
                    created: moment(markerModel.get("created")).format("LLLL"),
                    type: localization.SUG_TEUNA[markerModel.get("subtype")],
                    //icon: iconUrl
                });

                var $entry = $(entryHtml);
                $entry.data("marker", marker);

                $viewList.append($entry);
                markerCount++;
            }
        }

        this.$currentViewList.empty().append($viewList.find("li"));
        this.$el.find(".current-view-count").text(markerCount);
        app.updateFilterString();
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
    getMarker: function(e) {
        return $(e.target).data("marker") || $(e.target).parents("li").data("marker");
    }
});
