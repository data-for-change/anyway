$(function () {
    var AppRouter = Backbone.Router.extend({
        routes: {
            "": "navigateEmpty",
            "/?marker=:id&start_date=:start&end_date=:end&show_fatal=:showFatal&show_severe=:showSevere&show_light=:showLight&show_inaccurate=:showInaccurate&zoom=:zoom&lat=:lat&lon=:lon": "navigate"
        },
        //removed navigate function because we don't use backbone navigation for now
        //navigate: function (id, start, end, showFatal, showSevere, showLight, showInaccurate, zoom, lat, lon) {
        //    app.model.set("currentMarker", parseInt(id));
        //    app.model.set("dateRange", [new Date(start), new Date(end)]);
        //    app.model.set("showFatal", showFatal);
        //    app.model.set("showSevere", showSevere);
        //    app.model.set("showLight", showLight);
        //    app.model.set("showInaccurateMarkers", showInaccurate);
        //    app.map.setZoom(parseInt(zoom));
        //    app.map.setCenter(new google.maps.LatLng(lat, lon));
        //},
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
            this.markerIconType = true;
            this.markerList = [];
            this.clusterList = [];
            this.firstLoadDelay = true;
            this.show_markers = '1';
            this.show_discussions = '1';
            this.accurate = '1';
            this.approx = '1';
            this.show_fatal = '1';
            this.show_severe = '1';
            this.show_light = '1';
            this.show_urban = 3;
            this.show_intersection = 3;
            this.show_lane = 3;
            this.show_day = 7;
            this.show_holiday = 0;
            this.show_time = 24;
            this.start_time = 25;
            this.end_time = 25;
            this.weather = 0;
            this.road = 0;
            this.separation = 0;
            this.surface = 0;
            this.acctype = 0;
            this.controlmeasure = 0;
            this.district = 0;
            this.case_type = 0;

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
                //url = "/?" + this.getCurrentUrlParams();
                url = "";
            }else{
                var questionMarkPlace = url.indexOf('?');
                if (questionMarkPlace != -1) {
                    url = url.substring(0, questionMarkPlace);
                }
                var facebookCallbackPattern = url.indexOf('_=_');
                if (facebookCallbackPattern != -1) {
                    url = url.substring(0, facebookCallbackPattern);
                }
                var googleCallbackPattern = url.indexOf('#');
                if (googleCallbackPattern != -1) {
                    url = url.substring(0, googleCallbackPattern);
                }
            }
           Backbone.history.navigate(Backbone.history.fragment, false);
           // Backbone.history.navigate(url, true);
           window.history.pushState('','','/')
        },
        clusterMode: function () {
            return this.map.zoom < MINIMAL_ZOOM;
        },
        zoomChanged: function () {
            this.resetOnMouseUp = true;
            this.fetchMarkers();
        },
        reloadMarkers: function () {
            if (!this.firstLoadDelay){
                this.oms.unspiderfy();
                this.clearMarkersFromMap();
                this.fetchMarkers();
            }
        },
        fetchMarkers: function () {
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
                this.clearClustersFromMap();
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
        reloadSidebar: function () {
            if (this.clusterMode()) {
                this.sidebar.emptyMarkerList();
            } else { // close enough
                this.setMultipleMarkersIcon();
                this.sidebar.reloadMarkerList(this.markerList);
            }
            if (jsPanelInst!=null){
                startJSPanelWithChart(jsPanelInst, $("#statPanel").width(), $("#statPanel").height(),
					$("#statPanel").width() - 30, $("#statPanel").height() - 80);
            }
            this.updateFilterString();
            this.chooseMarker();
            if(this.iconTypeChanged == true){
                this.$el.find(".current-view").toggleClass("sidebar-pin");
                this.$el.find(".current-view").toggleClass("sidebar-dot");
                this.iconTypeChanged = false;
            }

        },
        buildMarkersParams: function (isForUrl) {
            var bounds = this.map.getBounds();
            if (!bounds) return null;
            var zoom = this.map.zoom;
            var dateRange = this.model.get("dateRange");

            var params = {};
            if (typeof isForUrl === 'undefined') {
                params["ne_lat"] = bounds.getNorthEast().lat();
                params["ne_lng"] = bounds.getNorthEast().lng();
                params["sw_lat"] = bounds.getSouthWest().lat();
                params["sw_lng"] = bounds.getSouthWest().lng();
                params["zoom"] = zoom;
                params["thin_markers"] = (zoom < MINIMAL_ZOOM || !bounds);
                // Pass start and end dates as unix time (in seconds)
                params["start_date"] = this.dateRanges[0].getTime() / 1000;
                params["end_date"] = this.dateRanges[1].getTime() / 1000;
            }else{
                var center = app.map.getCenter();
                params["zoom"] = zoom;
                params["start_date"] = moment(this.dateRanges[0]).format("YYYY-MM-DD");
                params["end_date"] = moment(this.dateRanges[1]).format("YYYY-MM-DD");
                params["lat"] = center.lat();
                params["lon"] = center.lng();
            }
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
            params["show_time"] = this.show_time;
            params["start_time"] = this.start_time;
            params["end_time"] = this.end_time;
            params["weather"] = this.weather;
            params["road"] = this.road;
            params["separation"] = this.separation;
            params["surface"] = this.surface;
            params["acctype"] = this.acctype;
            params["controlmeasure"] = this.controlmeasure;
            params["district"] = this.district;
            params["case_type"] = this.case_type;
            return params;
        },
        setMultipleMarkersIcon: function () {
            var groupID = 1;
            var groupsData = [];

            _.each(this.oms.markersNearAnyOtherMarker(), function (marker) {
                marker.view.model.unset("groupID");
            });

            //make single icons for those who are no longer in a group
            _.each(this.markerList, function(markerView){
                var marker = markerView.marker;
                if(this.map.getBounds().contains(marker.getPosition())){
                    if(!this.oms.markersNearMarker(marker,true).length){
                        marker.setTitle(markerView.getTitle("single"));
                    }
                }
            },this);

            //goes over all overlapping markers
            _.each(this.oms.markersNearAnyOtherMarker(), function (marker) {
                var firstMember = marker.view.model;
                var firstMemberGroupId = firstMember.get("groupID");
                var firstMemberIndex = firstMemberGroupId -1;
                if (!firstMemberGroupId) {
                    firstMemberGroupId = groupID;
                    firstMemberIndex = firstMemberGroupId -1;
                    firstMember.set("groupID", firstMemberGroupId);
                    var groupSeverity = firstMember.get('severity');
                    var firstMemberOpacity = firstMember.get("locationAccuracy") == 1 ? 'opaque' : 1;
                    groupsData.push({severity: groupSeverity, opacity: firstMemberOpacity, quantity: 1});

                    //goes over all markers which overlapping 'firstMember', and get the 'max' severity
                    _.each(this.oms.markersNearMarker(marker), function (markerNear) {
                        var markerNearModel = markerNear.view.model;
                        markerNearModel.set("groupID", firstMemberGroupId);
                        var currentMarkerNearSeverity = markerNearModel.get('severity');
                        // severity is an enum, when it's lower then it's more severe
                        if (currentMarkerNearSeverity < groupSeverity) {
                            groupsData[firstMemberIndex].severity = currentMarkerNearSeverity;
                            groupSeverity = currentMarkerNearSeverity;
                        }
                        if (groupsData[firstMemberIndex].opacity != 'opaque') {
                            if (markerNearModel.get("locationAccuracy") == 1) {
                                groupsData[firstMemberIndex].opacity = 'opaque';
                            } else {
                                groupsData[firstMemberIndex].opacity++;
                            }
                        }
                        groupsData[firstMemberIndex].quantity++;
                    });
                    groupID++;
                }
                if(marker.view.model.get("currentlySpiderfied")){
                    marker.setTitle(marker.view.getTitle("single"));
                }else{
                    groupMarkersCount = groupsData[firstMemberIndex].quantity;
                    groupSeverityString = SEVERITY_MAP[groupsData[firstMemberIndex].severity];
                    marker.setTitle( groupMarkersCount + " " + marker.view.getTitle("multiple") + " חומרה מירבית: " + groupSeverityString);
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
        fullScreen: function () {
            var body = document.body;

            if (
                document.fullscreenElement ||
                document.webkitFullscreenElement ||
                document.mozFullScreenElement ||
                document.msFullscreenElement){
                if (document.exitFullscreen) {
                    document.exitFullscreen();
                } else if (document.webkitExitFullscreen) {
                    document.webkitExitFullscreen();
                } else if (document.mozCancelFullScreen) {
                    document.mozCancelFullScreen();
                } else if (document.msExitFullscreen) {
                    document.msExitFullscreen();
                }
            }else{
                if (body.requestFullscreen) {
                    body.requestFullscreen();
                } else if (body.webkitRequestFullscreen) {
                    body.webkitRequestFullscreen();
                } else if (body.mozRequestFullScreen) {
                    body.mozRequestFullScreen();
                } else if (body.msRequestFullscreen) {
                    body.msRequestFullscreen();
                }
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
                var url = document.URL + "?" + this.getCurrentUrlParams();
                $map_link = $("#map_link"),
                $iframe_link = $("#iframe_link"),
                $embed_link = $("#js-embed-link");
                //if (url.indexOf('?') != -1) {
                //    url = url.substring(0, url.indexOf('?'));
                //}
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

            var statDiv = document.createElement('div');
            statDiv.className = "map-button statistics-control";
            statDiv.innerHTML = $("#statistics-control").html();
            google.maps.event.addDomListener(statDiv, 'click', function () {
                statPanelClick(700,400,700,350);
            }.bind(this));

            var fullScreenDiv = document.createElement('div');
            fullScreenDiv.className = "map-button full-screen-control";
            fullScreenDiv.innerHTML = $("#full-screen-control").html();
            google.maps.event.addDomListener(fullScreenDiv, 'click', function () {
                this.fullScreen();
            }.bind(this));

            mapControlDiv.appendChild(resetMapDiv);
            mapControlDiv.appendChild(downloadCsvDiv);
            mapControlDiv.appendChild(linkMapDiv);
            mapControlDiv.appendChild(tourDiv);
            mapControlDiv.appendChild(statDiv);
            mapControlDiv.appendChild(fullScreenDiv);
            if (MAP_ONLY)
                mapControlDiv.style = "display:none";

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

            var statLabel = document.createElement('div');
            statLabel.className = 'control-label';
            statLabel.innerHTML = 'גרפים';
            statDiv.appendChild(statLabel);

            var fullScreenLabel = document.createElement('div');
            fullScreenLabel.className = 'control-label';
            fullScreenLabel.innerHTML = 'מסך מלא';
            fullScreenDiv.appendChild(fullScreenLabel);

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

            var toggleBGDiv = document.createElement('div');
            toggleBGDiv.className = "toggle-control-bg";
            if (MAP_ONLY)
                toggleBGDiv.style = "display:none";
            toggleBGDiv.innerHTML = $("#toggle-control").html();

            var toggleDiv = document.createElement('div');
            toggleDiv.className = "map-button toggle-control pin";
            if (MAP_ONLY)
                toggleDiv.style = "display:none";
            toggleDiv.title = 'שנה תצוגת אייקונים';
            google.maps.event.addDomListener(toggleBGDiv, 'click', function () {
                $(toggleDiv).toggleClass('pin');
                $(toggleDiv).toggleClass('dot');
                this.iconTypeChanged = true;
                this.toggleMarkerIconType();
            }.bind(this));

            toggleBGDiv.appendChild(toggleDiv);
            this.map.controls[google.maps.ControlPosition.TOP_RIGHT].push(toggleBGDiv);

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
                    marker.setTitle(marker.view.getTitle('single'));
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

            $('#toggle-sidebar').click(function () {
                $('.main').toggleClass('main-open').toggleClass('main-close');
                $('.sidebar-container').toggleClass('sidebar-container-open').toggleClass('sidebar-container-close');
                
                setTimeout(function() {
                    google.maps.event.trigger(this.map, 'resize');
                }.bind(this), 500);
            }.bind(this));
            this.isReady = true;
            google.maps.event.addListener(this.map, "rightclick", _.bind(this.contextMenuMap, this) );
            google.maps.event.addListener(this.map, "idle", function(){
                if (!this.firstLoadDelay){
                    this.fetchMarkers();
                }
            }.bind(this) );
            google.maps.event.addListener(this.map, "click", _.bind(this.clickMap, this) );
            this.sidebar.setResponsively();
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
                var markerView = new MarkerView({model: model, map: this.map, markerIconType: this.markerIconType}).render();
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
        loginDialogLoad: function(){
            if (this.createDialog) this.createDialog.close();
            this.createDialog = new LoginDialog().render();
        },
        preferencesDialogLoad: function () {
            if (this.createDialog) this.createDialog.close();
            this.createDialog = new PreferencesDialog().render();
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
              icon: {
                    path: google.maps.SymbolPath.CIRCLE,
                    scale: 0,
                    fillColor: 'black'
              },
              title: 'מיקום נוכחי'
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
            var params = this.buildMarkersParams(true);
            var returnParams = [];
            $.each(params, function(attr, attr_value) {
                returnParams.push(attr + "=" + attr_value);
            });
            return returnParams.join("&");
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
        toggleMarkerIconType: function(){
            this.markerIconType = !this.markerIconType;
            this.resetMarkers();
            this.fetchMarkers();
        },
        loadFilter: function() {
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

            this.weather = $("input[type='radio'][name='weather']:checked").val();
            this.road = $("input[type='radio'][name='road']:checked").val();
            this.separation = $("input[type='radio'][name='separation']:checked").val();
            this.surface = $("input[type='radio'][name='surface']:checked").val();
            this.acctype = $("input[type='radio'][name='acctype']:checked").val();
            this.controlmeasure = $("input[type='radio'][name='controlmeasure']:checked").val();
            this.district = $("input[type='radio'][name='district']:checked").val();
            this.case_type = $("input[type='radio'][name='casetype']:checked").val();

            this.dateRanges = [new Date($("#sdate").val()), new Date($("#edate").val())]
            this.resetMarkers();
            this.fetchMarkers();
            this.updateFilterString();
        },
        loadFilterFromParameters: function() {
            var bool_atrs = {};
            bool_atrs["checkbox-discussions"] = this.show_discussions;
            bool_atrs["checkbox-accidents"] = this.show_markers;
            bool_atrs["checkbox-accurate"] = this.accurate;
            bool_atrs["checkbox-approx"] = this.approx;
            bool_atrs["checkbox-fatal"] = this.show_fatal;
            bool_atrs["checkbox-severe"] = this.show_severe;
            bool_atrs["checkbox-light"] = this.show_light;

             $.each(bool_atrs, function(attr, attr_value) {
                 $('#' + attr).prop("checked", attr_value == '1');
             });

            if (this.show_urban == 3){
                $("#checkbox-urban").prop("checked", true);
                $("#checkbox-nonurban").prop("checked", true);
            }else if( this.show_urban == 2){
                $("#checkbox-urban").prop("checked", true);
                $("#checkbox-nonurban").prop("checked", false);
            }else if( this.show_urban == 1){
                $("#checkbox-nonurban").prop("checked", true);
                $("#checkbox-urban").prop("checked", false);
            }else{
                $("#checkbox-nonurban").prop("checked", false);
                $("#checkbox-urban").prop("checked", false);
            }

            if (this.show_intersection == 3){
                $("#checkbox-intersection").prop("checked", true);
                $("#checkbox-nonintersection").prop("checked", true);
            }else if( this.show_intersection == 2){
                $("#checkbox-intersection").prop("checked", true);
                $("#checkbox-nonintersection").prop("checked", false);
            }else if( this.show_intersection == 1){
                $("#checkbox-nonintersection").prop("checked", true);
                $("#checkbox-intersection").prop("checked", false);
            }else{
                $("#checkbox-nonintersection").prop("checked", false);
                $("#checkbox-intersection").prop("checked", false);
            }

            if (this.show_lane == 3){
                $("#checkbox-multi-lane").prop("checked", true);
                $("#checkbox-one-lane").prop("checked", true);
            }else if( this.show_lane == 2){
                $("#checkbox-multi-lane").prop("checked", true);
                $("#checkbox-one-lane").prop("checked", false);
            }else if( this.show_lane == 1){
                $("#checkbox-one-lane").prop("checked", true);
                $("#checkbox-multi-lane").prop("checked", false);
            }else{
                $("#checkbox-one-lane").prop("checked", false);
                $("#checkbox-multi-lane").prop("checked", false);
            }

            var radio_attrs = {};
            radio_attrs["weather"] = this.weather;
            radio_attrs["road"] = this.road;
            radio_attrs["separation"] = this.separation;
            radio_attrs["surface"] = this.surface;
            radio_attrs["acctype"] = this.acctype;
            radio_attrs["controlmeasure"] = this.controlmeasure;
            radio_attrs["district"] = this.district;
            radio_attrs["case_type"] = this.case_type;

            $.each(radio_attrs, function(attr, attr_value) {
                $("input[type='radio'][name='" + attr +"']").each(function() {
                    if($(this).val() == attr_value) {
                        $(this).prop("checked", true);
                    }
                });
            });

            if (this.dateRanges !== 'undefined') {
                document.getElementById("sdate").valueAsDate = new Date(this.dateRanges[0]);
                document.getElementById("edate").valueAsDate = new Date(this.dateRanges[1]);
            }
        },
        changeDate: function() {
            var start_date, end_date;
            if ($("#checkbox-all-years").is(":checked")) {
              start_date = "2005"; end_date = "2025"
            } else {
                for (yearNum in app.years) {
                    year = app.years[yearNum];
                    if($("#checkbox-"+year).is(":checked")) {
                        start_date = year; end_date = year + 1;
                        break;
                    }
                }
            }
            $("#sdate").val(start_date + '-01-01');
            $("#edate").val(end_date + '-01-01');

            this.show_day = $("input[type='radio'][name='day']:checked").val()
            this.show_holiday = $("input[type='radio'][name='holiday']:checked").val()
            this.show_time = $("input[type='radio'][name='time']:checked").val()
            // TODO: only parses the hour int for now, need to apply the minutes too
            if (!isNaN(parseInt($("#stime").val())) && !isNaN(parseInt($("#etime").val()))){
                this.start_time = parseInt($("#stime").val())
                this.end_time = parseInt($("#etime").val())
                $("#checkbox-time-all").prop('checked', true);
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
                    approx = "ומרחבי";
                } else if (approx == '1') {
                    approx = "מרחבי ";
                } else {
                    approx = "";
                }
                if (accurate == '' && approx == '') {
                    accuracyText = ""
                }

                $("#filter-string").empty()
                    .append("<span>מציג </span>")
                    .append("<span><a onclick='showFilter(FILTER_MARKERS)'>"+markerCount+"</a></span>")
                    .append("<span> תאונות</span>")
                    .append("<span> בין התאריכים </span><br>")
                    .append("<span><a onclick='showFilter(FILTER_DATE)'>"+
                                moment(this.dateRanges[0]).format('LL') + " עד " +
                                moment(this.dateRanges[1]).format('LL') +"</a></span><br>")
                    .append("<span>" + severityText + "</span>")
                    .append("<span><a onclick='showFilter(FILTER_INFO)' style='color: #d81c32;'>" + fatal + "</a></span>")
                    .append("<span><a onclick='showFilter(FILTER_INFO)' style='color: #ff9f1c;'>" + severe + "</a></span>")
                    .append("<span><a onclick='showFilter(FILTER_INFO)' style='color: #ffd82b;'>" + light + "</a></span><br>")
                    .append("<span>" + accuracyText + "</span>")
                    .append("<span><a onclick='showFilter(FILTER_INFO)'>" + accurate + "</a></span>")
                    .append("<span><a onclick='showFilter(FILTER_INFO)'>" + approx + "</a></span>")
                ;
            } else {
                $("#filter-string").empty()
                    .append("<p>התקרב על מנת לקבל נתוני סינון</p>");
            }
        }
    });
});

