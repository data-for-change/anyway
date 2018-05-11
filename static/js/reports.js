$(function(){

//Models:
var ReportType = Backbone.Model.extend({});
var ReportTypeData  = Backbone.Model.extend({});

var reportTypes = [
new ReportType({'id':1, 'name': 'accidentsNearSchool', 'caption':'תאונות ליד בתי-ספר'}),
new ReportType({'id':2, 'name': 'accidentsPedestrian', 'caption':'תאונות של הולכי-רגל'}),
];

var reportTypesData = [
new ReportTypeData({'id':1, 'name': 'accidentsNearSchool', 'caption':'ברדיוס 100מ\'', url:'/static/data/reports/accidents_near_schools_100m.xlsx'}),
new ReportTypeData({'id':2, 'name': 'accidentsNearSchool', 'caption':'ברדיוס 300מ\'', url:'/static/data/reports/accidents_near_schools_300m.xlsx'}),
new ReportTypeData({'id':3, 'name': 'accidentsNearSchool', 'caption':'ברדיוס 500מ\'', url:'/static/data/reports/accidents_near_schools_500m.xlsx'}),
new ReportTypeData({'id':4, 'name': 'accidentsPedestrian', 'caption':'ברדיוס 100מ\'', url:'/static/data/reports/pedestrian_accidents_100m.xlsx'}),
new ReportTypeData({'id':5, 'name': 'accidentsPedestrian', 'caption':'ברדיוס 300מ\'', url:'/static/data/reports/pedestrian_accidents_300m.xlsx'}),
new ReportTypeData({'id':6, 'name': 'accidentsPedestrian', 'caption':'ברדיוס 500מ\'', url:'/static/data/reports/pedestrian_accidents_500m.xlsx'}),
];

//Collections:
var ReportTypes = Backbone.Collection.extend({
    model: ReportType
});

var ReportTypesData = Backbone.Collection.extend({
    model: ReportTypeData
});



//Views:
var ReportView = Backbone.View.extend({
    tagName:'option',
    initialize: function(){
    _.bindAll(this, 'render');
    this.render();
    },
    render: function(){
        $(this.el).attr('value', this.model.get('id')).html(this.model.get('caption'));
        return this;
    }
});


var ReportsView = Backbone.View.extend({
    events: {
    'change':'changeSelected'
    },

    initialize: function(){
        _.bindAll(this, 'addOne', 'addAll');
        this.collection.bind('reset', this.addAll);
        this.addAll();
    },

    addOne: function(report){
        var reportView = new ReportView({ model: report});
        this.reportViews.push(reportView);
        $(this.el).append(reportView.render().el);
    },
    addAll: function(){
        _.each(this.reportViews, function(reportView){ reportView.remove(); });
        this.reportViews = [];
        this.collection.each(this.addOne);
    },
    changeSelected: function(){
        this.setSelectedId($(this.el).val());
    },
    populateFrom: function(reportTypeId){
        var reportTypeResult = _.find(reportTypes, function(reportType){
            return reportType.get('id') == reportTypeId;
        });

        if(reportTypeResult){
            var reportTypesDataColl = _.filter(reportTypesData, function(reportTypeData){
                return reportTypeData.get('name') == reportTypeResult.get('name');
            });
            this.collection.reset(reportTypesDataColl);
            this.setDisabled(false);

        }else{
            this.collection.reset();
            this.setSelectedId('');
            this.setDisabled(true);
        }
    },
    setDisabled: function(disabled){
        $(this.el).attr('disabled', disabled);
    }
});

var ReportTypesView = ReportsView.extend({
    setSelectedId: function(reportTypeId) {
        this.reportTypesDataView.populateFrom(reportTypeId);
    }
});

var ReportTypesDataView = ReportsView.extend({
    setSelectedId: function(reportTypeDataId) {

        var data = _.find(reportTypesData, function(reportTypeData){
           return reportTypeData.get('id') == reportTypeDataId;
        });
        if(data){
            $("#selectedTypeUrl a").attr('href', data.get('url')).html('לחץ כאן להורדה');
        }else{
            $("#selectedTypeUrl a").attr('href', '').html('');
        }
    }
});

var reportTypesView = new ReportTypesView({ el: $("#selectTypeOfReport"), collection: new ReportTypes(reportTypes)});
var reportTypesDataView = new ReportTypesDataView({ el: $('#selectTypeOfReportData'), collection: new ReportTypesData() });

reportTypesView.reportTypesDataView = reportTypesDataView;
reportTypesView.setSelectedId('');
});