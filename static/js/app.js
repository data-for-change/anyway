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
        },
        initialize : function() {
            this.markers = new MarkerCollection();
            this.clusters = new ClusterCollection();
            this.model = new Backbone.Model();
            this.markerList = [];
            this.clusterList = [];
            this.firstLoadDelay = true;
            this.show_markers = '1';
            this.show_discussions = '1';
            this.accurate = '1';
            this.approx = '';
            this.show_fatal = '1';
            this.show_severe = '1';
            this.show_light = '1';
            this.show_urban = 3;
            this.show_intersection = 3;
            this.show_lane = 3;
            this.show_day = 'all';
            this.show_holiday = 0;

            this.dateRanges = [new Date($("#sdate").val()), new Date($("#edate").val())];

            setTimeout(function(){
                this.firstLoadDelay = false;
            }.bind(this), 2200);

            this.markers
                .bind("reset", this.loadMarkers, this)
                .bind("destroy", this.loadMarkers, this)
                .bind("add", this.loadMarker, this)
                .bind("change:currentModel", this.chooseMarker, this);

            this.clusters
                .bind("reset", this.loadClusters, this)
                .bind("add", this.loadCluster, this);

            this.initLayers();

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
                if (app.infoWindow || app.discussionShown) return;
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
            if (!this.firstLoadDelay){
                this.oms.unspiderfy();
                this.clearMarkersFromMap();
                this.fetchMarkers();
            }
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
                $("#view-filter").prop('disabled', false);
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
            params["start_date"] = this.dateRanges[0].getTime() / 1000;
            params["end_date"] = this.dateRanges[1].getTime() / 1000;
            params["show_fatal"] = this.show_fatal;
            params["show_severe"] = this.show_severe;
            params["show_light"] = this.show_light;
            params["approx"] = this.approx;
            params["accurate"] = this.accurate;
            params["show_markers"] = this.show_markers;
            params["show_discussions"] = this.show_discussions;
            params["show_urban"] = this.show_urban;
            params["show_intersection"] = this.show_intersection;
            params["show_lane"] = this.show_lane;
            params["show_day"] = this.show_day;
            params["show_holiday"] = this.show_holiday;
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
                    icon: app.retinaIconsResize(MULTIPLE_ICONS[SEVERITY_VARIOUS])
                });
                tourLocation = 6 ;
                console.log("inside the group id "+tourLocation+"new2");
                contentString = '<p>בנקודה זו התרחשו מספר תאונות, לחיצה על האייקון תציג אותן בנפרד ותאפשר בחירה</br> בתאונה בודדת.</p>';
                titleString = 'אייקון של מספר תאונות באותו מקום';
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
        linkMap: function () {
            $('#embed').modal('show');
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

            var mapControlDiv = document.createElement('div');
            mapControlDiv.className = "map-control";
            mapControlDiv.innerHTML = $("#map-control").html();

            var resetMapDiv = document.createElement('div');
            resetMapDiv.className = "map-button reset-map-control";
            resetMapDiv.innerHTML = $("#reset-map-control").html();
            google.maps.event.addDomListener(resetMapDiv, 'click', function () {
                this.goToMyLocation();
            }.bind(this));

            var downloadCsvDiv = document.createElement('div');
            downloadCsvDiv.className = "map-button download-csv-control";
            downloadCsvDiv.innerHTML = $("#download-csv-control").html();
            google.maps.event.addDomListener(downloadCsvDiv, 'click', function () {
                this.downloadCsv();
            }.bind(this));

            var linkMapDiv = document.createElement('div');
            linkMapDiv.className = 'map-button link-map-control';
            linkMapDiv.innerHTML = $("#link-map-control").html();
            google.maps.event.addDomListener(linkMapDiv, 'click', function () {
                var url = document.URL,
                $map_link = $("#map_link"),
                $iframe_link = $("#iframe_link"),
                $embed_link = $("#js-embed-link");
                $map_link.val(url);
                $iframe_link.html('<iframe src="' + url + '&map_only=true"></iframe>');
                $(".js-btn-copytoclipboard").on("click", function(){
                    $("#" + $(this).data("copy")).select();
                });
                this.linkMap();
            }.bind(this));

            var tourDiv = document.createElement('div');
            tourDiv.className = "map-button tour-control blink";
            tourDiv.innerHTML = $("#tour-control").html();
            google.maps.event.addDomListener(tourDiv, 'click', function () {
                tourClick();
            }.bind(this));

            mapControlDiv.appendChild(resetMapDiv);
            mapControlDiv.appendChild(downloadCsvDiv);
            mapControlDiv.appendChild(linkMapDiv);
            mapControlDiv.appendChild(tourDiv);

            var linkLabel = document.createElement('div');
            linkLabel.className = 'control-label';
            linkLabel.innerHTML = 'קישור לתצוגה נוכחית';
            linkMapDiv.appendChild(linkLabel);

            var downloadLabel = document.createElement('div');
            downloadLabel.className = 'control-label';
            downloadLabel.innerHTML = 'הורד נתוני תאונות (CSV)';
            downloadCsvDiv.appendChild(downloadLabel);

            var tourLabel = document.createElement('div');
            tourLabel.className = 'control-label';
            tourLabel.innerHTML = 'התחל הדרכה';
            tourDiv.appendChild(tourLabel);

            this.map.controls[google.maps.ControlPosition.TOP_RIGHT].push(mapControlDiv);

            if (LOCATION_SPECIFIED) {
                if (!MARKER_ID && !DISCUSSION_IDENTIFIER) {
                    this.setCenterWithMarker(this.defaultLocation);
                }
            } else {
                this.goToMyLocation();
            }
            setTimeout(function(){
                this.fetchMarkers();
            }.bind(this),2000);
            // search box:
            // Create the search box and link it to the UI element.
            var input = document.getElementById('pac-input');
            this.map.controls[google.maps.ControlPosition.TOP_RIGHT].push(input);
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
                    size: 42,
                    width: 5
                },
                {
                    size: 52,
                    width: 10
                },
                {
                    size: 62,
                    width: 15
                },
                {
                    size: 72,
                    width: 20
                }
            ];
            var mcOptions = {maxZoom: MINIMAL_ZOOM - 1, minimumClusterSize: 1, styles: clusterStyle};
            this.clusterer = new MarkerClusterer(this.map, [], mcOptions);
            console.log('Loaded MarkerClusterer');

            this.sidebar = new SidebarView({map: this.map}).render();
            this.$el.find(".sidebar-container").append(this.sidebar.$el);
            console.log('Loaded SidebarView');

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
            google.maps.event.addListener( this.map, "idle", function(){
                if (!this.firstLoadDelay){
                    this.fetchMarkers();
                }
            }.bind(this) );
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
        },
        initLayers: function (severity) {
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
            this.updateUrl(this.getDiscussionUrl(identifier));
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
                this.updateUrl(this.getDiscussionUrl(identifier));
                this.newDiscussionIdentifier = undefined;
            }
            $("#discussion-dialog").modal("show");
            this.discussionShown = identifier;
            $("#discussion-dialog").on("hidden", function() {
                this.discussionShown = null;
            }.bind(this));
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
        getDiscussionUrl: function (identifier) {
            return "/?discussion=" + identifier + "&" + app.getCurrentUrlParams();
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
              icon: this.retinaIconsResize(USER_LOCATION_ICON)
            });

             // agam add- tour find location for step 2
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
        // TODO: After the filters a re ready improve that too accordingly
            var dateRange = app.model.get("dateRange");
            var center = app.map.getCenter();
            return "start_date=" + moment(this.dateRanges[0]).format("YYYY-MM-DD") +
                "&end_date=" + moment(this.dateRanges[1]).format("YYYY-MM-DD") +
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
        },
        retinaIconsResize : function(image_url){
            if (isRetina){
                image_url = {
                    url: image_url,
                    scaledSize: new google.maps.Size(30, 50)
                };
            }
            return image_url;
        },
        load_filter: function() {
            // TODO: Change to switch which will only go through requested filters
            //TODO: Stop point 5.8 --> Fix clusters connection when filters complete
            if ($("#checkbox-discussions").is(":checked")) { this.show_discussions='1' } else { this.show_discussions='' }
            if ($("#checkbox-accidents").is(":checked")) { this.show_markers='1' } else { this.show_markers='' }
            if ($("#checkbox-accurate").is(":checked")) { this.accurate='1' } else { this.accurate='' }
            if ($("#checkbox-approx").is(":checked")) { this.approx='1' } else { this.approx='' }
            if ($("#checkbox-fatal").is(":checked")) { this.show_fatal='1' } else { this.show_fatal='' }
            if ($("#checkbox-severe").is(":checked")) { this.show_severe='1' } else { this.show_severe='' }
            if ($("#checkbox-light").is(":checked")) { this.show_light='1' } else { this.show_light='' }

            if ($("#checkbox-urban").is(":checked") && $("#checkbox-nonurban").is(":checked")) {
                this.show_urban = 3;
            } else if ($("#checkbox-urban").is(":checked")) {
                this.show_urban = 2;
            } else if ($("#checkbox-nonurban").is(":checked")) {
                this.show_urban = 1;
            } else {
                this.show_urban = 0;
            };

            if ($("#checkbox-intersection").is(":checked") && $("#checkbox-nonintersection").is(":checked")) {
                this.show_intersection = 3;
            } else if ($("#checkbox-intersection").is(":checked")) {
                this.show_intersection = 2;
            } else if ($("#checkbox-nonintersection").is(":checked")) {
                this.show_intersection = 1;
            } else {
                this.show_intersection = 0;
            };

            // This section only filters one-lane and multi-lane.
            // Accidents with 'other' setting (which are the majority) Will not be shown
            if ($("#checkbox-multi-lane").is(":checked") && $("#checkbox-one-lane").is(":checked")) {
                this.show_lane = 3;
            } else if ($("#checkbox-multi-lane").is(":checked")) {
                this.show_lane = 2;
            } else if ($("#checkbox-one-lane").is(":checked")) {
                this.show_lane = 1;
            } else {
                this.show_lane = 0;
            };




            this.dateRanges = [new Date($("#sdate").val()), new Date($("#edate").val())]
            this.resetMarkers();
            this.fetchMarkers();
            this.updateFilterString();
        },
        change_date: function() {
            // TODO 1: Change ACCYEARS to conatin the year itself and pull years here from the object
            // TODO 2: (optional): change years from radios to checkboxes and allow multiple choices forcing sequential periods
            var start_date, end_date, all_years = false;
            if ($("#checkbox-2014").is(":checked")) { start_date = "2014"; end_date = "2015" }
            else if ($("#checkbox-2013").is(":checked")) { start_date = "2013"; end_date = "2014" }
            else if ($("#checkbox-2012").is(":checked")) { start_date = "2012"; end_date = "2013" }
            else if ($("#checkbox-2011").is(":checked")) { start_date = "2011"; end_date = "2012" }
            else if ($("#checkbox-all-years").is(":checked")) { start_date = "2005"; end_date = "2025"; all_years = true }
            if (!all_years) {
                $("#sdate").val(start_date + '-01-01');
                $("#edate").val(end_date + '-01-01');
            } else {
                $("#sdate").val('');
                $("#edate").val('');
            }

            // TODO: keep building when SOF reaches an answer:

            /*
            switch ($("input[type='radio'][name='day']:checked").val()) {
                case 'A':
                    this.show_day = 'sun';
                    break;
                case 'B':
                    this.show_day = 'mon';
                    break;

                default:
                    this.show_day = 'all';

            }
            */

            switch ($("input[type='radio'][name='holiday']:checked").val()) {
                case 'all':
                    this.show_holiday = 0;
                    break;
                case 'holiday':
                    this.show_holiday = 1;
                    break;
                case 'holi-eve':
                    this.show_holiday = 2;
                    break;
                case 'holi-weekday':
                    this.show_holiday = 3;
                    break;
                case 'weekday':
                    this.show_holiday = 4;
                    break;

            }



            this.dateRanges = [new Date(start_date + '-01-01'), new Date(end_date + '-01-01')];
            this.resetMarkers();
            this.fetchMarkers();
            this.updateFilterString();
        },
        updateFilterString: function() {
            if (!this.clusterMode()) {
                var fatal = this.show_fatal, severe = this.show_severe, light = this.show_light, severityText = " בחומרה ";
                var accurate = this.accurate, approx = this.approx, accuracyText = " ובעיגון ";

                // Severity variables and strings
                if (fatal == '1') {
                    fatal = "קטלנית "
                } else {
                    fatal = ""
                }
                if (severe == '1' && fatal != '' && light == '') {
                    severe = "וקשה ";
                } else if (severe == '1') {
                    severe = "קשה ";
                } else {
                    severe = '';
                }
                ;
                if (fatal == '' && severe == '' && light == '') {
                    severityText = ""
                }

                if (light == '1' && (fatal != '' || severe != '')) {
                    light = "וקלה ";
                } else if (light == '1') {
                    light = "קלה ";
                } else {
                    light = '';
                }

                // Accuracy variables and strings
                if (accurate == '1') {
                    accurate = "מדויק "
                } else {
                    accurate = ""
                }
                if (approx == '1' && accurate != '') {
                    approx = "ומשוער ";
                } else if (approx == '1') {
                    approx = "משוער ";
                } else {
                    approx = "";
                }
                if (accurate == '' && approx == '') {
                    accuracyText = ""
                }

                $("#filter-string").text(
                    "" + "מציג " + markerCount + " תאונות בין התאריכים " + moment(this.dateRanges[0]).format('LL')
                    + " עד " + moment(this.dateRanges[1]).format('LL') + severityText + fatal + severe + light
                    + accuracyText + accurate + approx
                );
            } else {
                $("#filter-string").text(" התקרב על מנת לקבל נתוני סינון ");
            }
        }
    });
});

