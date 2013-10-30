var MarkerDialog = Backbone.View.extend({
	className: "marker-dialog",
	events: {
		"submit" : "submit",
		"click .save-button" : "submit",
		"click .close-button" : "close"
	},
	initialize: function(options) {
		this.markers = options.markers;
		this.type = options.type;
		this.event = options.event;

	},
	render: function() {
		this.$el.append($("#marker-dialog-template").html());
		$(document.body).append(this.$el);
		this.modal = this.$el.find(".modal");
		this.modal.modal("show");
		return this;
	},
	close: function() {
		this.modal.modal("hide");
	},
	submit : function() {
		this.markers.create({
			type: this.type,
			latitude: this.event.latLng.lat(),
			longitude: this.event.latLng.lng(),
			title: this.$el.find("#title").val(),
			description: this.$el.find("#description").val()
		}, {wait: true});

		this.close();
	}

});