var jsPanelInst;

function statPanelClick(widthOfPanel, heightOfPanel, chartWidth, chartHeight) {
 	jQuery.jsPanel({
 	rtl: {
 	rtl: true,
 	lang: 'he'
 	},
 	size: { width: widthOfPanel, height: heightOfPanel },
 	title: 'קצת גרפים',
 	position: 'center',
    id: 'statPanel',
	theme: 'light',
	//callback: startJSPanelWithChart(jsPanel, widthOfPanel, heightOfPanel, chartWidth, chartHeight)
	callback: function (jsPanel) {
		jsPanelInst = jsPanel;
		startJSPanelWithChart( jsPanel, widthOfPanel, heightOfPanel, chartWidth, chartHeight );
		}
	});
};

var startJSPanelWithChart = function( jsPanel, widthOfPanel, heightOfPanel, chartWidth, chartHeight ){
	var str = '<div id="myChart" width="';
	str+= chartWidth.toString();
	str+= '" height="';
	str+= chartHeight.toString();
	str+= '"></div>';
	jsPanel.content.empty();
	jsPanel.content.append(str);
	//jsPanel.content.append('<canvas id="myChart" width=chartWidth height=chartHeight></canvas>')


    var groupedByMonth = _.countBy(app.markers.pluck("created"), function(item) {
		return item.substring(0,7);
	});

    var jsonMonth = _.map(groupedByMonth, function(group, key) {return {"label": key, "value": group.toString()}});

	FusionCharts.ready(function(){
      var revenueChart = new FusionCharts({
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
              "theme": "fint"
           },
          "data": jsonMonth
       	 }
		});

		revenueChart.render();
	});


	//var ctx = $("#myChart").get(0).getContext("2d");
	//var myNewChart = new Chart(ctx);

	//var monthSorted = Object.keys(groupedByMonth).sort();
	//var numberOfMonths = Object.keys(groupedByMonth).length;
	//var numberOfAccidentsPerMonth = [];
	//for (i = 0; i <= numberOfMonths-1; i++) {
	//	numberOfAccidentsPerMonth.push(groupedByMonth[Object.keys(groupedByMonth)[i]].length);
	//}
    //
	//var data = {
	//	labels: monthSorted,
	//	datasets: [
	//		{
	//			label: "Number of accidents",
	//			labelColor : 'black',
     //           labelFontSize : '16',
	//			fillColor: "rgba(220,220,220,0.2)",
	//			strokeColor: "rgba(220,220,220,1)",
	//			pointColor: "rgba(220,220,220,1)",
	//			pointStrokeColor: "#fff",
	//			pointHighlightFill: "#fff",
	//			pointHighlightStroke: "rgba(220,220,220,1)",
	//			data: numberOfAccidentsPerMonth
	//		}//,
	//		//{
	//		//	label: "My Second dataset",
	//		//	fillColor: "rgba(151,187,205,0.2)",
	//		//	strokeColor: "rgba(151,187,205,1)",
	//		//	pointColor: "rgba(151,187,205,1)",
	//		//	pointStrokeColor: "#fff",
	//		//	pointHighlightFill: "#fff",
	//		//	pointHighlightStroke: "rgba(151,187,205,1)",
	//		//	data: app.markers.pluck("weather")
	//		//}
	//	]
	//};
    //
	//var myLineChart = new Chart(ctx).Line(data);
	};

$('body').on( "jspanelloaded", function( event, id ){
    event.preventDefault();
	$('body').on( "jspanelstatechange", function( event, id ){
		if( id === "statPanel" ) {
			if (jsPanelInst!=null) {
				startJSPanelWithChart(jsPanelInst, $("#statPanel").width(), $("#statPanel").height(),
					$("#statPanel").width() - 30, $("#statPanel").height() - 50);
			}
		}
	});
});

$("body").on( "jspanelclosed", function closeHandler(event, id) {
    if( id === "statPanel" ) {
        jsPanelInst = null;
        // close handlers attached to body should be removed again
        //$("body").off("jspanelclosed", closeHandler);
    }
});



	

	
	

	
	
	
