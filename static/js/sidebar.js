var SidebarView = Backbone.View.extend({
	className: "info-window",
	events: {
		"click .current-view li" : "clickEntry"
	},
	initialize: function(options) {
		this.map = options.map;
		google.maps.event.addListener(this.map, 'center_changed', _.bind(this.updateMarkerList, this));

	},
	render: function() {
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

		for(var i = 0; i < sortedMarkerList.length; i++) {
			if( bounds.contains(sortedMarkerList[i].marker.getPosition()) ){
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
	clickEntry: function(e) {
		var marker = $(e.target).data("marker") || $(e.target).parents("li").data("marker");
		//this.map.setCenter(marker.getPosition());
		new google.maps.event.trigger( marker, 'click' );

	}
});
