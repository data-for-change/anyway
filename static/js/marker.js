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
			icon: ICONS[this.model.get("subtype")],
			title: this.model.get("title")
		});

		this.$el.html($("#marker-content-template").html());

		this.$el.width(400);
		this.$el.find(".title").text(this.model.get("title"));
		this.$el.find(".description").text(this.model.get("description"));
		this.$el.find(".profile-image").attr("src", "https://graph.facebook.com/" + user.facebook_id + "/picture");
		this.$el.find(".type").text(TYPE_STRING[this.model.get("type")]);
		this.$el.find(".added-by").text("נוסף על ידי " + user.first_name + " " + user.last_name);

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
			caption: TYPE_STRING[this.model.get("type")]
			// picture
		}, function(response) {
			if (response && response.post_id) {
				console.log("published");
			}
		});
	}
});