var ADD_MARKER_OFFER = "הוסף הצעה";
var ADD_MARKER_PETITION = "הוסף עצומה";
var INIT_LAT = 32.0833;
var INIT_LON = 34.8000;
var INIT_ZOOM = 14;
var ICONS = [
	"/img/exclamation.png",
	"/img/events.png"
];
var TYPE_STRING = [
	"הצעה",
	"עצומה"
];
$(function() {
	var AppRouter = Backbone.Router.extend({
		routes: {
			":id" : "navigate"
		},
		navigate: function(id) {
			console.log(id);
			app.model.set("currentMarker", parseInt(id))
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
			"click .fb-logout" : "logout"
		},
		initialize : function() {
			_.bindAll(this, "clickContext");

			this.markers = new MarkerCollection();
			this.model = new Backbone.Model();
			this.markerList = [];

			this.markers.bind("reset", this.loadMarkers, this);
			this.markers.bind("add", this.loadMarker, this);
			this.markers.bind("change:currentModel", this.chooseMarker, this);
			//this.markers.bind("change", this.loadMarker, this);
			this.model.bind("change:user", this.updateUser, this);
			this.login();

		},
		render : function() {
			//this.markers.fetch({add: false, reset: true});
			this.markers.fetch();

			var mapOptions = {
				center: new google.maps.LatLng(INIT_LAT, INIT_LON),
				zoom: INIT_ZOOM,
				mapTypeId: google.maps.MapTypeId.ROADMAP
			};
			this.map = new google.maps.Map(this.$el.find("#map_canvas").get(0), mapOptions);

			google.maps.event.addListener( this.map, "rightclick", _.bind(this.contextMenuMap, this) );

			this.sidebar = new SidebarView({ map: this.map }).render();
			this.$el.find(".sidebar-container").append(this.sidebar.$el);

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
					minDate: '01/01/2013',
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
					this.startRange = start;
					this.endRange = end;
				}, this)
			);

			this.router = new AppRouter();
			Backbone.history.start({pushState: true});

			return this;
		},
		clickMap : function(e) {
			console.log("clickd map");
		},
		loadMarker : function(model) {
			console.log("loading marker", model, ICONS[this.model.get("type")]);
			var markerPosition = new google.maps.LatLng(model.get("latitude"), model.get("longitude"));
			var marker = new google.maps.Marker({
				position: markerPosition,
				map: this.map,
				icon: ICONS[model.get("type")],
				title: model.get("title")
			});

			// TODO: move info window to a new view
			var markerContent = $($("#marker-content-template").html());
			markerContent.width(400).height(300);
			markerContent.find(".title").text(model.get("title"));
			markerContent.find(".description").text(model.get("description"));
			markerContent.find(".profile-image").attr("src", "https://graph.facebook.com/" + model.get("user").facebook_id + "/picture");
			markerContent.find(".type").text(TYPE_STRING[model.get("type")]);
			markerContent.find(".added-by").text("נוסף על ידי " + model.get("user").first_name + " " + model.get("user").last_name);

			var $followButton = markerContent.find(".follow-button");
			var $unfollowButton = markerContent.find(".unfollow-button");
			var $shareButton = markerContent.find(".share-button");
			var $followerList = markerContent.find(".followers");

			$followButton.click(function() {
				model.save({following: true}, {wait:true});
			});

			$unfollowButton.click(function() {
				model.save({following: false}, {wait:true});
			});

			var updateFollowing = function() {
				if (model.get("following")) {
					$followButton.hide();
					$unfollowButton.show();
				} else {
					$followButton.show();
					$unfollowButton.hide();
				}

				$followerList.empty();
				for (var i = 0; i < model.get("followers").length; i++) {
					var follower = model.get("followers")[i].facebook_id;
					var image = "https://graph.facebook.com/" + follower + "/picture";
					$followerList.append($("<img>").attr("src", image));
				}
			};
			updateFollowing();
			model.bind("change:following", updateFollowing, model);

			$shareButton.click(function() {
				FB.ui({
					method: "feed",
					name: model.get("title"),
					link: document.location.href,
					description: model.get("description"),
					caption: TYPE_STRING[model.get("type")]
					// picture
				}, function(response) {
					if (response && response.post_id) {
						console.log("published");
					}
				});
			});

			var markerWindow = new google.maps.InfoWindow({
				content: markerContent.get(0)
			});

			google.maps.event.addListener(marker, 'click', _.bind(function() {
				if (this.infowindow) {
					this.infowindow.close();
				}
				markerWindow.open(this.map, marker);
				this.infowindow = markerWindow;
				Backbone.history.navigate("/" + model.get("id"), false);

			}, this));

			model.set("markerView", this.markerList.length);
			this.markerList.push(marker);

			this.chooseMarker(model.get("id"));
		},
		loadMarkers : function() {
			console.log("loading markers", this.markers);
			if (this.markerList) {
				_(this.markerList).each(function(marker) {
					this.map.removeOverlay(marker);
				});
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
			var markerView = this.markerList[this.markers.get(currentMarker).get("markerView")];
			new google.maps.event.trigger( markerView, 'click' );
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
