$(function () {
    var AppRouter = Backbone.Router.extend({
        routes: {
            "": "navigateEmpty",
            "/?marker=:id&start_date=:start&end_date=:end&show_fatal=:showFatal&show_severe=:showSevere&show_light=:showLight&show_inaccurate=:showInaccurate&zoom=:zoom&lat=:lat&lon=:lon": "navigate"
        },
        navigate: function (id, start, end, showFatal, showSevere, showLight, showInaccurate, zoom, lat, lon) {
            app.model.set("currentMarker", parseInt(id));
            app.model.set("dateRange", [new Date(start), new Date(end)]);
            app.model.set("showFatal", showFatal);
            app.model.set("showSevere", showSevere);
            app.model.set("showLight", showLight);
            app.model.set("showInaccurateMarkers", showInaccurate);
            app.map.setZoom(parseInt(zoom));
            app.map.setCenter(new google.maps.LatLng(lat, lon));
        },
        navigateEmpty: function () {
            app.model.set("currentMarker", null);
        }
    });

    var Discussion = Backbone.Model.extend({});

    window.MarkerCollection = Backbone.Collection.extend({
        url: "/markers",

        parse: function (response, options) {
            return response.markers;
        }
    });

    window.ClusterCollection = Backbone.Collection.extend({
        url: "/clusters",

        parse: function (response, options) {
            return response.clusters;
        }
    });

    window.AppView = Backbone.View.extend({
        el : $("#app"),
        events : {
            "click .download-csv" : "downloadCsv"
        },
        initialize : function() {
            this.markers = new MarkerCollection();
            this.clusters = new ClusterCollection();
            this.model = new Backbone.Model();
            this.markerList = [];
            this.clusterList = [];

            this.markers
                .bind("reset", this.loadMarkers, this)
                .bind("destroy", this.loadMarkers, this)
                .bind("add", this.loadMarker, this)
                .bind("change:currentModel", this.chooseMarker, this);

            this.clusters
                .bind("reset", this.loadClusters, this)
                .bind("add", this.loadCluster, this);

            this.initLayers();
            this.initShowInaccurate();

            this.model
                .bind("change:user", this.updateUser, this)
                .bind("change:showFatal",
                _.bind(this.reloadMarkersIfNeeded, this, "showFatal"))
                .bind("change:showSevere",
                _.bind(this.reloadMarkersIfNeeded, this, "showSevere"))
                .bind("change:showLight",
                _.bind(this.reloadMarkersIfNeeded, this, "showLight"))
                .bind("change:showInaccurateMarkers",
                _.bind(this.reloadMarkersIfNeeded, this, "showInaccurateMarkers"))
                .bind("change:dateRange", this.reloadMarkers, this);
        },
        reloadMarkersIfNeeded: function(attr) {
            if (this.clusterMode() || this.model.get(attr)) {
                this.reloadMarkers();
            } else {
                this.updateUrl();
                this.loadMarkers();
            }
        },
        updateUrl: function (url) {
            if (typeof url == 'undefined') {
                if (app.infoWindow) return;
                url = "/?" + this.getCurrentUrlParams();
            }
            Backbone.history.navigate(url, true);
        },
        clusterMode: function () {
            return this.map.zoom < MINIMAL_ZOOM;
        },
        zoomChanged: function () {
            this.resetOnMouseUp = true;
            var reset = this.previousZoom < MINIMAL_ZOOM;
            this.fetchData(reset);
            this.previousZoom = this.map.zoom;
        },
        reloadMarkers: function () {
            this.oms.unspiderfy();
            this.clearMarkersFromMap();
            this.fetchMarkers();
        },
        fetchMarkers: function (reset) {
            if (!this.isReady) return;

            var params = this.buildMarkersParams();
            if (!params) return;

            var reset = this.clusterMode() || this.previousZoom < MINIMAL_ZOOM;
            this.previousZoom = this.map.zoom;
            if (reset) {
                this.resetMarkers();
            }

            if (this.clusterMode()) {
                this.closeInfoWindow();
                this.clusters.fetch({
                    data: $.param(params),
                    reset: reset,
                    success: this.reloadSidebar.bind(this)
                });
            } else {
                if (!this.markerList.length) {
                    this.loadMarkers();
                }

                this.clearClustersFromMap();

                this.markers.fetch({
                    data: $.param(params),
                    reset: reset,
                    success: this.reloadSidebar.bind(this)
                });
            }
        },
        fetchData: function (reset) {
            if (!this.isReady) return;
            this.updateUrl();
            var params = this.buildMarkersParams();

            reset = this.clusterMode() || (typeof reset !== 'undefined' && reset);
            reset &= this.resetOnMouseUp;
            google.maps.event.clearListeners(this.map, "mousemove");
            this.resetOnMouseUp = false;
            if (reset) {
                this.resetMarkers();
            }

            if (this.clusterMode()) {

                this.clusters.fetch({
                    data: $.param(params),
                    reset: reset,
                    success: this.reloadSidebar.bind(this)
                });

            } else {
                if (!this.markerList.length) {
                    this.loadMarkers();
                }

                this.clearClustersFromMap();

                this.markers.fetch({
                    data: $.param(params),
                    reset: reset,
                    success: this.reloadSidebar.bind(this)
                });
            }
        },
        reloadSidebar: function () {
            if (this.clusterMode()) {
                this.sidebar.showClusterMessage();
            } else { // close enough
                this.setMultipleMarkersIcon();
                this.sidebar.reloadMarkerList(this.markerList);
            }
            this.chooseMarker();
        },
        buildMarkersParams: function () {
            var bounds = this.map.getBounds();
            if (!bounds) return null;
            var zoom = this.map.zoom;
            var dateRange = this.model.get("dateRange");

            var params = {};
            params["ne_lat"] = bounds.getNorthEast().lat();
            params["ne_lng"] = bounds.getNorthEast().lng();
            params["sw_lat"] = bounds.getSouthWest().lat();
            params["sw_lng"] = bounds.getSouthWest().lng();
            params["zoom"] = zoom;
            params["thin_markers"] = (zoom < MINIMAL_ZOOM || !bounds);
            // Pass start and end dates as unix time (in seconds)
            params["start_date"] = dateRange[0].getTime() / 1000;
            params["end_date"] = dateRange[1].getTime() / 1000;
            params["show_fatal"] = this.model.get("showFatal");
            params["show_severe"] = this.model.get("showSevere");
            params["show_light"] = this.model.get("showLight");
            params["show_inaccurate"] = this.model.get("showInaccurateMarkers");
            return params;
        },
        setMultipleMarkersIcon: function () {
            var groupID = 1;
            var groupsData = [];

            _.each(this.oms.markersNearAnyOtherMarker(), function (marker) {
                marker.view.model.unset("groupID");
            });

            _.each(this.oms.markersNearAnyOtherMarker(), function (marker) {
                marker.title = 'מספר תאונות בנקודה זו';
                var groupHead = marker.view.model;
                if (!groupHead.get("groupID")) {
                    groupHead.set("groupID", groupID);
                    var groupHeadSeverity = groupHead.get('severity');
                    var groupsHeadOpacity = groupHead.get("locationAccuracy") == 1 ? 'opaque' : 1;
                    groupsData.push({severity: groupHeadSeverity, opacity: groupsHeadOpacity});

                    _.each(this.oms.markersNearMarker(marker), function (markerNear) {
                        var markerNearModel = markerNear.view.model;
                        markerNearModel.set("groupID", groupID);
                        if ((groupHeadSeverity != markerNearModel.get('severity'))) {
                            groupsData[groupsData.length - 1].severity = SEVERITY_VARIOUS;
                        }
                        if (groupsData[groupsData.length - 1].opacity != 'opaque') {
                            if (markerNearModel.get("locationAccuracy") == 1) {
                                groupsData[groupsData.length - 1].opacity = 'opaque';
                            } else {
                                groupsData[groupsData.length - 1].opacity++;
                            }
                        }
                    });
                    groupID++;

                }

            },this);
            this.groupsData = groupsData;
              // agam
            if(tourLocation == 5) {
               var myLatlng = new google.maps.LatLng(32.09170,34.86435);
               var location1 = new google.maps.Marker({
              position: myLatlng,
              map: this.map,
              icon: MULTIPLE_ICONS[SEVERITY_VARIOUS]
            });
                tourLocation = 6 ;
                console.log("inside the group id "+tourLocation+"new2");
                contentString = '<p>בנקודה זו התרחשו מספר תאונות, לחיצה על האייקון תציג אותן בנפרד ותאפשר בחירה</br> בתאונה בודדת.</p>';
                titleString = 'אייקון של מספר התאונות באותו מקום';
                defInfoWindows();
                infowindow = new google.maps.InfoWindow({
                    content: htmlTourString,
                    maxWidth: 350
                });
                infowindow.open(this.map, location1);
                tourStyle(infowindow);
            }

            _.each(this.oms.markersNearAnyOtherMarker(), function(marker){
                if (!marker.view.model.get("currentlySpiderfied")){
                    marker.view.opacitySeverityForGroup();
                }
            });

        },
        downloadCsv: function () {
            if (this.markers.length > 0) {
                params = this.buildMarkersParams();
                params["format"] = "csv";

                window.location = this.markers.url + "?" + $.param(params);
            } else {
                $('#empty-csv-dialog').modal('show');
            }
        },
        render: function () {
            this.isReady = false;

            this.defaultLocation = new google.maps.LatLng(INIT_LAT, INIT_LON);

            var mapOptions = {
                center: this.defaultLocation,
                zoom: INIT_ZOOM,
                mapTypeId: google.maps.MapTypeId.ROADMAP,
                mapTypeControl: false,
                zoomControl: !MAP_ONLY,
                panControl: !MAP_ONLY,
                streetViewControl: !MAP_ONLY,
                styles: MAP_STYLE
            };
            this.map = new google.maps.Map(this.$el.find("#map_canvas").get(0), mapOptions);

            var resetMapDiv = document.createElement('div');
            resetMapDiv.innerHTML = $("#reset-map-control").html();
            google.maps.event.addDomListener(resetMapDiv, 'click', function () {
                this.goToMyLocation();
            }.bind(this));
            this.map.controls[google.maps.ControlPosition.TOP_RIGHT].push(resetMapDiv);

            if (LOCATION_SPECIFIED) {
                if (!MARKER_ID) {
                    this.setCenterWithMarker(this.defaultLocation);
                }
            } else {
                this.goToMyLocation();
            }
            // search box:
            // Create the search box and link it to the UI element.
            var input = document.getElementById('pac-input');
            this.map.controls[google.maps.ControlPosition.TOP_LEFT].push(input);
            this.searchBox = new google.maps.places.SearchBox(input);

            google.maps.event.addListener(this.searchBox, 'places_changed', function () {
                this.handleSearchBox();
            }.bind(this));

            this.oms = new OverlappingMarkerSpiderfier(this.map, {
                markersWontMove: true,
                markersWontHide: true,
                keepSpiderfied: true
            });
            this.oms.addListener("click", function (marker, event) {
                marker.view.clickMarker();
                this.clickedMarker = true;
            }.bind(this));
            this.oms.addListener("spiderfy", function (markers) {
                this.closeInfoWindow();
                _.each(markers, function (marker) {
                    marker.title = marker.view.getTitle();
                    marker.view.resetOpacitySeverity();
                    marker.view.model.set("currentlySpiderfied", true);
                });
                this.clickedMarker = true;
            }.bind(this));
            this.oms.addListener("unspiderfy", function(markers){
                _.each(markers, function(marker){
                    marker.view.model.unset("currentlySpiderfied");
                });
            }.bind(this));
            this.oms.addListener("unspiderfy", this.setMultipleMarkersIcon.bind(this));
            console.log('Loaded OverlappingMarkerSpiderfier');
            var clusterStyle = [
                {
                    textColor: 'black',
                    url: '/static/img/icons/cluster_1.png',
                    height: 42,
                    width: 42
                },
                {
                    textColor: 'black',
                    url: '/static/img/icons/cluster_2.png',
                    height: 52,
                    width: 52
                },
                {
                    textColor: 'black',
                    url: '/static/img/icons/cluster_3.png',
                    height: 62,
                    width: 62
                },
                {
                    textColor: 'black',
                    url: '/static/img/icons/cluster_4.png',
                    height: 72,
                    width: 72
                }
            ];
            var mcOptions = {maxZoom: MINIMAL_ZOOM - 1, minimumClusterSize: 1, styles: clusterStyle};
            this.clusterer = new MarkerClusterer(this.map, [], mcOptions);
            console.log('Loaded MarkerClusterer');

            this.sidebar = new SidebarView({map: this.map}).render();
            this.$el.find(".sidebar-container").append(this.sidebar.$el);
            console.log('Loaded SidebarView');

            if (!START_DATE) {
                START_DATE = '01/01/2013';
            }
            if (!END_DATE) {
                END_DATE = '01/01/2014';
            }
            this.$el.find("input.date-range").daterangepicker({
                    /*
                         These ranges are irrelevant as long as no recent data is loaded:
                         'היום': ['today', 'today'],
                         'אתמול': ['yesterday', 'yesterday'],
                         'שבוע אחרון': [Date.today().add({ days: -6 }), 'today'],
                         'חודש אחרון': [Date.today().add({ days: -29 }), 'today'],
                         'החודש הזה': [Date.today().moveToFirstDayOfMonth(), Date.today().moveToLastDayOfMonth()],
                         'החודש שעבר': [Date.today().moveToFirstDayOfMonth().add({ months: -1 }), Date.today().moveToFirstDayOfMonth().add({ days: -1 })]
                    */
                    ranges: ACCYEARS,
                    opens: 'left',
                    format: 'dd/MM/yyyy',
                    separator: ' עד ',
                    startDate: START_DATE,
                    endDate: END_DATE,
                    minDate: '01/01/2005',
                    maxDate: '31/12/2023',
                    locale: {
                        applyLabel: 'בחר',
                        fromLabel: 'מ',
                        toLabel: 'עד',
                        customRangeLabel: 'בחר תאריך',
                        daysOfWeek: ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'],
                        monthNames: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
                        firstDay: 1
                    },
                    showWeekNumbers: true,
                    buttonClasses: ['btn-danger']
                },
                function (start, end) {
                    var daterangepicker = this.$el.find("input.date-range").data("daterangepicker");
                    if (!start)
                        start = daterangepicker.minDate;
                    if (!end)
                        end = daterangepicker.maxDate;
                    this.model.set("dateRange", [start, end]);
                }.bind(this)
            );
            this.$el.find("#calendar-control").click( // only applies to <i>
                function () {
                    this.$el.find("input.date-range").data('daterangepicker').show();
                }.bind(this)
            );
            this.$el.find("input.date-range").data("daterangepicker").notify();
            console.log('Loaded daterangepicker');

            $(document).ajaxStart(function () {
                this.spinner = $('<li/>');
                this.spinner.height('20px');
                this.sidebar.$currentViewList.prepend(this.spinner);
                this.spinner.spin();
            }.bind(this));
            $(document).ajaxStop(function () {
                if (this.spinner) {
                    this.spinner.spin(false);
                }
            }.bind(this));
            console.log('Loaded spinner');

            this.previousZoom = this.map.zoom;

            this.router = new AppRouter();
            Backbone.history.start({pushState: true});
            console.log('Loaded AppRouter');

            this.isReady = true;
            google.maps.event.addListener( this.map, "rightclick", _.bind(this.contextMenuMap, this) );
            google.maps.event.addListener( this.map, "idle", _.bind(this.fetchMarkers, this) );
            google.maps.event.addListener( this.map, "click", _.bind(this.clickMap, this) );

            return this;
        },
        goToMyLocation: function () {
            if (typeof this.myLocation !== 'undefined') {
                this.setCenterWithMarker(this.myLocation);
            } else if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(function (position) {
                    var latitude = position.coords.latitude;
                    var longitude = position.coords.longitude;
                    this.myLocation = new google.maps.LatLng(latitude, longitude);
                    this.setCenterWithMarker(this.myLocation);
                    this.createHighlightPoint(latitude, longitude, HIGHLIGHT_TYPE_USER_GPS);
                }.bind(this));
            } else {
                this.myLocation = this.defaultLocation;
                this.setCenterWithMarker(this.myLocation);
            }
            this.map.setZoom(INIT_ZOOM);
        },
        closeInfoWindow: function () {
            if (app.infoWindow) {
                this.selectedMarker.unhighlight();
                this.selectedMarker = null;
                app.infoWindow.close();
                app.infoWindow = null;
                this.updateUrl();
                $(document).off('keydown',app.ESCinfoWindow);
            }
        },
        clickMap: function (e) {
            this.closeInfoWindow();
        },
        trackDrag: function () {
            google.maps.event.addListener(this.map, "mousemove", function () {
                this.resetOnMouseUp = true;
            });
        }, initShowInaccurate: function () {
            var showInaccurate = this.model.get("showInaccurateMarkers");
            if (typeof showInaccurate == 'undefined') {
                this.model.set("showInaccurateMarkers", SHOW_INACCURATE ? 1 : 0);
                showInaccurate = SHOW_INACCURATE;
            }
            return showInaccurate;
        }, initLayers: function (severity) {
            var severities = [SEVERITY_FATAL, SEVERITY_SEVERE, SEVERITY_LIGHT];
            var self = this;
            severities.forEach(function (severity) {
                var attr = SEVERITY_ATTRIBUTES[severity];
                var layer = self.model.get(attr);
                if (!layer) {
                    self.model.set(attr, LAYERS[severity]);
                    layer = LAYERS[severity];
                }
            });
        },
        loadMarker: function (model) {
            for (var i = 0; i < this.markerList.length; i++) {
                if (this.markerList[i].model.get("type") == model.get("type") &&
                    this.markerList[i].model.attributes.id == model.attributes.id) {
                    return; // avoid adding duplicates
                }
            }

            // markers are loaded immediately as they are fetched
            if (this.clusterMode() || this.fitsFilters(model) ||
                !this.clusterMode() && model.get("type") == MARKER_TYPE_DISCUSSION) {
                var markerView = new MarkerView({model: model, map: this.map}).render();
                model.set("markerView", this.markerList.length);
                this.markerList.push(markerView);
            }
        },
        loadCluster: function (model) {
            var clusterExists = _.any(this.clusterList, function (cluster) {
                return cluster.model.attributes.longitude === model.attributes.longitude
                    && cluster.model.attributes.latitude === model.attributes.latitude;
            });
            if (!clusterExists) {
                var clusterView = new ClusterView({model: model, map: this.map}).render();
                this.clusterList.push(clusterView);
            }
        },
        loadClusters: function (model) {
            this.oms.unspiderfy();
            this.clearClustersFromMap();
            this.clusters.each(_.bind(this.loadCluster, this));
        },
        fitsFilters: function (model) {
            var layer = this.model.get(SEVERITY_ATTRIBUTES[model.get("severity")]);
            if (!layer) {
                return false;
            }

            if (this.model.get("dateRange")) {
                var createdDate = new Date(model.get("created"));

                var start = this.model.get("dateRange")[0];
                var end = this.model.get("dateRange")[1];

                if (createdDate < start || createdDate > end) {
                    return false;
                }
            }

            var showInaccurate = this.initShowInaccurate();
            if (!showInaccurate && model.get("locationAccuracy") != 1) {
                return false;
            }

            return true;
        },
        loadMarkers: function () {
            this.oms.unspiderfy();
            this.clearMarkersFromMap();
            this.clearClustersFromMap();
            this.markers.each(_.bind(this.loadMarker, this));
        },
        clearMarkersFromMap: function () {
            if (this.markerList) {
                _(this.markerList).each(_.bind(function (marker) {
                    marker.marker.setMap(null);
                }, this));
            }
            this.markerList = [];
            this.clusterer.clearMarkersFromMap();
            this.clearClustersFromMap();
        },
        clearClustersFromMap: function () {
            this.clusterer.removeClusters();
            this.clusterList = [];
        },
        resetMarkers: function () {
            this.clearMarkersFromMap();
            this.markers.reset();
        },
        resetClusters: function () {
            this.clearClustersFromMap();
            this.clusters.reset();
        },
        chooseMarker: function () {
            if (!this.markerList.length) {
                return;
            }

            var currentMarker = this.model.get("currentMarker");
            if (!this.markers.get(currentMarker)) {
                this.updateUrl();
                return;
            }
            var markerView = this.markerList[this.markers.get(currentMarker).get("markerView")];
            if (!markerView) {
                // this.model.set("currentMarker", null);
                return;
            }

            markerView.choose();
            this.model.set("currentMarker", null);
        },
        contextMenuMap : function(e) {
            this.clickLocation = e.latLng;
            if (this.menu) {
                this.menu.remove();
            }
            this.menu = new ContextMenuView({
                items: [
                    {
                        icon : "plus-sign",
                        text : ADD_DISCUSSION,
                        callback : _.bind(this.showDiscussion, this)
                    },
                    {
                        icon : "plus-sign",
                        text : NEW_FEATURES,
                        callback : _.bind(this.featuresSubscriptionDialog, this)
                    }
                ]}).render(e);
        },
        addDiscussionMarker : function() { // called once a comment is posted
            var identifier = this.newDiscussionIdentifier;
            if (typeof identifier == 'undefined') return true; // marker already exists
            var model = new Discussion({
                identifier: identifier,
                latitude: this.clickLocation.lat(),
                longitude: this.clickLocation.lng(),
                type: MARKER_TYPE_DISCUSSION
            });
            var view = new MarkerView({model: model, map: this.map}).render();
            $.post("discussion", JSON.stringify({
                    "latitude"  : model.get("latitude"),
                    "longitude" : model.get("longitude"),
                    "identifier": identifier,
                    "title"     : identifier
                }));
            return true;
        },
        showDiscussion : function(identifier) { // called when clicking add, or on marker
            if (typeof identifier == 'undefined') { // new discussion from context menu
                identifier = this.clickLocation.toString(); // (lat, lon)
                this.newDiscussionIdentifier = identifier;
            } else { // clicked existing discussion marker
                this.newDiscussionIdentifier = undefined;
            }
            $("#discussion-dialog").modal("show");
            var url = window.location.protocol + "//" + window.location.host +
                      "/discussion?identifier=" + identifier;
            DISQUS.reset({
                reload: true,
                config: function () {
                    this.page.identifier = identifier;
                    this.page.url = url;
                    this.page.title = identifier;
                }
            });
        },
        featuresSubscriptionDialog : function(type, event) {
            if (this.createDialog) this.createDialog.close();
            this.createDialog = new FeatureDialog({
                type: type,
                event: event,
                markers: this.markers
            }).render();
        },
        handleSearchBox: function () {
            var places = this.searchBox.getPlaces();
            if (places && places.length > 0) {
              var place = places[0];
              this.createHighlightPoint(place.geometry.location.lat(), place.geometry.location.lng(), HIGHLIGHT_TYPE_USER_SEARCH);
              this.setCenterWithMarker(place.geometry.location);
              this.map.setZoom(INIT_ZOOM);
            }
         },
        createHighlightPoint : function(lat, lng, highlightPointType) {
            if (isNaN(lat) || isNaN(lng) || isNaN(highlightPointType)) return;
            $.post("highlightpoints", JSON.stringify({
                    "latitude": lat,
                    "longitude": lng,
                    "type": highlightPointType
                }));
        },
        setCenterWithMarker: function(loc) {
            this.closeInfoWindow();
            this.map.setCenter(loc);
            this.fetchMarkers();
            if (this.locationMarker) {
                this.locationMarker.setMap(null);
            }
            this.locationMarker = new google.maps.Marker({
              position: loc,
              map: this.map,
              icon: USER_LOCATION_ICON
            });
             //agam add- tour find location for step 2
            if (tourLocation == 2)
            {
                tourLocation = 3;
                var location = this.locationMarker;
                contentString = '<p>המיקום שחיפשתם יסומן באיקון הזה. </br> מסביבו תוכלו לראות אייקונים שמייצגים תאונות עם נפגעים.  </p>';
                titleString = ' המיקום שחיפשתם ';
                defInfoWindows();
                infowindow = new google.maps.InfoWindow({
                    content: htmlTourString,
                    maxWidth: 350
                });
                infowindow.open(this.map, location);
                tourStyle(infowindow);
            }
          },
          getCurrentUrlParams: function () {
            var dateRange = app.model.get("dateRange");
            var center = app.map.getCenter();
            return "start_date=" + moment(dateRange[0]).format("YYYY-MM-DD") +
                "&end_date=" + moment(dateRange[1]).format("YYYY-MM-DD") +
                "&show_fatal=" + (parseInt(app.model.get("showFatal")) || 0) +
                "&show_severe=" + (parseInt(app.model.get("showSevere")) || 0) +
                "&show_light=" + (parseInt(app.model.get("showLight")) || 0) +
                "&show_inaccurate=" + (parseInt(app.model.get("showInaccurateMarkers")) || 0) +
                "&zoom=" + app.map.zoom + "&lat=" + center.lat() + "&lon=" + center.lng();
		},
        ESCinfoWindow: function(event) {
            if (event.keyCode == 27) {
                app.closeInfoWindow();
                console.log('ESC pressed');
            }
        }
    });
});


