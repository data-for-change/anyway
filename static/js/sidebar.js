var ICONS_PREFIX = "/static/img/menu icons/";
var CHECKBOX_ICONS = [
    ["deadly-unchecked.png", "severe-unchecked.png", "medium-unchecked.png"],
    ["deadly-checked.png",   "severe-checked.png",   "medium-checked.png"],
    ["deadly-hover.png",     "severe-hover.png",     "medium-hover.png"]
];

function getCheckbox(img) {
    return $("#" + img.attr("id").replace(/^checkboxImage/, ""))
}

function updateCheckboxIcon(img, hover) {
    var o = getCheckbox(img);
    var checked;
    if (hover == undefined) {
        checked = o.prop("checked") ? 1 : 0;
    } else {
        checked = 2;
    }
    var dataType = o.attr("data-type");
    var icon = ICONS_PREFIX + CHECKBOX_ICONS[checked][dataType-1];
    img.attr("src", icon);
}

var SidebarView = Backbone.View.extend({
    className: "info-window",
    events: {
        "click .current-view li" : "clickEntry",
        "change input[type=checkbox]" : "updateCheckbox"
    },
    initialize: function(options) {
        this.map = options.app.map;
        this.appModel = options.app.model;
        google.maps.event.addListener(this.map, "center_changed", _.bind(this.updateMarkerList, this));

    },
    render: function() {
        $("input[type=checkbox]").each(this.replaceCheckbox);
        this.$el.on("click", "img.checkboxImage", function(e) {
            img = $(e.target);
            updateCheckboxIcon(img);
            var o = getCheckbox(img);
            o.prop("checked", !o.prop("checked"));
            o.trigger("change");
        });
        this.$el.on("mouseover", "img.checkboxImage", function(e) {
            updateCheckboxIcon($(e.target), "hover");
        });
        this.$el.on("mouseout", "img.checkboxImage", function(e) {
            updateCheckboxIcon($(e.target));
        });
        this.$el.append($("#sidebar-template").html());
        this.$currentViewList = this.$el.find(".current-view");
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
    replaceCheckbox: function() {
        var id = $(this).attr("id");
        var img = $("<img></img>")
            .attr("id", "checkboxImage" + id)
            .addClass("checkboxImage");
        updateCheckboxIcon(img);
        $(this).hide()
            .parent()
            .prepend(img);
    },
    updateCheckbox: function() {
        var layers = [];
        this.$el.find("input[type=checkbox]").each(function() {
            layers[parseInt($(this).data("type"))] = $(this).prop("checked");
        });
        this.appModel.set("layers", layers);
    },
    clickEntry: function(e) {
        var marker = $(e.target).data("marker") || $(e.target).parents("li").data("marker");
        new google.maps.event.trigger( marker, "click" );

    }
});
