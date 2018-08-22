var LocationSubscriptionDialog = Backbone.View.extend({
    className: "subscription-dialog",
    events: {
        "submit": "submit",
        "click .save-button": "submit",
        "click .close-button": "close"
    },
    initialize: function(options) {
        this.markers = options.markers;
        this.type = options.type;
        this.event = options.event;

    },
    render: function() {
        this.$el.append($("#subscription-dialog-template").html());
        $(document.body).append(this.$el);
        this.modal = this.$el.find(".modal");
        this.modal.modal("show");
        return this;
    },
    close: function() {
        this.modal.modal("hide");
    },
    submit: function() {
        var adr = this.$el.find("#emailAddress").val();
        var firstname = this.$el.find("#fName").val();
        var lastname = this.$el.find("#lName").val();
        var bounds = app.map.getBounds();
        if (!bounds) return null;
        var ne_lng = bounds.getNorthEast().lng();
        var ne_lat = bounds.getNorthEast().lat();
        var sw_lng = bounds.getSouthWest().lng();
        var sw_lat = bounds.getSouthWest().lat();

        $.post("location-subscription", JSON.stringify({
            'address': adr,
            'fname': firstname,
            'lname': lastname,
            'ne_lng': ne_lng,
            'ne_lat': ne_lat,
            'sw_lng': sw_lng,
            'sw_lat': sw_lat,
        }));
        this.close();
    }
});
/* function success(response) {
    alert(response);
    //do some stuff
} */
