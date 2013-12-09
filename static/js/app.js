var ADD_MARKER_OFFER = "הוסף הצעה";
var ADD_MARKER_PETITION = "הוסף עצומה";
var INIT_LAT = 32.0833;
var INIT_LON = 34.8000;
var INIT_ZOOM = 14;
var ICONS = [
    "/img/icons/vehicle_object_lethal.png",
    "/img/icons/vehicle_object_medium.png",
    "/img/icons/vehicle_object_severe.png",
    "/img/icons/vehicle_person_lethal.png",
    "/img/icons/vehicle_person_medium.png",
    "/img/icons/vehicle_person_severe.png",
    "/img/icons/vehicle_vehicle_lethal.png",
    "/img/icons/vehicle_vehicle_medium.png",
    "/img/icons/vehicle_vehicle_severe.png"
];

// dummy

var TYPE_STRING = [
    "הצעה",
    "עצומה"
];
$(function() {
    var AppRouter = Backbone.Router.extend({
        routes: {
            "" : "navigateEmpty",
            ":id" : "navigate"
        },
        navigate: function(id) {
            app.model.set("currentMarker", parseInt(id));
        },
        navigateEmpty: function() {
            app.model.set("currentMarker", null);
        }
    });

    window.MarkerCollection = Backbone.Collection.extend({
        url : "/markers"
    });

    window.AppView = Backbone.View.extend({
        el : $("#app"),
        events : {
            "click #map_canvas" : "clickMap",
            "click .fb-login" : "requireLogin",
            "click .fb-logout" : "logout",
            "change input[type=checkbox]" : "updateCheckbox"
        },
        initialize : function() {
            _.bindAll(this, "clickContext");

            this.markers = new MarkerCollection();
            this.model = new Backbone.Model();
            this.markerList = [];

            this.markers.bind("reset", this.loadMarkers, this);
            this.markers.bind("destroy", this.loadMarkers, this);
            this.markers.bind("add", this.loadMarker, this);
            this.markers.bind("change:currentModel", this.chooseMarker, this);
            //this.markers.bind("change", this.loadMarker, this);
            this.model.bind("change:user", this.updateUser, this);
            this.model.bind("change:layers", this.loadMarkers, this);
            this.model.bind("change:dateRange", this.loadMarkers, this);
            this.login();

        },
        fetchMarkers : function() {
            var bounds = this.map.getBounds();
            var zoom = this.map.zoom;

            var params = {};

            if (!bounds) {
                return;
            }

            if (bounds) {
                params["ne_lat"] = bounds.getNorthEast().lat();
                params["ne_lng"] = bounds.getNorthEast().lng();
                params["sw_lat"] = bounds.getSouthWest().lat();
                params["sw_lng"] = bounds.getSouthWest().lng();
                params["zoom"] = zoom;
            }

            this.markers.fetch({ data : $.param(params) });
        },
        render : function() {


            var styles = [

              {

                "featureType": "water",

                "elementType": "geometry",

                "stylers": [

                  { "color": "#9ecfec" }

                ]

              },{

                "featureType": "landscape.natural",

                "elementType": "geometry",

                "stylers": [

                  { "color": "#f2eeee" }

                ]

              },{

                "featureType": "landscape.man_made",

                "elementType": "geometry",

                "stylers": [

                  { "color": "#eae6e6" }

                ]

              },{

                "featureType": "poi",

                "elementType": "poi",

                "stylers": [

                  { "visibility": "off" }

                ]

              },{

                "featureType": "poi.park",

                "elementType": "geometry",

                "stylers": [

                  { "visibility": "on" },

                  { "color": "#d3e0bf" }

                ]

              },{

                "featureType": "road.highway",

                "elementType": "geometry.fill",

                "stylers": [

                  { "color": "#ffffff" }

                ]

              },{

                "featureType": "road.arterial",

                "elementType": "geometry.fill",

                "stylers": [

                  { "color": "#ffffff" }

                ]

              },{

                "featureType": "road.local",

                "elementType": "geometry.fill",

                "stylers": [

                  { "color": "#ffffff" }

                ]

              },{

                "featureType": "road.local",

                "elementType": "geometry.stroke",

                "stylers": [

                  { "color": "#c8c8c8" }

                ]

              },{

                "featureType": "road.arterial",

                "elementType": "geometry.stroke",

                "stylers": [

                  { "color": "#aaaaaa" }

                ]

              },{

                "featureType": "road.highway",

                "elementType": "geometry.stroke",

                "stylers": [

                  { "color": "#969696" }

                ]

              },{

                "featureType": "road.highway",

                "elementType": "labels.text.fill",

                "stylers": [

                  { "color": "#1e1e1e" }

                ]

              },{

                "featureType": "road.arterial",

                "elementType": "labels.text.fill",

                "stylers": [

                  { "color": "#1e1e1e" }

                ]

              },{

                "featureType": "road.local",

                "elementType": "labels.text.fill",

                "stylers": [

                  { "color": "#1e1e1e" }

                ]

              },{

                "featureType": "administrative",

                "elementType": "labels.text.fill",

                "stylers": [

                  { "color": "#505050" }

                ]

              },{

                "featureType": "transit.line",

                "stylers": [

                  { "color": "#4e99fe" }

                ]

              },{

                "featureType": "landscape"  }

            ];



            var geolocpoint=new google.maps.LatLng(INIT_LAT, INIT_LON);

            var mapOptions = {
                center: geolocpoint,
                zoom: INIT_ZOOM,
                mapTypeId: google.maps.MapTypeId.ROADMAP,
                mapTypeControl: false,
                zoomControl: true,
                panControl: true,
                styles: styles
            };
            var init_map = new google.maps.Map(this.$el.find("#map_canvas").get(0), mapOptions);

            if(navigator.geolocation){
                navigator.geolocation.getCurrentPosition(function(position){
                    var latitude=position.coords.latitude;
                    var longitude=position.coords.longitude;
                    geolocpoint=new google.maps.LatLng(latitude,longitude);
                    init_map.setCenter(geolocpoint);
                });

            }
            this.map=init_map;


            google.maps.event.addListener( this.map, "rightclick", _.bind(this.contextMenuMap, this) );
            google.maps.event.addListener( this.map, "mouseup", _.bind(this.fetchMarkers, this) );

            this.fetchMarkers();




            this.sidebar = new SidebarView({ map: this.map }).render();
            this.$el.find(".sidebar-container").append(this.sidebar.$el);

            //this.updateCheckbox();

            this.$el.find(".date-range").daterangepicker({
                    ranges: {
                        'היום': ['today', 'today'],
                        'אתמול': ['yesterday', 'yesterday'],
                        'שבוע אחרון': [Date.today().add({ days: -6 }), 'today'],
                        'חודש אחרון': [Date.today().add({ days: -29 }), 'today'],
                        'החודש הזה': [Date.today().moveToFirstDayOfMonth(), Date.today().moveToLastDayOfMonth()],
                        'החודש שעבר': [Date.today().moveToFirstDayOfMonth().add({ months: -1 }), Date.today().moveToFirstDayOfMonth().add({ days: -1 })]
                    },
                    opens: 'left',
                    format: 'dd/MM/yyyy',
                    separator: ' עד ',
                    startDate: Date.today().add({ days: -29 }),
                    endDate: Date.today(),
                    minDate: '01/01/2005',
                    maxDate: '12/31/2023',
                    locale: {
                        applyLabel: 'בחר',
                        fromLabel: 'מ',
                        toLabel: 'עד',
                        customRangeLabel: 'בחר תאריך',
                        daysOfWeek: ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr','Sa'],
                        monthNames: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
                        firstDay: 1
                    },
                    showWeekNumbers: true,
                    buttonClasses: ['btn-danger']
                },
                _.bind(function(start, end) {
                    this.model.set("dateRange", [start, end]);
                }, this)
            );

            this.router = new AppRouter();
            Backbone.history.start({pushState: true});

            return this;
        },
        clickMap : function(e) {
            console.log("clickd map");
        },
        updateCheckbox : function() {
            var layers = [];
            this.$el.find("input[type=checkbox]").each(function() {
                layers[parseInt($(this).data("type"))] = $(this).prop("checked");
            });
            this.model.set("layers", layers);
        },
        loadMarker : function(model) {
            console.log("loading marker", ICONS[model.get("subtype")]);

            if (this.model.get("layers") && !this.model.get("layers")[model.get("type")]) {
                console.log("skipping marker because the layer is not chosen");
                return;
            }

            if (this.model.get("dateRange")) {
                var createdDate = new Date(model.get("created"));

                var start = this.model.get("dateRange")[0];
                var end = this.model.get("dateRange")[1];

                if (createdDate < start || createdDate > end) {
                    console.log("skipping marker becuase the date is not in the range");
                    return;
                }

            }

            var markerView = new MarkerView({model: model, map: this.map}).render();


            model.set("markerView", this.markerList.length);
            this.markerList.push(markerView);

            this.chooseMarker(model.get("id"));

        },
        loadMarkers : function() {
            console.log("loading markers", this.markers);
            if (this.markerList) {
                _(this.markerList).each(_.bind(function(marker) {
                    marker.marker.setMap(null);
                }, this));
            }
            this.markerList = [];
            this.markers.each(_.bind(this.loadMarker, this));
            this.sidebar.updateMarkerList();
            this.chooseMarker();
        },
        chooseMarker: function(markerId) {
            var currentMarker = this.model.get("currentMarker");
            if (typeof markerId == "number" && currentMarker != markerId) {
                return;
            }
            console.log("choosing marker", currentMarker);
            if (!this.markerList.length) {
                return;
            }

            if (!this.markers.get(currentMarker)) {
                return;
            }
            var markerView = this.markerList[this.markers.get(currentMarker).get("markerView")];
            if (!markerView) {
                this.model.set("currentMarker", null);
                return;
            }

            new google.maps.event.trigger(markerView.marker , "click");
        },
        contextMenuMap : function(e) {
            if (this.menu) {
                this.menu.remove();
            }
            this.menu = new ContextMenuView({
                items : [
                    {
                        icon : "plus-sign",
                        text : ADD_MARKER_OFFER,
                        callback : this.clickContext
                    },
                    {
                        icon : "plus-sign",
                        text : ADD_MARKER_PETITION,
                        callback : this.clickContext
                    }
                ]}).render(e);
        },
        clickContext : function(item, event) {
            console.log("clicked item, require login");
            this.requireLogin(_.bind(function() {
                console.log("clicked item", item, event);
                this.openCreateDialog(item, event);
            }, this));
        },
        openCreateDialog : function(type, event) {
            if (this.createDialog) this.createDialog.close();
            this.createDialog = new MarkerDialog({
                type: type,
                event: event,
                markers: this.markers
            }).render();

        },
        requireLogin : function(callback) {
            if (this.model.get("user")) {
                if (typeof callback == "function") callback();
                return;
            }

            FB.getLoginStatus(_.bind(function(response) {
                if (response.status === 'connected') {
                    var uid = response.authResponse.userID;
                    var accessToken = response.authResponse.accessToken;

                    this.login(response.authResponse, callback);

                } else {
                    // the user is logged in to Facebook,
                    // but has not authenticated your app
                    FB.login(_.bind(function(response) {
                        if (response.authResponse) {
                            this.login(response.authResponse, callback);
                        } else {
                            console.log('User cancelled login or did not fully authorize.');
                        }
                    }, this), {scope:"email"});
                }
            }, this));

        },
        login : function(authResponse, callback) {
            console.log("Logging in...");
            $.ajax({
                url: "/login",
                type: "post",
                data: JSON.stringify(authResponse),
                contentType: "application/json",
                traditional: true,
                dataType: "json",
                success: _.bind(function(user) {
                    if (user) {
                        this.model.set("user", user);
                        if (typeof callback == "function") callback();
                    }
                }, this),
                error: _.bind(function() {

                }, this)
            });
        },
        logout : function() {
            this.model.set("user", null);
            FB.logout();
        },
        updateUser : function() {
            var user = this.model.get("user");

            if (user) {
                this.$el.find(".fb-login").hide();

                this.$el.find(".user-details").show();
                this.$el.find(".profile-picture").attr("src", 'https://graph.facebook.com/' + user.facebook_id + '/picture');
                this.$el.find(".profile-name").text(user.first_name);

            } else {
                this.$el.find(".fb-login").show();
                this.$el.find(".user-details").hide();

            }
        }
    });
});
