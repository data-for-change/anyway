/**
 * Created by Avik on 07-Mar-16.
 */
var PreferencesDialog = Backbone.View.extend({
    className: "preferences-dialog",
    events: {        
        "click .save-button": "submit",
        "click .close-button": "close",
        "change .produceAccidentsReport" : "showHideReportPrefereces",
        "change .prefTypeOfAccidents" : "changeTypeOfAccidents",
        "change .prefDisableHistoricalReport" : "changeSendHistoricalReport"
    },     
    render: function () {
        var self = this;
        self.$el.append($("#preferences-dialog-template").html());
        $(document.body).append(self.$el);
        $.get("preferences", function (data) {
            self.$el.find("#prefAccidentSeverity").val(data["accident_severity"]);
            self.$el.find("#prefAccidentsLms").prop('checked', false);
            self.$el.find("#prefAccidentsIhud").prop('checked', false);
            var resource_types =  data["pref_resource_types"];
            if (resource_types != undefined) {
                for (i = 0; i < resource_types.length; i++) {
                    if (resource_types[i] == '1'){
                        self.$el.find("#prefAccidentsLms").prop('checked', true);
                    }else if (resource_types[i] == '2'){
                        self.$el.find("#prefAccidentsIhud").prop('checked', true);
                    }
                }
            }
            if (data["produce_accidents_report"]) {
                self.$el.find("#produceAccidentsReport").prop('checked', true);
                self.$el.find("#prefLat").val(data["lat"]);
                self.$el.find("#prefLon").val(data["lon"]);
                self.$el.find("#prefRadius").val(data["pref_radius"]);
                self.$el.find("#prefAccidentSeverityForReport").val(data["pref_accident_severity_for_report"]);
                if (data["how_many_months_back"] == '0'){
                    self.$el.find("#prefDisableHistoricalReport").prop('checked', true);
                    self.$el.find("#prefHistoricalReportPeriod").attr("disabled", "disabled");
                }else{
                    self.$el.find("#prefHistoricalReportPeriod").val(data["how_many_months_back"]);
                    self.$el.find("#prefDisableHistoricalReport").prop('checked', false);
                    self.$el.find("#prefHistoricalReportPeriod").removeAttr("disabled");
                }
            } else {
                self.$el.find("#produceAccidentsReport").prop('checked', false);
                $(".prefReportControls *").attr("disabled", "disabled");
            }                  
            self.modal = self.$el.find(".modal");
            self.modal.modal("show");
            return self;
        });
        
    },
    close: function () {
        this.modal.modal("hide");
    },
    submit: function () {   
        var accident_severity = this.$el.find("#prefAccidentSeverity :selected").val();    
        var resource_types = [];
        var prefAccidentsLms = this.$el.find("#prefAccidentsLms");
        if ($(prefAccidentsLms).is(':checked')) {
            resource_types.push($(prefAccidentsLms).val());
        }
        var prefAccidentsIhud = this.$el.find("#prefAccidentsIhud");
        if ($(prefAccidentsIhud).is(':checked')) {
            resource_types.push($(prefAccidentsIhud).val());
        }
        var produceAccidentsReport = this.$el.find("#produceAccidentsReport").is(':checked');
        var lat = this.$el.find("#prefLat").val();
        var lon = this.$el.find("#prefLon").val();
        var prefRadius = this.$el.find("#prefRadius :selected").val(); 
        var prefAccidentSeverityForReport = this.$el.find("#prefAccidentSeverityForReport :selected").val();               
        var prefDisableHistoricalReport = this.$el.find("#prefDisableHistoricalReport");
        var history_report;
        if ($(prefDisableHistoricalReport).is(':checked')){
            history_report = $(prefDisableHistoricalReport).val();
        }else{
            history_report = this.$el.find("#prefHistoricalReportPeriod :selected").val();
        }

        $.post("preferences", JSON.stringify({ 'accident_severity': accident_severity, 'pref_resource_types': resource_types,
                                             'produce_accidents_report': produceAccidentsReport, 'lat': lat, 'lon': lon, 'pref_radius': prefRadius, 'pref_accident_severity_for_report': prefAccidentSeverityForReport,
                                             'history_report': history_report }), 'json');
        this.close();
    },
    showHideReportPrefereces: function () {
        var produceAccidentsReport = this.$el.find("#produceAccidentsReport");
        if ($(produceAccidentsReport).is(':checked')) {
            $(".prefReportControls *").removeAttr("disabled");
        }else{
            $(".prefReportControls *").attr("disabled", "disabled");
        }
    },
    changeTypeOfAccidents : function (ev) {
        var prefAccidentsLms = this.$el.find("#prefAccidentsLms").is(':checked');
        var prefAccidentsIhud = this.$el.find("#prefAccidentsIhud").is(':checked');            
        if (!prefAccidentsLms && !prefAccidentsIhud) {
            $(ev.currentTarget).prop('checked', true);
        }
    },
    changeSendHistoricalReport : function(){
        var prefDisableHistoricalReport = this.$el.find("#prefDisableHistoricalReport").is(':checked');
        var prefHistoricalReportPeriod = this.$el.find("#prefHistoricalReportPeriod");
        if (prefDisableHistoricalReport){
            $(prefHistoricalReportPeriod).attr("disabled", "disabled");
        }else{
            $(prefHistoricalReportPeriod).removeAttr("disabled");
        }
    }
});



