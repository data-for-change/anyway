/**
 * Created by root on 30/04/15.
 */

var tour = new Tour({
    template: "<div class='popover tour' role='tooltip' > \
    <div class='arrow'></div>\
    <button type='button' class='close' data-role='end'><span> x </span></button> \
    <h3 class='popover-title'></h3> \
    <div class='popover-content'></div> \
    <nav class='popover-navigation-rtl'> \
        <div class='btn-group' role='group'> \
            <button class='btn btn-default' data-role='next'>הבא >></button> \
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
    onNext: function(tour){
        tourAddInput();
    }

  },
  {
    element:  '#pac-input',
    title: "חיפוש כתובת",
    animation: true,
    placement: 'bottom',
    content: '<p>כאן תוכלו להזין את כתובתכם או כתובת שאתם נוהגים לבקר בה.</p></br>'+'<p> לחיצה על ENTER תיקח אתכם אל הכתובת. לדוגמא:</br>זבוטנסקי 74 פתח תקווה</p>',
    onNext: function ()
    {
        tourClickInput();
    }
  },
]});
// Initialize the tour
tour.init();
// Start the tour
tour.start();
$("#tourOnClick").click(function(){
  tour.start();
});
var tour1 = new Tour({
    template: "<div class='popover tour' role='tooltip' > \
    <div class='arrow'></div>\
    <button type='button' class='close' data-role='end'><span> x </span></button> \
    <h3 class='popover-title'></h3> \
    <div class='popover-content'></div> \
    <nav class='popover-navigation-rtl'> \
        <div class='btn-group' role='group'> \
            <button class='btn btn-default' data-role='next'>הבא >></button> \
        </div> \
    </nav> \
    </div>",
//still at work
  steps: [
  {
    element:  $('#step2Component'),
    placement: 'left',
    title: "סינון לפי חומרה",
    content: '<p>כאן ניתן להציג או להסתיר תאונות ברמות חומרה שונות. </br>לצורך הדוגמא נבטל את הצגתן של תאונות קלות עך ידי ביטול הסימון.</br> במידה ותבחרו להציג תאונות שמיקומן מוערך שימו לב שמידת ההערכה תופיע בשדה "עיגון" בפרטי התאונה ואייקון התאונה יהיה שקוף. </p>'
  },
{
    element:  $('#step2Component'),
    title: "סינון לפי טווח תאריכים ",
    content: '<p xmlns="http://www.w3.org/1999/html">כאן ניתן לבחור טווח תאריכים להצגת תאונות.</br>לנוחותכם ישנם קיצורי דרך לשנה ספציפית וכן אפשרות לבחור כל טווח תאריכים באופן ידני.</br> לצורך הדוגמא נבחר להציג תאונות מינואר 2006 עד ינואר 2014.</p>'
  },
]})
