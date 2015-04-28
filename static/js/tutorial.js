if (document.cookie.indexOf("visited") == -1) {	
	document.cookie = "visited=yes";  
	var steps = [{
              content: '<p>ברוכים הבאים ל - anyway. האתר מציג נתוני תאונות לפי מיקום.</p>',
              highlightTarget: true,
              nextButton: true,
              target: $('#step1Component'),
              my: 'top center',
              at: 'bottom center'
            }, {
              content: '<p>בפאנל הזה תוכלו לבחור את סוגי התאונות שאתם מעוניינים לראות וטווח התאריכים שלהן. בנוסף, תוכלו לצפות בפרטי התאונות שנמצאות בחלון הנוכחי.</p>',
              highlightTarget: true,
              nextButton: true,
              target: $('#step2Component'),
              my: 'top right',
              at: 'left center'
            }]

            var tour = new Tourist.Tour({
              steps: steps,
              tipClass: 'Bootstrap',
              tipOptions:{ showEffect: 'slidein' }
            });
            tour.start();
}


