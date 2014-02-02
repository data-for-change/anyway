var MarkerView = Backbone.View.extend({
	events : {
		"click .follow-button" : "clickFollow",
		"click .unfollow-button" : "clickUnfollow",
		"click .share-button" : "clickShare",
		"click .delete-button" : "clickDelete"
	},
	initialize : function(options) {
		this.map = options.map;
		this.model.bind("change:following", this.updateFollowing, this);
	},
	render : function() {
		var user = this.model.get("user");

		var markerPosition = new google.maps.LatLng(this.model.get("latitude"), this.model.get("longitude"));
		
		this.marker = new google.maps.Marker({
			position: markerPosition,
			map: this.map,
			icon: getIcon(this.model.get("subtype"), this.model.get("severity")),
			title: this.model.get("title")
		});

		this.$el.html($("#marker-content-template").html());

		this.$el.width(400);
		this.$el.find(".title").text(TYPES_MAP[this.model.get("title")]);
		this.$el.find(".description").text(this.model.get("description"));
		this.$el.find(".creation-date").text("תאריך " + this.model.get("created") );
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

		var markerWindow = new google.maps.InfoWindow({
			content: this.el
		});

		google.maps.event.addListener(this.marker, "click", _.bind(function() {
			if (app.infowindow) {
				app.infowindow.close();
			}
			markerWindow.open(this.map, this.marker);
			app.infowindow = markerWindow;
			Backbone.history.navigate("/" + this.model.get("id"), true);
		}, this));

		google.maps.event.addListener(markerWindow,"closeclick",function(){
			Backbone.history.navigate("/", true);
		});

		return this;

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
				console.log("published");
			}
		});
	}
});
