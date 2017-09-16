var jsPanelInst;
var currentTypeOfChart = "accidentsPerMonth";
var currentDataType = "numberType";

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
}

var startJSPanelWithChart = function(jsPanel, widthOfPanel, heightOfPanel, chartWidth, chartHeight) {
    var isClusterMode = false;
    var str = '<div>';
    str += '<select class="form-control" id="selectTypeOfChart">';
    str += '<option value="accidentsPerMonth" id="accidentsPerMonth">מספר התאונות בחודש על פני כל השנים שנבחרו</option>';
    str += '<option value="accidentsPerMonthStacked" id="accidentsPerMonthStacked">מספר התאונות בחודש - מקובץ לפי חודשים</option>';
    str += '<option value="severityTotal" id="severityTotal">מספר התאונות לפי דרגת חומרה</option>';
    str += '<option value="severityPerMonth" id="severityPerMonth">מספר התאונות בחודש לפי דרגת חומרה</option>';
    str += '<option value="severityPerMonthStacked" id="severityPerMonthStacked">מספר התאונות בחודש לפי דרגת חומרה - מקובץ לפי חודשים</option>';
    str += '<option value="ageGroup" id="ageGroup">נפגעים לפי קבוצת גיל</option>';
    str += '<option value="accidentsBySexAndAge" id="accidentsBySexAndAge">נפגעים לפי קבוצת גיל ומין</option>';
    str += '</select>';
    str += '<select class="form-control" id="selectTypeOfData">';
    str += '<option value="numberType" id="numberType">מספרים</option>';
    str += '<option value="percentType" id="percentType">אחוזים</option>';
    str += '</select>';
    str += '</div>';
    str += '<div id="myChart" width="';
    str += chartWidth.toString();
    str += '" height="';
    str += chartHeight.toString() + '">';
    if (app.markers.length === 0 && app.clusters.length > 0) {
        isClusterMode = true;
        str += '<h2> אין נתונים להצגה. אנא הגדל/י את רמת המיקוד במפה </h2>';
    }
    str += '</div>';
    jsPanel.content.empty();
    jsPanel.content.append(str);
    //jsPanel.content.append('<canvas id="myChart" width=chartWidth height=chartHeight></canvas>')
    $("#selectTypeOfChart").width(360);
    $("#selectTypeOfData").width(100);
    $("#" + currentTypeOfChart).prop('selected', true);
    $("#" + currentDataType).prop('selected', true);

    if (isClusterMode) {
        return;
    }

    if (currentTypeOfChart === "accidentsBySexAndAge"){
        $('#selectTypeOfData').hide();
    }else{
        $('#selectTypeOfData').show();
    }

    switch (currentTypeOfChart) {
        case "accidentsPerMonth":
            var sum;
            var jsonAccidentsByMonth;
            var groupedAccidentsByMonth = _.countBy(app.markers.pluck("created"), function(item) {
                return item.substring(0, 7);
            });

            if (currentDataType === "percentType") {
                sum = _.reduce(groupedAccidentsByMonth, function(num1, num2) {
                    return num1 + num2;
                }, 0);
                jsonAccidentsByMonth = _.map(groupedAccidentsByMonth, function(numOfAccidents, month) {
                    return {
                        "label": month,
                        "value": (numOfAccidents / sum).toFixed(2)
                    };
                });
            } else {
                jsonAccidentsByMonth = _.map(groupedAccidentsByMonth, function(numOfAccidents, month) {
                    return {
                        "label": month,
                        "value": numOfAccidents.toString()
                    };
                });
            }

            jsonAccidentsByMonth = _.sortBy(jsonAccidentsByMonth, 'label');

            if (currentDataType === "percentType") {
                FusionCharts.ready(function() {
                    var statChart = new FusionCharts({
                        "type": "column2d",
                        "renderAt": "myChart",
                        "width": chartWidth,
                        "height": chartHeight,
                        "dataFormat": "json",
                        "dataSource": {
                            "chart": {
                                "caption": "מספר התאונות בחודש באחוזים",
                                "xAxisName": "חודשים",
                                "yAxisName": "אחוז התאונות מסך התאונות",
                                "theme": "fint",
                                "labelFontSize": "15",
                                "yAxisNameFontSize": "20",
                                "xAxisNameFontSize": "20",
                                "captionFontSize": "25",
                                "numberScaleValue": ".01",
                                "numberScaleUnit": "%",
                            },
                            "data": jsonAccidentsByMonth
                        }
                    });

                    statChart.render();
                });
            } else {
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
            }

            break;
        case "accidentsPerMonthStacked":

            var groupedAccidentsByYear = _.countBy(app.markers.pluck("created"), function(item) {
                return item.substring(0, 4);
            });
            var jsonAccidentsByYear = _.map(groupedAccidentsByYear, function(numOfAccidents, year) {
                return {
                    "label": year,
                    "value": numOfAccidents.toString()
                };
            });
            jsonAccidentsByYear = _.sortBy(jsonAccidentsByYear, 'label');
            var groupedAccidentsByMonth = _.countBy(app.markers.pluck("created"), function(item) {
                return item.substring(5, 7);
            });
            var numberOfYears = jsonAccidentsByYear.length;
            var jsonAccidentsByMonth = _.map(groupedAccidentsByMonth, function(numOfAccidents, month) {
                return {
                    "label": month
                };
            });
            jsonAccidentsByMonth = _.sortBy(jsonAccidentsByMonth, 'label');
            var groupedAccidentsForAllYears = _.countBy(app.markers.pluck("created"), function(item) {
                return item.substring(0, 7);
            });
            var jsonAccidentsByMonthAllYears = _.map(groupedAccidentsForAllYears, function(numOfAccidents, month) {
                return {
                    "label": month,
                    "value": numOfAccidents.toString()
                };
            });
            jsonAccidentsByMonthAllYears = _.sortBy(jsonAccidentsByMonthAllYears, 'label');
            var dataPerMonth = [];
            var dataObj = {};
            var dataOfValues = [];
            var dataValue = {};
            var counter;
            for (i = 0; i < numberOfYears; i++) {
                var numOfMonthTotal = jsonAccidentsByMonthAllYears.length;
                dataOfValues = [];
                counter = 0;
                for (j = 0; j < numOfMonthTotal; j++) {
                    dataValue = new Object();
                    if (jsonAccidentsByMonthAllYears[j]["label"].substring(0, 4) === jsonAccidentsByYear[i]["label"]) {
                        if (currentDataType === "percentType") {
                            dataValue = {
                                value: (jsonAccidentsByMonthAllYears[j]["value"] /
                                    groupedAccidentsByMonth[jsonAccidentsByMonthAllYears[j]["label"].substring(5, 7)]).toFixed(2)
                            };
                        } else {
                            dataValue = {
                                value: jsonAccidentsByMonthAllYears[j]["value"].toString()
                            };
                        }
                        jsonAccidentsByMonthAllYears.splice(j, 1);
                        j--;
                        numOfMonthTotal--;
                    } else {
                        dataValue = {
                            value: "0"
                        };
                    }
                    dataOfValues.push(dataValue);
                }
                dataObj = new Object();
                dataObj = {
                    seriesname: jsonAccidentsByYear[i]["label"].toString(),
                    data: dataOfValues
                };
                dataPerMonth.push(dataObj);
                counter++;
                numOfMonthTotal = jsonAccidentsByMonthAllYears.length;
                if (counter > 11) {
                    break;
                }

            }

            var categories = {
                category: jsonAccidentsByMonth
            };

            if (currentDataType === "percentType") {
                FusionCharts.ready(function() {
                    var statChart = new FusionCharts({
                        "type": "stackedcolumn2d",
                        "renderAt": "myChart",
                        "width": chartWidth,
                        "height": chartHeight,
                        "dataFormat": "json",
                        "dataSource": {
                            "chart": {
                                "caption": "מספר התאונות בחודש באחוזים",
                                "xAxisName": "חודשים - מקובץ מכל השנים שנבחרו",
                                "yAxisName": "אחוז התאונות מסך התאונות החודשי",
                                "theme": "fint",
                                "labelFontSize": "15",
                                "yAxisNameFontSize": "20",
                                "xAxisNameFontSize": "20",
                                "captionFontSize": "25",
                                "stack100Percent": "1",
                                "decimals": "0",
                            },
                            "categories": categories,
                            "dataset": dataPerMonth
                        }
                    });

                    statChart.render();
                });
            } else {
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
            }


            break;
        case "severityTotal":
            var sum;
            var jsonAccidentsBySeverity;
            var groupedAccidentsBySeverity = _.countBy(app.markers.pluck("severity"), function(item) {
                return item;
            });

            if (currentDataType === "percentType") {
                sum = _.reduce(groupedAccidentsBySeverity, function(num1, num2) {
                    return num1 + num2;
                }, 0);
                jsonAccidentsBySeverity = _.map(groupedAccidentsBySeverity, function(numOfAccidents, severity) {
                    return {
                        "label": severity,
                        "value": (numOfAccidents / sum).toFixed(2)
                    };
                });
            } else {
                jsonAccidentsBySeverity = _.map(groupedAccidentsBySeverity, function(numOfAccidents, severity) {
                    return {
                        "label": severity,
                        "value": numOfAccidents.toString()
                    };
                });
            }


            jsonAccidentsBySeverity = _.sortBy(jsonAccidentsBySeverity, 'label');

            for (i = 0; i < jsonAccidentsBySeverity.length; i++) {
                switch (jsonAccidentsBySeverity[i]["label"]) {
                    case "1":
                        jsonAccidentsBySeverity[i]["label"] = "קטלנית";
                        jsonAccidentsBySeverity[i]["color"] = "#d81c32";
                        break;
                    case "2":
                        jsonAccidentsBySeverity[i]["label"] = "קשה";
                        jsonAccidentsBySeverity[i]["color"] = "#ff9f1c";
                        break;
                    case "3":
                        jsonAccidentsBySeverity[i]["label"] = "קלה";
                        jsonAccidentsBySeverity[i]["color"] = "#ffd82b";
                        break;
                }
            }
            if (currentDataType === "percentType") {
                FusionCharts.ready(function() {
                    var statChart = new FusionCharts({
                        "type": "column2d",
                        "renderAt": "myChart",
                        "width": chartWidth,
                        "height": chartHeight,
                        "dataFormat": "json",
                        "dataSource": {
                            "chart": {
                                "caption": "מספר התאונות לפי חומרה באחוזים",
                                "xAxisName": "חומרת התאונות",
                                "yAxisName": "אחוז התאונות מסך התאונות",
                                "theme": "fint",
                                "showSum": "1",
                                "labelFontSize": "15",
                                "yAxisNameFontSize": "20",
                                "xAxisNameFontSize": "20",
                                "captionFontSize": "25",
                                "numberScaleValue": ".01",
                                "numberScaleUnit": "%",
                            },
                            //"categories": categories,
                            "data": jsonAccidentsBySeverity
                        }
                    });

                    statChart.render();
                });
            } else {
                FusionCharts.ready(function() {
                    var statChart = new FusionCharts({
                        "type": "column2d",
                        "renderAt": "myChart",
                        "width": chartWidth,
                        "height": chartHeight,
                        "dataFormat": "json",
                        "dataSource": {
                            "chart": {
                                "caption": "מספר התאונות לפי חומרה",
                                "xAxisName": "חומרת התאונות",
                                "yAxisName": "מספר תאונות",
                                "theme": "fint",
                                "showSum": "1",
                                "labelFontSize": "15",
                                "yAxisNameFontSize": "20",
                                "xAxisNameFontSize": "20",
                                "captionFontSize": "25",
                            },
                            //"categories": categories,
                            "data": jsonAccidentsBySeverity
                        }
                    });

                    statChart.render();
                });
            }

            break;
        case "severityPerMonth":
        case "severityPerMonthStacked":
            var models = [];
            var doesAlreadyExists;
            var monthCategories = [];
            var dataset = [];
            var dataValuesLethal = [];
            var dataValuesSevere = [];
            var dataValuesLight = [];
            var lastDate;
            var currentDate;
            var found;
            app.markers.each(function(model) {
                if (currentTypeOfChart === "severityPerMonth") {
                    models.push({
                        created: model.get("created").substring(0, 7),
                        severity: model.get("severity")
                    });
                } else {
                    models.push({
                        created: model.get("created").substring(5, 7),
                        severity: model.get("severity")
                    });
                }
            });
            models = _.sortBy(models, 'created');

            if (models.length > 0) {
                lastDate = models[0]["created"];
            }

            for (var index = 0; index < models.length; index++) {
                doesAlreadyExists = false;
                currentDate = models[index]["created"];
                if (currentDate != lastDate) {
                    PushZeroValues(dataValuesLethal, dataValuesSevere, dataValuesLight, lastDate);
                    lastDate = currentDate;
                }

                switch (models[index]["severity"]) {
                    case 1:
                        for (i = 0; i < dataValuesLethal.length; i++) {
                            if (dataValuesLethal[i]["label"] === models[index]["created"]) {
                                dataValuesLethal[i]["value"]++;
                                doesAlreadyExists = true;
                                break;
                            }
                        }
                        if (doesAlreadyExists === false) {
                            dataValuesLethal.push({
                                label: models[index]["created"],
                                value: 1
                            });
                        }
                        break;
                    case 2:
                        for (i = 0; i < dataValuesSevere.length; i++) {
                            if (dataValuesSevere[i]["label"] === models[index]["created"]) {
                                dataValuesSevere[i]["value"]++;
                                doesAlreadyExists = true;
                                break;
                            }
                        }
                        if (doesAlreadyExists === false) {
                            dataValuesSevere.push({
                                label: models[index]["created"],
                                value: 1
                            });
                        }
                        break;
                    case 3:
                        for (i = 0; i < dataValuesLight.length; i++) {
                            if (dataValuesLight[i]["label"] === models[index]["created"]) {
                                dataValuesLight[i]["value"]++;
                                doesAlreadyExists = true;
                                break;
                            }
                        }
                        if (doesAlreadyExists === false) {
                            dataValuesLight.push({
                                label: models[index]["created"],
                                value: 1
                            });
                        }
                        break;
                }

                found = monthCategories.some(function(el) {
                    return el.label === models[index]["created"];
                });
                if (!found) {
                    monthCategories.push({
                        label: models[index]["created"]
                    });
                }
            }

            PushZeroValues(dataValuesLethal, dataValuesSevere, dataValuesLight, lastDate);

            dataValuesLethal = _.sortBy(dataValuesLethal, 'label');
            dataValuesSevere = _.sortBy(dataValuesSevere, 'label');
            dataValuesLight = _.sortBy(dataValuesLight, 'label');

            if (currentDataType === "percentType") {

                for (var index = 0; index < dataValuesLethal.length; index++) {
                    dataValuesLethal[index]["value"] = (parseFloat(dataValuesLethal[index]["value"]) /
                        (parseFloat(dataValuesLethal[index]["value"]) +
                            parseFloat(dataValuesSevere[index]["value"]) +
                            parseFloat(dataValuesLight[index]["value"]))).toFixed(2);
                    delete dataValuesLethal[index]["label"];
                }

                for (var index = 0; index < dataValuesSevere.length; index++) {
                    dataValuesSevere[index]["value"] = (parseFloat(dataValuesSevere[index]["value"]) /
                        (parseFloat(dataValuesLethal[index]["value"]) +
                            parseFloat(dataValuesSevere[index]["value"]) +
                            parseFloat(dataValuesLight[index]["value"]))).toFixed(2);
                    delete dataValuesSevere[index]["label"];
                }

                for (var index = 0; index < dataValuesLight.length; index++) {
                    dataValuesLight[index]["value"] = (parseFloat(dataValuesLight[index]["value"]) /
                        (parseFloat(dataValuesLethal[index]["value"]) +
                            parseFloat(dataValuesSevere[index]["value"]) +
                            parseFloat(dataValuesLight[index]["value"]))).toFixed(2);
                    delete dataValuesLight[index]["label"];
                }
            } else {
                for (var index = 0; index < dataValuesLethal.length; index++) {
                    delete dataValuesLethal[index]["label"];
                }

                for (var index = 0; index < dataValuesSevere.length; index++) {
                    delete dataValuesSevere[index]["label"];
                }

                for (var index = 0; index < dataValuesLight.length; index++) {
                    delete dataValuesLight[index]["label"];
                }
            }


            dataset.push({
                seriesname: "קטלנית",
                data: dataValuesLethal,
                color: "#d81c32"
            });
            dataset.push({
                seriesname: "קשה",
                data: dataValuesSevere,
                color: "#ff9f1c"
            });
            dataset.push({
                seriesname: "קלה",
                data: dataValuesLight,
                color: "#ffd82b"
            });
            monthCategories = _.sortBy(monthCategories, 'label');

            for (var index = 0; index < monthCategories.length; index++) {
                switch (monthCategories[index]["label"]) {
                    case "1":
                        monthCategories[index]["label"] = "קטלנית";
                        break;
                    case "2":
                        monthCategories[index]["label"] = "קשה";
                        break;
                    case "3":
                        monthCategories[index]["label"] = "קלה";
                        break;
                }
            }

            var categories = {
                category: monthCategories
            };

            if (currentDataType === "percentType") {
                FusionCharts.ready(function() {
                    var statChart = new FusionCharts({
                        "type": "stackedcolumn2d",
                        "renderAt": "myChart",
                        "width": chartWidth,
                        "height": chartHeight,
                        "dataFormat": "json",
                        "dataSource": {
                            "chart": {
                                "caption": "מספר התאונות בחודש לפי חומרה באחוזים",
                                "xAxisName": "חודשים - מקובץ מכל השנים שנבחרו",
                                "yAxisName": "מספר תאונות לפי חומרה באחוזים",
                                "theme": "fint",
                                "labelFontSize": "15",
                                "yAxisNameFontSize": "20",
                                "xAxisNameFontSize": "20",
                                "captionFontSize": "25",
                                "stack100Percent": "1",
                                "decimals": "0",
                            },
                            "categories": categories,
                            "dataset": dataset
                        }
                    });
                    statChart.render();
                });
            } else {
                FusionCharts.ready(function() {
                    var statChart = new FusionCharts({
                        "type": "stackedcolumn2d",
                        "renderAt": "myChart",
                        "width": chartWidth,
                        "height": chartHeight,
                        "dataFormat": "json",
                        "dataSource": {
                            "chart": {
                                "caption": "מספר התאונות בחודש לפי חומרה",
                                "xAxisName": "חודשים - מקובץ מכל השנים שנבחרו",
                                "yAxisName": "מספר תאונות לפי חומרה",
                                "theme": "fint",
                                "showSum": "1",
                                "labelFontSize": "15",
                                "yAxisNameFontSize": "20",
                                "xAxisNameFontSize": "20",
                                "captionFontSize": "25",
                            },
                            "categories": categories,
                            "dataset": dataset
                        }
                    });
                    statChart.render();
                });
            }

            break;
        case "ageGroup":
            var params = app.buildMarkersParams();
            params["fetch_markers"] = '';
            params["fetch_vehicles"] = '';
            params["fetch_involved"] = '1';
            $.get("charts-data", params, function(data){
                var involved = data.involved;
                var age_groups = {};
                var dataset = [];
                for (var i = 0; i < involved.length; i++) {
                    if (age_groups[involved[i].age_group]){
                        age_groups[involved[i].age_group]++;
                    }else{
                        age_groups[involved[i].age_group] = 1;
                    }
                }
                for (var key in age_groups) {
                    if (age_groups.hasOwnProperty(key)) {
                        dataset.push({ label: key, value: age_groups[key] });
                    }
                }
                FusionCharts.ready(function() {
                    var statChart = new FusionCharts({
                        "type": 'pie2d',
                        "renderAt": "myChart",
                        "width": chartWidth,
                        "height": chartHeight,
                        "dataFormat": "json",
                        "dataSource": {
                            "chart": {
                                "caption": "מספר הנפגעים לפי קבוצת גיל",
                                "theme": "fint",
                                "showPercentValues": currentDataType === "percentType" ? "1" : "0",
                                "showPercentInTooltip": currentDataType === "percentType" ? "1" : "0",
                                "decimals": "1",
                                "useDataPlotColorForLabels": "1",
                            },
                            "data": dataset
                        }
                    });
                    statChart.render();
                });
            });
            break;
        case "accidentsBySexAndAge":
            var params = app.buildMarkersParams();
            params["fetch_markers"] = '';
            params["fetch_vehicles"] = '';
            params["fetch_involved"] = '1';
            $.get("charts-data", params, function(data){
                var involved = data.involved;
                var age_groups = {};
                var dataset = [];
                var males = [];
                var females = [];
                var keys = [];
                var categories = { category: [] };
                for (var i = 0; i < involved.length; i++) {
                    if (age_groups[involved[i].age_group]){
                        if (involved[i].sex === 1){
                            if (age_groups[involved[i].age_group].male){
                                age_groups[involved[i].age_group].male++;
                            }else{
                                age_groups[involved[i].age_group].male = 1;
                            }
                        }else if (involved[i].sex === 2){
                            if (age_groups[involved[i].age_group].female){
                                age_groups[involved[i].age_group].female++;
                            }else{
                                age_groups[involved[i].age_group].female = 1;
                            }
                        }
                    }else{
                        age_groups[involved[i].age_group] = {};
                        if (involved[i].sex === 1){
                            age_groups[involved[i].age_group].male = 1;
                        }else if (involved[i].sex === 2){
                            age_groups[involved[i].age_group].female = 1;
                        }
                    }
                }
                for (var key in age_groups) {
                    if (age_groups.hasOwnProperty(key)) {
                        keys.push(key);
                    }
                }
                keys.sort();
                for (var i = 0; i < keys.length; i++) {
                    categories.category.push({ label: keys[i]});
                        if (age_groups[keys[i]].male){
                            males.push({ value: age_groups[keys[i]].male.toString() });
                        }else{
                            males.push({ value: '0' });
                        }
                        if (age_groups[keys[i]].female){
                            females.push({ value: age_groups[keys[i]].female.toString() });
                        }else{
                            females.push({ value: '0' });
                        }
                }
                dataset.push({ seriesname: 'זכר', data: males});
                dataset.push({ seriesname: 'נקבה', data: females});
                FusionCharts.ready(function() {
                    var statChart = new FusionCharts({
                        "type": 'mscolumn2d',
                        "renderAt": "myChart",
                        "width": chartWidth,
                        "height": chartHeight,
                        "dataFormat": "json",
                        "dataSource": {
                            "chart": {
                                "caption": "מספר הנפגעים לפי קבוצת גיל ומין",
                                "theme": "fint"
                            },
                            "categories": categories,
                            "dataset": dataset
                        }
                    });
                    statChart.render();
                });
            });
            break;
    }

    $("#selectTypeOfChart").on("change", function() {
        if (jsPanelInst != null) {
            currentTypeOfChart = $("#selectTypeOfChart").val();
            startJSPanelWithChart(jsPanelInst, $("#statPanel").width(), $("#statPanel").height(),
                $("#statPanel").width() - 30, $("#statPanel").height() - 80);
        }
    });

    $("#selectTypeOfData").on("change", function() {
        if (jsPanelInst != null) {
            currentDataType = $("#selectTypeOfData").val();
            startJSPanelWithChart(jsPanelInst, $("#statPanel").width(), $("#statPanel").height(),
                $("#statPanel").width() - 30, $("#statPanel").height() - 80);
        }
    });

};

function PushZeroValues(dataValuesLethal, dataValuesSevere, dataValuesLight, lastDate) {
    if (dataValuesLethal.length > 0) {
        if (dataValuesLethal[dataValuesLethal.length - 1]["label"] != lastDate) {
            dataValuesLethal.push({
                label: lastDate,
                value: 0
            });
        }
    } else {
        dataValuesLethal.push({
            label: lastDate,
            value: 0
        });
    }
    if (dataValuesSevere.length > 0) {
        if (dataValuesSevere[dataValuesSevere.length - 1]["label"] != lastDate) {
            dataValuesSevere.push({
                label: lastDate,
                value: 0
            });
        }
    } else {
        dataValuesSevere.push({
            label: lastDate,
            value: 0
        });
    }
    if (dataValuesLight.length > 0) {
        if (dataValuesLight[dataValuesLight.length - 1]["label"] != lastDate) {
            dataValuesLight.push({
                label: lastDate,
                value: 0
            });
        }
    } else {
        dataValuesLight.push({
            label: lastDate,
            value: 0
        });
    }
}

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