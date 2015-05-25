var FeatureDialog = Backbone.View.extend({
	className: "feature-dialog",
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
		this.$el.append($("#feature-dialog-template").html());
		$(document.body).append(this.$el);
		this.modal = this.$el.find(".modal");
        this.modal.modal("show");
		return this;
	},
	close: function() {
		this.modal.modal("hide");
	},
	submit : function()
    {
        var adr = this.$el.find("#emailAddress").val();
        var firstname = this.$el.find("#fName").val();
        var lastname = this.$el.find("#lName").val();
        $.post("new-features", JSON.stringify({'address': adr, 'fname': firstname, 'lname': lastname}));
        this.close();
	}
});
 /* function success(response) {
    alert(response);
    //do some stuff
} */


