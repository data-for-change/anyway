/**
 * Created by root on 30/04/15.
 */

var infowindow;
var checkStepsAdd = false;
var tourLocation = 0;
var tour1 = new Tour({
    storage: window.localStorage,
    template: "<div class='popover tour' role='tooltip' > \
    <div class='arrow'></div>\
    <button type='button' class='close' data-role='end'><span>×</span></button> \
    <h3 class='popover-title'></h3> \
    <div class='popover-content'></div> \
    <nav class='popover-navigation-rtl'> \
        <div class='modal-footer'> \
            <button type='button' class='btn btn-default btn-small pull-right' data-role='prev'><< הקודם</button> \
            <button type='button' class='btn btn-default btn-small pull-left' data-role='next'> הבא >></button> \
        </div> \
    </nav> \
    </div>",
  steps: [
  {
    element:  '#tourOnClick',
    animation: true,
    title: "ברוכים הבאים!",
    placement: 'bottom',
    content: '<p>ברוכים הבאים ל-ANYWAY. על גבי המפה ניתן לראות היכן התרחשו תאונות דרכים עם נפגעים.</p>',
      onShown: function(){
          $('#step-0').find('[data-role="prev"]').prop('disabled', true);
      },
      onNext: function(){
        tourAddInput();
    }
  },
  {
    element:  '#pac-input',
    title: "חיפוש כתובת",
    animation: true,
    placement: 'bottom',
    content: '<p>כאן תוכלו להזין את כתובתכם או כתובת שאתם נוהגים לבקר בה.</p></br>'+'<p> לחיצה על ENTER תיקח אתכם אל הכתובת. לדוגמא:</br>ז\'בוטנסקי 74 פתח תקווה</p>',
    onNext: function () {
        tourClickInput();
    }
  },
        {
    element:  '#step3tour',
    title: "סינון לפי חומרה",
    placement: 'left',
    content: '<p>כאן ניתן להציג או להסתיר תאונות ברמות חומרה שונות. </br>לצורך הדוגמא נבטל את הצגתן של תאונות קלות על ידי ביטול הסימון.</br> במידה ותבחרו להציג תאונות שמיקומן מוערך שימו לב שמידת ההערכה תופיע בשדה "עיגון" בפרטי התאונה ואייקון התאונה יהיה שקוף. </p>',
    onShow: function(){
     // if ($('*[data-type="3"]').attr('data-tourClick') == "false") {
          $('*[data-type="3"]').click();
    //  }
    },
    onPrev: function(){
      //  if ($('*[data-type="3"]').attr('data-onClick') == "true") {
            $('*[data-type="3"]').click();
   //     }
        step3prev();
        $('*[data-type="3"]').click();

    }
  },
{
    element:  '#step4tour',
    title: "סינון לפי טווח תאריכים ",
    placement: 'left',
    content: '<p>כאן ניתן לבחור טווח תאריכים להצגת תאונות.</br>לנוחותכם ישנם קיצורי דרך לשנה ספציפית וכן אפשרות לבחור כל טווח תאריכים באופן ידני.</br> לצורך הדוגמא נבחר להציג תאונות מינואר 2006 עד ינואר 2014.</p>'
},
  ]});
// Initialize the tour
tour1.init();
resetTour();// Start the tour
tour.start();
function onClick(){
    if (!tour.ended()) {
        tour.end();
        if (infowindow) {
            infowindow.close();
        }
    }
    checkStepsAdd = false;
    tour.restart();
    resetTour();
    tour.start(true);
}
function resetTour(){
    tour = new Tour(tour1);
    tour.addStep(tour1.getStep(0));
    tour.addStep(tour1.getStep(1));
    tour.init();
}
function step2next() {
    infowindow.close();
    if (!checkStepsAdd) {
        //add as many steps according to mockup
        tour.addStep(tour1.getStep(2));
        tour.addStep(tour1.getStep(3));
        checkStepsAdd = true;
    }
    tour.goTo(2);
}
function step2prev() {
    infowindow.close();
    tour.goTo(1);
}
function step3prev() {
    tour.end();
    tour.restart();
    resetTour();
    checkStepsAdd = false;
    tour.goTo(1);
}
function tourAddInput() {
    var a = document.getElementById('pac-input');
    a.value = "ז'בוטנסקי 74, פתח תקווה";
}

function tourClickInput() {
    var a = document.getElementById('pac-input');
    a.value = "ז'בוטנסקי 74, פתח תקווה";
    google.maps.event.trigger(a, 'focus');
    google.maps.event.trigger(a, 'keydown', {keyCode: 13});
    tourLocation = 2;
}

