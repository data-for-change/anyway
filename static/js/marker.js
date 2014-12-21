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
		var user = this.model.get("user");

		var markerPosition = new google.maps.LatLng(this.model.get("latitude"), this.model.get("longitude"));

		this.marker = new google.maps.Marker({
			position: markerPosition,
			map: this.map,
			icon: this.getIcon(),
			title: this.getTitle(),
			id: this.model.get("id"),
			opacity: this.model.get("locationAccuracy") == 1 ? 1.0 : INACCURATE_MARKER_OPACITY
		});

        app.oms.addMarker(this.marker);
        this.marker.view = this;

		this.$el.html($("#marker-content-template").html());

		this.$el.width(400);
		this.$el.find(".title").text(TYPES_MAP[this.model.get("title")]);
		this.$el.find(".description").text(this.model.get("description"));
		this.$el.find(".creation-date").text("תאריך: " +
                moment(this.model.get("created")).format("LLLL"));
		if (user) {
		    this.$el.find(".profile-image").attr("src", "https://graph.facebook.com/" + user.facebook_id + "/picture");
		} else {
			this.$el.find(".profile-image").attr("src", "/static/img/lamas.png");
			this.$el.find(".profile-image").attr("width", "50px");
		}
		this.$el.find(".type").text(TYPE_STRING[this.model.get("type")]);
		var display_user = "";
		if (user.first_name && user.last_name) {
			display_user = user.first_name + " " + user.last_name;
		} else {
			display_user = 'הלשכה המרכזית לסטטיסטיקה';
		}
		this.$el.find(".added-by").text("נוסף על ידי " + display_user);
		this.$followButton = this.$el.find(".follow-button");
		this.$unfollowButton = this.$el.find(".unfollow-button");
		this.$followerList = this.$el.find(".followers");
		this.$deleteButton = this.$el.find(".delete-button");

		this.updateFollowing();

		if (app.model.get("user") && app.model.get("user").is_admin) {
			this.$deleteButton.show();
		}

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
        return "/?marker=" + this.model.get("id") +
            "&start_date=" + moment(dateRange[0]).format("YYYY-MM-DD") +
            "&end_date=" + moment(dateRange[1]).format("YYYY-MM-DD") +
            "&show_fatal=" + (app.model.get("showFatal") ? 1 : 0) +
            "&show_severe=" + (app.model.get("showSevere") ? 1 : 0) +
            "&show_light=" + (app.model.get("showLight") ? 1 : 0) +
            "&show_inaccurate=" + (app.model.get("showInaccurateMarkers") ? 1 : 0);
    }, clickMarker : function() {
        app.closeInfoWindow();

        app.infoWindow = new google.maps.InfoWindow({
            content: this.el
        });

        app.infoWindow.open(this.map, this.marker);
        Backbone.history.navigate(this.getUrl(), true);

        google.maps.event.addListener(app.infoWindow,"closeclick",function(){
            Backbone.history.navigate("/", true);
        });
    },
	updateFollowing : function() {
		if (this.model.get("following")) {
			this.$followButton.hide();
			this.$unfollowButton.show();
		} else {
			this.$followButton.show();
			this.$unfollowButton.hide();
		}

		this.$followerList.empty();
		for (var i = 0; i < this.model.get("followers").length; i++) {
			var follower = this.model.get("followers")[i].facebook_id;
			var image = "https://graph.facebook.com/" + follower + "/picture";
			this.$followerList.append($("<img>").attr("src", image));
		}
	},
	clickFollow : function() {
		this.model.save({following: true}, {wait:true});
	},
	clickUnfollow : function() {
		this.model.save({following: false}, {wait:true});
	},
	clickDelete : function() {
		this.model.destroy();
	},
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
	}
});
