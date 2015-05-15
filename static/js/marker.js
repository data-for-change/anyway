var INACCURATE_MARKER_OPACITY = 0.5;

var MarkerView = Backbone.View.extend({


	events : {
		//"click .follow-button" : "clickFollow",
		//"click .unfollow-button" : "clickUnfollow",
		//"click .share-button" : "clickShare",
		"click .delete-button" : "clickDelete"
	},
	initialize : function(options) {
		this.map = options.map;
		this.model.bind("change:following", this.updateFollowing, this);
        _.bindAll(this, "clickMarker");
	},
	render : function() {
//		var user = this.model.get("user");

		var markerPosition = new google.maps.LatLng(this.model.get("latitude"), this.model.get("longitude"));

		this.marker = new google.maps.Marker({
			position: markerPosition,
			id: this.model.get("id")
		});

        app.clusterer.addMarker(this.marker);
        if (app.map.zoom < MINIMAL_ZOOM) {
            return this;
        }

        this.marker.setOpacity(this.model.get("locationAccuracy") == 1 ? 1.0 : INACCURATE_MARKER_OPACITY);
        this.marker.setIcon(this.getIcon());
		this.marker.setTitle(this.getTitle());
        this.marker.setMap(this.map);
        this.marker.view = this;

        app.oms.addMarker(this.marker);

		this.$el.html($("#marker-content-template").html());
		this.$el.width(400);
		this.$el.find(".title").text(localization.SUG_TEUNA[0][this.model.get("subtype")]);
		this.$el.find(".roadType").text(fields.SUG_DEREH + ": " + localization.SUG_DEREH[0][this.model.get("roadType")]);
		this.$el.find(".accidentType").text(fields.SUG_TEUNA+ ": " + localization.SUG_TEUNA[0][this.model.get("subtype")]);
		this.$el.find(".roadShape").text(fields.ZURAT_DEREH+ ": " + localization.ZURAT_DEREH[0][this.model.get("roadShape")]);
	    this.$el.find(".severityText").text(fields.HUMRAT_TEUNA + ": " + localization.HUMRAT_TEUNA[0][this.model.get("severity")]);
	    this.$el.find(".dayType").text(fields.SUG_YOM + ": " + localization.SUG_YOM[0][this.model.get("dayType")]);
        this.$el.find(".igun").text(fields.STATUS_IGUN + ": " + localization.STATUS_IGUN[0][this.model.get("locationAccuracy")]);
		this.$el.find(".unit").text(fields.YEHIDA + ": " + localization.YEHIDA[0][this.model.get("unit")]);
		this.$el.find(".mainStreet").text(this.model.get("mainStreet"));
		this.$el.find(".secondaryStreet").text(this.model.get("secondaryStreet"));
		this.$el.find(".junction").text(this.model.get("junction"));


		this.$el.find(".creation-date").text("תאריך: " +
                moment(this.model.get("created")).format("LLLL"));
//		if (user) {
//		    this.$el.find(".profile-image").attr("src", "https://graph.facebook.com/" + user.facebook_id + "/picture");
//		} else {
			this.$el.find(".profile-image").attr("src", "/static/img/lamas.png");
			this.$el.find(".profile-image").attr("width", "50px");
//		}
		this.$el.find(".type").text(TYPE_STRING[this.model.get("type")]);
//		var display_user = "";
//		if (user && user.first_name && user.last_name) {
//			display_user = user.first_name + " " + user.last_name;
//		} else {
			display_user = 'הלשכה המרכזית לסטטיסטיקה';
//		}
		this.$el.find(".added-by").text("נוסף על ידי " + display_user);
//		this.$followButton = this.$el.find(".follow-button");
//		this.$unfollowButton = this.$el.find(".unfollow-button");
//		this.$followerList = this.$el.find(".followers");
//		this.$deleteButton = this.$el.find(".delete-button");
//
//		this.updateFollowing();
//
//		if (app.model.get("user") && app.model.get("user").is_admin) {
//			this.$deleteButton.show();
//		}

		return this;
	},
    getIcon : function() {
        return getIcon(this.model.get("subtype"), this.model.get("severity"));
    },
    getTitle : function() {
        return moment(this.model.get("created")).format("l") +
            " תאונה " + SEVERITY_MAP[this.model.get("severity")] +
            ": " + SUBTYPE_STRING[this.model.get("subtype")];
    },
    choose : function() {
        if (app.oms.markersNearMarker(this.marker).length) {
            new google.maps.event.trigger(this.marker, "click");
        }
        new google.maps.event.trigger(this.marker, "click");
    },
    getUrl: function () {
        var dateRange = app.model.get("dateRange");
        var center = app.map.getCenter();
        return "/?marker=" + this.model.get("id") + "&" + app.getCurrentUrlParams();
    },
    clickMarker : function() {
        this.highlight();
        app.closeInfoWindow();

        app.selectedMarker = this;
        app.infoWindow = new google.maps.InfoWindow({
            content: this.el
        });

        app.infoWindow.open(this.map, this.marker);
        app.updateUrl(this.getUrl());

        google.maps.event.addListener(app.infoWindow,"closeclick",function(){
            app.fetchMarkers();
        });

        $(document).keydown(app.ESCinfoWindow);

    },
    highlight : function() {
    	if (app.oms.markersNearMarker(this.marker, true)[0]  && !this.model.get("currentlySpiderfied")){
            this.resetOpacitySeverity();
    	}
        this.marker.setAnimation(google.maps.Animation.BOUNCE);


        // ##############################
        // # Another option, if we don't want the somewhat unintuitive experience where an icon start's bouncing,
        // # but other icons in the same place stay still, will be to do like so: (option 2)
        // ##############################

        // _.each(app.oms.markersNearMarker(this.marker), function (marker){

        //     marker.setAnimation(google.maps.Animation.BOUNCE);

        // });
        // this.marker.setAnimation(google.maps.Animation.BOUNCE);

        // ## END (option 2)

    },
    unhighlight : function() {
    	if (app.oms.markersNearMarker(this.marker, true)[0] && !this.model.get("currentlySpiderfied")){
            this.opacitySeverityForGroup();
    	}
        this.marker.setAnimation(null);


        // ##############################
        // # Option 2
        // ##############################

        // _.each(app.oms.markersNearMarker(this.marker), function (marker){

        //     marker.setAnimation(null);

        // });
        // this.marker.setAnimation(null);

        // ## END (option 2)

    },
//	updateFollowing : function() {
//		if (this.model.get("following")) {
//			this.$followButton.hide();
//			this.$unfollowButton.show();
//		} else {
//			this.$followButton.show();
//			this.$unfollowButton.hide();
//		}
//
//		this.$followerList.empty();
//        var followers = this.model.get('followers');
//        for (var i = 0; followers && i < followers.length; i++) {
//            var follower = this.model.get("followers")[i].facebook_id;
//            var image = "https://graph.facebook.com/" + follower + "/picture";
//            this.$followerList.append($("<img>").attr("src", image));
//        }
//
//	},
//	clickFollow : function() {
//		this.model.save({following: true}, {wait:true});
//	},
//	clickUnfollow : function() {
//		this.model.save({following: false}, {wait:true});
//	},
//	clickDelete : function() {
//		this.model.destroy();
//	},
	clickShare : function() {
		FB.ui({
			method: "feed",
			name: this.model.get("title"),
			link: document.location.href,
			description: this.model.get("description"),
			caption: SUBTYPE_STRING[this.model.get("subtype")]
			// picture
		}, function(response) {
			if (response && response.post_id) {
				// console.log("published");
			}
		});
	},
    resetOpacitySeverity : function() {
        this.marker.icon = this.getIcon();
        this.marker.opacity = this.model.get("locationAccuracy") == 1 ? 1.0 : INACCURATE_MARKER_OPACITY;
    },
    opacitySeverityForGroup : function() {
        var group = this.model.get("groupID") -1;
        this.marker.icon = MULTIPLE_ICONS[app.groupsData[group].severity];
        if (app.groupsData[group].opacity != 'opaque'){
            this.marker.opacity = INACCURATE_MARKER_OPACITY / app.groupsData[group].opacity;
        }
    }

});