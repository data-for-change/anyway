var jsPanelInst;
var currentTypeOfChart = "accidentsPerMonth";

function statPanelClick(widthOfPanel, heightOfPanel, chartWidth, chartHeight) {
    jQuery.jsPanel({
        rtl: {
            rtl: true,
            lang: 'he'
        },
        size: {
            width: widthOfPanel,
            height: heightOfPanel
        },
        title: 'קצת גרפים',
        position: 'center',
        id: 'statPanel',
        theme: 'light',
        //callback: startJSPanelWithChart(jsPanel, widthOfPanel, heightOfPanel, chartWidth, chartHeight)
        callback: function(jsPanel) {
            jsPanelInst = jsPanel;
            startJSPanelWithChart(jsPanel, widthOfPanel, heightOfPanel, chartWidth, chartHeight);
        }
    });
};

var startJSPanelWithChart = function(jsPanel, widthOfPanel, heightOfPanel, chartWidth, chartHeight) {
    var str = '<select class="form-control" id="selectTypeOfChart">'
    str += '<option value="accidentsPerMonth" id="accidentsPerMonth">מספר התאונות בחודש על פני כל השנים שנבחרו</option>';
    str += '<option value="accidentsPerMonthStacked" id="accidentsPerMonthStacked">מספר התאונות בחודש - מקובץ לפי חודשים</option>';
    str += '</select>';
    str += '<div id="myChart" width="';
    str += chartWidth.toString();
    str += '" height="';
    str += chartHeight.toString();
    str += '"></div>';
    jsPanel.content.empty();
    jsPanel.content.append(str);
    //jsPanel.content.append('<canvas id="myChart" width=chartWidth height=chartHeight></canvas>')
    $("#selectTypeOfChart").width(300);
    $("#" + currentTypeOfChart).prop('selected', true);

    switch (currentTypeOfChart) {
        case "accidentsPerMonth":
            var groupedAccidentsByMonth = _.countBy(app.markers.pluck("created"), function(item) {
                return item.substring(0, 7);
            });
            var jsonAccidentsByMonth = _.map(groupedAccidentsByMonth, function(numOfAccidents, month) {
                return {
                    "label": month,
                    "value": numOfAccidents.toString()
                }
            });
            jsonAccidentsByMonth = _.sortBy(jsonAccidentsByMonth, 'label');

            FusionCharts.ready(function() {
                var statChart = new FusionCharts({
                    "type": "column2d",
                    "renderAt": "myChart",
                    "width": chartWidth,
                    "height": chartHeight,
                    "dataFormat": "json",
                    "dataSource": {
                        "chart": {
                            "caption": "מספר התאונות בחודש",
                            "xAxisName": "חודשים",
                            "yAxisName": "מספר תאונות",
                            "theme": "fint",
                            "labelFontSize": "15",
                            "yAxisNameFontSize": "20",
                            "xAxisNameFontSize": "20",
                            "captionFontSize": "25",
                        },
                        "data": jsonAccidentsByMonth
                    }
                });

                statChart.render();
            });

            break;
        case "accidentsPerMonthStacked":
            var groupedAccidentsByYear = _.countBy(app.markers.pluck("created"), function(item) {
                return item.substring(0, 4);
            });
            var groupedAccidentsByMonth = _.countBy(app.markers.pluck("created"), function(item) {
                return item.substring(5, 7);
            });
            var numberOfYears = Object.keys(groupedAccidentsByYear).length;
            var jsonAccidentsByMonth = _.map(groupedAccidentsByMonth, function(numOfAccidents, month) {
                return {
                    "label": month
                }
            });
            jsonAccidentsByMonth = _.sortBy(jsonAccidentsByMonth, 'label');

            var groupedAccidentsForAllYears = _.countBy(app.markers.pluck("created"), function(item) {
                return item.substring(0, 7);
            });

            var dataPerMonth = [];
            var dataObj = {};
            var dataOfValues = [];
            var dataValue = {};
            var tempProp;
            for (i = 0; i < numberOfYears; i++) {
                var numOfMonthTotal = Object.keys(groupedAccidentsForAllYears).length;
                dataOfValues = [];
                for (j = numOfMonthTotal - 1; j >= 0; j--) {
                    if (Object.keys(groupedAccidentsForAllYears)[j].substring(0, 4) === Object.keys(groupedAccidentsByYear)[i]) {
                        dataValue = new Object();
                        dataValue = {
                            value: groupedAccidentsForAllYears[Object.keys(groupedAccidentsForAllYears)[j]].toString()
                        };
                        dataOfValues.push(dataValue);
                        tempProp = Object.keys(groupedAccidentsForAllYears)[j];
                        delete groupedAccidentsForAllYears[tempProp];
                    }
                }
                dataObj = new Object();
                dataObj = {
                    seriesname: Object.keys(groupedAccidentsByYear)[i].toString(),
                    data: dataOfValues
                };
                dataPerMonth.push(dataObj);
            }

            var categories = {
                category: jsonAccidentsByMonth
            };

            FusionCharts.ready(function() {
                var statChart = new FusionCharts({
                    "type": "stackedcolumn2d",
                    "renderAt": "myChart",
                    "width": chartWidth,
                    "height": chartHeight,
                    "dataFormat": "json",
                    "dataSource": {
                        "chart": {
                            "caption": "מספר התאונות בחודש",
                            "xAxisName": "חודשים - מקובץ מכל השנים שנבחרו",
                            "yAxisName": "מספר תאונות",
                            "theme": "fint",
                            "showSum": "1",
                            "labelFontSize": "15",
                            "yAxisNameFontSize": "20",
                            "xAxisNameFontSize": "20",
                            "captionFontSize": "25",
                        },
                        "categories": categories,
                        "dataset": dataPerMonth
                    }
                });

                statChart.render();
            });

            break;
            //var groupedAccidentsByMonth = _.countBy(app.markers.pluck("created"), function(item) {
            //   return item.substring(5,7);
            //});
            //var jsonAccidentsByMonth = _.map(groupedAccidentsByMonth, function(numOfAccidents, month) {return {"label": month, "value": numOfAccidents.toString()}});
            //jsonAccidentsByMonth = _.sortBy(jsonAccidentsByMonth, 'label');
            //
            //FusionCharts.ready(function(){
            // var statChart = new FusionCharts({
            //   "type": "column2d",
            //   "renderAt": "myChart",
            //   "width": chartWidth,
            //   "height": chartHeight,
            //   "dataFormat": "json",
            //   "dataSource": {
            //   "chart": {
            //	  "caption": "מספר התאונות בחודש",
            //	  "xAxisName": "חודשים - מקובץ מכל השנים שנבחרו",
            //	  "yAxisName": "מספר תאונות",
            //	  "theme": "fint",
            //	  "labelFontSize": "15",
            //	  "yAxisNameFontSize": "20",
            //	  "xAxisNameFontSize": "20",
            //	  "captionFontSize": "25",
            //   },
            //  "data": jsonAccidentsByMonth
            //  }
            //});
            //
            //statChart.render();
            //});
    }

    $("#selectTypeOfChart").on("change", function() {
        if (jsPanelInst != null) {
            currentTypeOfChart = $("#selectTypeOfChart").val();
            startJSPanelWithChart(jsPanelInst, $("#statPanel").width(), $("#statPanel").height(),
                $("#statPanel").width() - 30, $("#statPanel").height() - 80, $("#selectTypeOfChart").val());
        }
    });

};

$('body').on("jspanelloaded", function(event, id) {
    event.preventDefault();
    $('body').on("jspanelstatechange", function(event, id) {
        if (id === "statPanel") {
            if (jsPanelInst != null) {
                startJSPanelWithChart(jsPanelInst, $("#statPanel").width(), $("#statPanel").height(),
                    $("#statPanel").width() - 30, $("#statPanel").height() - 80);
            }
        }
    });
});

$("body").on("jspanelclosed", function closeHandler(event, id) {
    if (id === "statPanel") {
        jsPanelInst = null;
        // close handlers attached to body should be removed again
        //$("body").off("jspanelclosed", closeHandler);
    }
});