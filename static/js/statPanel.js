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


    var groupedAccidentsByMonth = _.countBy(app.markers.pluck("created"), function(item) {
		return item.substring(0,7);
	});

    var jsonAccidentsByMonth = _.map(groupedAccidentsByMonth, function(numOfAccidents, month) {return {"label": month, "value": numOfAccidents.toString()}});
	jsonAccidentsByMonth = _.sortBy(jsonAccidentsByMonth, 'label');

	FusionCharts.ready(function(){
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



	

	
	

	
	
	
