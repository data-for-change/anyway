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
    emptyMarkerList: function() {
        this.$currentViewList.empty();
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

                var entryHtml = this.sidebarItemTemplate({
                    created: moment(markerModel.get("created")).format("LLLL"),
                    type: localization.SUG_TEUNA[markerModel.get("subtype")],
                    icon: markerView.getTitle("single"),
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
    },
    setResponsively: function() {
        //set .filter-panel after .filter-descriptionand .filter-menu
        var filterPanelTop = this.$el.find(".filter-description").outerHeight() + this.$el.find(".filter-menu").outerHeight();
        var filterPanel = this.$el.find(".filter-panel");
        $(filterPanel).css("top", filterPanelTop);
        //set .current-view after .btn-label and .btn-wrap
        var currentViewTop = this.$el.find("#step6tour .btn-label").outerHeight() + this.$el.find("#step6tour .btn-wrap").outerHeight();
        var currentView = this.$el.find(".current-view");
        $(currentView).css("top", currentViewTop);
    }
});
