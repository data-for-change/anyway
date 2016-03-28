/**
 * Created by Avik on 07-Mar-16.
 */
var PreferencesDialog = Backbone.View.extend({
    className: "preferences-dialog",
    events: {        
        "click .save-button": "submit",
        "click .close-button": "close"
    },    
    render: function () {
        self = this;
        self.$el.append($("#preferences-dialog-template").html());
        $(document.body).append(self.$el);
        $.get("preferences", function (data) {
            self.$el.find("#prefLat").val(data["lat"]);
            self.$el.find("#prefLon").val(data["lon"]);
            self.$el.find("#prefDistance").val(data["distance"]);
            self.$el.find("#prefAccidentSeverity").val(data["accident_severity"]);
            if (data["history_report"] == true) {
                self.$el.find("#prefHistoryReportTrue").prop('checked', true);                
            } else {
                self.$el.find("#prefHistoryReportTrue").prop('checked', false);
            }
            self.$el.find("#prefHistoryReportTrue")
            self.modal = self.$el.find(".modal");
            self.modal.modal("show");
            return self;
        });
        
    },
    close: function () {
        this.modal.modal("hide");
    },
    submit: function () {        
        var lat = this.$el.find("#prefLat").val();
        var lon = this.$el.find("#prefLon").val();
        var distance = this.$el.find("#prefDistance").val();
        var accident_severity = this.$el.find("#prefAccidentSeverity :selected").val();
        var history_report = this.$el.find("#prefHistoryReportTrue").is(":checked");        
        $.post("preferences", JSON.stringify({ 'lat': lat, 'lon': lon, 'distance': distance, 'accident_severity': accident_severity, 'history_report': history_report }), 'json');
        this.close();
    }
});



