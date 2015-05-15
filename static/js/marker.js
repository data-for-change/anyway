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
		this.$el.find(".title").text(TYPES_MAP[this.model.get("title")]);

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

var localization =
{
      "SUG_DEREH": [{
        "1": "עירוני בצומת",
        "2": "עירוני לא בצומת",
        "3": "לא עירוני בצומת",
        "4": "לא עירוני לא בצומת"
      }],
      "YEHIDA": [{
        "11" : "מרחב חוף (חיפה)",
        "12" : "מרחב גליל",
        "14" : "מרחב עמקים",
        "20" : "מרחב ת\"א",
        "33" : "מרחב אילת",
        "34" : "מרחב הנגב",
        "36" : "מרחב שמשון (עד 1999)",
        "37" : "מרחב שמשון (החל ב-2004)",
        "38" : "מרחב לכיש",
        "41" : "מרחב שומרון",
        "43" : "מרחב יהודה",
        "51" : "מרחב השרון",
        "52" : "מרחב השפלה",
        "61" : "מחוז ירושלים"
      }],
      "SUG_YOM": [{
        "1" : "חג",
        "2" : "ערב חג",
        "3" : "חול המועד",
        "4" : "יום אחר",
       }],
      "HUMRAT_TEUNA": [{
        "1" : "קטלנית",
        "2" : "קשה",
        "3" : "קלה",
        }],
      "SUG_TEUNA": [{
        "1" : "פגיעה בהולך רגל",
        "2" : "התנגשות חזית אל צד",
        "3" : "התנגשות חזית באחור",
        "4" : "התנגשות צד בצד",
        "5" : "התנגשות חזית אל חזית",
        "6" : "התנגשות עם רכב שנעצר ללא חניה",
        "7" : "התנגשות עם רכב חונה",
        "8" : "התנגשות עם עצם דומם",
        "9" : "ירידה מהכביש או עלייה למדרכה",
        "10" : "התהפכות",
        "11" : "החלקה",
        "12" : "פגיעה בנוסע בתוך כלי רכב",
        "13" : "נפילה ברכב נע",
        "14" : "שריפה",
        "15" : "אחר",
        "17" : "התנגשות אחור אל חזית",
        "18" : "התנגשות אחור אל צד",
        "19" : "התנגשות עם בעל חיים",
        "20" : "פגיעה ממטען של רכב",
        }],
      "ZURAT_DEREH": [{
        "1" : "כניסה למחלף",
        "2" : "ביציאה ממחלף",
        "3" : "מ.חניה/ת. דלק",
        "4" : "שיפוע תלול",
        "5" : "עקום חד",
        "6" : "על גשר מנהרה",
        "7" : "מפגש מסילת ברזל",
        "8" : "כביש ישר/צומת",
        "9" : "אחר",
        }],
      "HAD_MASLUL": [{
        "1": "חד סיטרי",
        "2" : "דו סיטרי+קו הפרדה רצוף",
        "3" : "דו סיטרי אין קו הפרדה רצוף",
        "4" : "אחר",
        }],
      "RAV_MASLUL": [{
        "1" : "מיפרדה מסומנת בצבע",
        "2" : "מיפרדה עם גדר בטיחות",
        "3" : "מיפרדה בנויה ללא גדר בטיחות",
        "4" : "מיפרדה לא בנויה",
        "5" : "אחר",
        }],
      "MEHIRUT_MUTERET": [{
        "1" : "עד 50 קמ\"ש",
        "2" : "60 קמ\"ש",
        "3" : "70 קמ\"ש",
        "4" : "80 קמ\"ש",
        "5" : "90 קמ\"ש",
        "6" : "100 קמ\"ש",
        }],
    "TKINUT": [{
        "1" : "אין ליקוי",
        "2" : "שוליים גרועים",
        "3" : "כביש משובש",
        "4" : "שוליים גרועים וכביש משובש",
        }],
    "ROHAV": [{
        "1" : "עד 5 מטר",
        "2" : "5 עד 7",
        "3" : "7 עד 10.5",
        "4" : "10.5 עד 14",
        "5" : "יותר מ-14",
    }],
    "SIMUN_TIMRUR": [{
        "1" : "סימון לקוי/חסר",
        "2" : "תימרור לקוי/חסר",
        "3" : "אין ליקוי",
        "4" : "לא נדרש תמרור",
    }],
    "TEURA": [{
        "1" : "אור יום רגיל",
        "2" : "ראות מוגבלת עקב מזג אויר (עשן,ערפל)",
        "3" : "לילה פעלה תאורה",
        "4" : "קיימת תאורה בלתי תקינה/לא פועלת",
        "5" : "לילה לא קיימת תאורה",
    }],
    "BAKARA": [{
        "1" : "אין בקרה",
        "2" : "רמזור תקין",
        "3" : "רמזור מהבהב צהוב",
        "4" : "רמזור לא תקין",
        "5" : "תמרור עצור",
        "6" : "תמרור זכות קדימה",
        "7" : "אחר",
    }],
    "MEZEG_AVIR": [{
        "1" : "בהיר",
        "2" : "גשום",
        "3" : "שרבי",
        "4" : "ערפילי",
        "5" : "אחר",
    }],
    "PNE_KVISH": [{
        "1" : "יבש",
        "2" : "רטוב ממים",
        "3" : "מרוח בחומר דלק",
        "4" : "מכוסה בבוץ",
        "5" : "חול או חצץ על הכביש",
        "6" : "אחר",
    }],
    "SUG_EZEM": [{
        "1" : "עץ",
        "2" : "עמוד חשמל/תאורה/טלפון",
        "3" : "תמרור ושלט",
        "4" : "גשר סימניו ומגיניו",
        "5" : "מבנה",
        "6" : "גדר בטיחות לרכב",
        "7" : "חבית",
        "8" : "אחר",
    }],
    "MERHAK_EZEM": [{
        "1" : "עד מטר",
        "2" : "1-3 מטר",
        "3" : "על הכביש",
        "4" : "על שטח הפרדה",
    }],
    "LO_HAZA": [{
        "1" : "הלך בכיוון התנועה",
        "2" : "הלך נגד",
        "3" : "שיחק על הכביש",
        "4" : "עמד על הכביש",
        "5" : "היה על אי הפרדה",
        "6" : "היה על שוליים/מדרכה",
        "7" : "אחר",
    }],
    "OFEN_HAZIYA": [{
        "1" : "התפרץ אל הכביש",
        "2" : "חצה שהוא מוסתר",
        "3" : "חצה רגיל",
        "4" : "אחר",
    }],
    "MEKOM_HAZIYA": [{
        "1" : "לא במעבר חציה ליד צומת",
        "2" : "לא במעבר חציה לא ליד צומת",
        "3" : "במעבר חציה בלי רמזור",
        "4" : "במעבר חציה עם רמזור",
    }],
    "KIVUN_HAZIYA": [{
        "1" : "מימין לשמאל",
        "2" : "משמאל לימין",
    }],
    "STATUS_IGUN": [{
        "1" : "עיגון מדויק",
        "2" : "מרכז ישוב",
        "3" : "מרכז דרך",
        "4" : "מרכז קילומטר",
        "9" : "לא עוגן",
    }]
 }

 var fields = {
                "pk_teuna_fikt": "מזהה",
                "SUG_DEREH": "סוג דרך",
                "SHEM_ZOMET": "שם צומת",
                "SEMEL_YISHUV": "ישוב",
                "REHOV1": "רחוב 1",
                "REHOV2": "רחוב 2",
                "BAYIT": "מספר בית",
                "ZOMET_IRONI": "צומת עירוני",
                "KVISH1": "כביש 1",
                "KVISH2": "כביש 2",
                "ZOMET_LO_IRONI": "צומת לא עירוני",
                "YEHIDA": "יחידה",
                "SUG_YOM": "סוג יום",
                "RAMZOR": "רמזור",
                "HUMRAT_TEUNA": "חומרת תאונה",
                "SUG_TEUNA": "סוג תאונה",
                "ZURAT_DEREH": "צורת דרך",
                "HAD_MASLUL": "חד מסלול",
                "RAV_MASLUL": "רב מסלול",
                "MEHIRUT_MUTERET": "מהירות מותרת",
                "TKINUT": "תקינות",
                "ROHAV": "רוחב",
                "SIMUN_TIMRUR": "סימון תמרור",
                "TEURA": "תאורה",
                "BAKARA": "בקרה",
                "MEZEG_AVIR": "מזג אוויר",
                "PNE_KVISH": "פני כביש",
                "SUG_EZEM": "סוג עצם",
                "MERHAK_EZEM": "מרחק עצם",
                "LO_HAZA": "לא חצה",
                "OFEN_HAZIYA": "אופן חציה",
                "MEKOM_HAZIYA": "מקום חציה",
                "KIVUN_HAZIYA": "כיוון חציה",
                "STATUS_IGUN": "עיגון",
                "MAHOZ": "מחוז",
                "NAFA": "נפה",
                "EZOR_TIVI": "אזור טבעי",
                "MAAMAD_MINIZIPALI": "מעמד מוניציפלי",
                "ZURAT_ISHUV": "צורת יישוב"
                }

