/**
 * Created by root on 30/04/15.
 */

var infowindow,checkStepsAdd = false,checkStepsAdd2 = false, tourLocation = 0,stepId,iwOuter,iwBackground,iwCloseBtn;
var tour1 = new Tour({
    storage: window.localStorage,
    template: "<div class='popover tour' role='tooltip' > \
    <div class='arrow'></div>\
    <button type='button' class='close' data-role='end'> ×</button> \
    <h3 class='popover-title'></h3> \
    <div class='popover-content'></div> \
    <nav class='popover-navigation'> \
        <div class='btn-group center-block'> \
            <button type='button' class='btn btn-default' data-role='prev'><< הקודם</button> \
            <button type='button' class='btn btn-default' data-role='next'> הבא >></button> \
        </div> \
    </nav> \
    </div>",
    steps: [
        {
            element:  '#tour-control',
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
                stepId = 'step-2';
                tourClickInput();
            }
        },
        {
            element:  '#step3tour',
            title: "סינון לפי חומרה",
            placement: 'left',
            content: '<p>כאן ניתן להציג או להסתיר תאונות ברמות חומרה שונות. </br>לצורך הדוגמא נבטל את הצגתן של תאונות קלות על ידי ביטול הסימון.</br> במידה ותבחרו להציג תאונות שמיקומן מוערך שימו לב שמידת ההערכה תופיע בשדה "עיגון" בפרטי התאונה ואייקון התאונה יהיה שקוף. </p>',
            onPrev: function(){
                $('*[data-type="3"]').click();
                step3prev();
            },
            onNext: function(){
                tourLocation = 3;
            }
        },
        {
            element:  '#step4tour',
            title: "סינון לפי טווח תאריכים ",
            placement: 'left',
            content: '<p>כאן ניתן לבחור טווח תאריכים להצגת תאונות.</br>לנוחותכם ישנם קיצורי דרך לשנה ספציפית וכן אפשרות לבחור כל טווח תאריכים באופן ידני.</br> לצורך הדוגמא נבחר להציג תאונות מינואר 2006 עד ינואר 2014.</p>',
            onNext: function(){
                tour4next();
            }
        },
        {
            element:  '#step6tour',
            title: "רשימת התאונות המוצגות על המפה",
            placement: 'left',
            content: '<p>כאן תתעדכן רשימת המצגות על גבי המפה לפי תאריך בסדר יורד, מעבר על פריט ברשימה תקפיץ אותו על המפה, ולחיצה תפתח את פרטיו על גבי המפה.</p>',
            onPrev: function(){
                tour6prev();
            }
        },{
            element:  '#js-embed-link',
            title: "קישור לתצוגה הנוכחית",
            placement: 'bottom',
            content: '<p>כאן תתעדכן רשימת המצגות על גבי המפה לפי תאריך בסדר יורד, מעבר על פריט ברשימה תקפיץ אותו על המפה, ולחיצה תפתח את פרטיו על גבי המפה.</p>'
        },
    ]});
// Initialize the tour

function tourClick(){
    tour1.init();
    resetTour();// Start the tour
    tour.addStep(tour1.getStep(0));
    tour.addStep(tour1.getStep(1));
    tour.init();
    tour.start();
    if (!tour.ended()) {
        tour.end();
        if (infowindow) {
            infowindow.close();
        }
    }
    checkStepsAdd = false;
    checkStepsAdd2 = false;
    resetTour();
    tour.addStep(tour1.getStep(0));
    tour.addStep(tour1.getStep(1));
    tour.init();
    tour.restart();
}
function resetTour(){
    tourLocation = 0;
    tour = new Tour(tour1);
}
function step2next() {
    infowindow.close();
    //console.log("Next click infoWindow = "+tourLocation);
    restInfoWindow(iwOuter,iwBackground,iwCloseBtn);
    if (tourLocation != 5 && tourLocation != 6){
        if (checkStepsAdd) {
            for (i = 0; i < 4; i++) {
                tour.addStep(tour1.getStep(i));
            }
            tour.init();
            tour.restart();
        }
        else  {
            tour.addStep(tour1.getStep(2));
            tour.addStep(tour1.getStep(3));
            checkStepsAdd = true;
        }
        tour.goTo(2);
        $('*[data-type="3"]').click();
    }
    else{
        if (checkStepsAdd2) {
            for (i = 0; i < 6; i++) {
                tour.addStep(tour1.getStep(i));
            }
            tour.init();
            tour.restart();
        }
        else{
            tour.addStep(tour1.getStep(4));
            tour.addStep(tour1.getStep(5));
            checkStepsAdd2 = true;
        }
        tour.goTo(4);
    }
}
function step2prev() {
    infowindow.close();
    resetTour();
    restInfoWindow(iwOuter,iwBackground,iwCloseBtn);
    if(stepId == 'step-2'){
        tour.addStep(tour1.getStep(0));
        tour.addStep(tour1.getStep(1));
        tour.init();
        tour.restart();
        checkStepsAdd = false;
        tour.goTo(1);
    }
    if(stepId == 'step-5'){
        stepId = 'step-2';

        tour.init();
        tour.restart();
        checkStepsAdd2 = false;
        tour.goTo(3);
    }
}
function step3prev() {
    tour.end();
    resetTour();
    tourClickInput();
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
    if( tourLocation != 5) {
        tourLocation = 2;
    }
}
function tour4next(){
    stepId = 'step-5';
    tourLocation = 5;
    console.log("inside tour"+tourLocation);
    tourClickInput();
}
function tour6prev(){
    tour.end();
    resetTour();
    stepId = 'step-5';
    tourLocation = 5;
    console.log("inside tour"+tourLocation);
    tourClickInput();
}
function defInfoWindows(){
    htmlTourString =
                '<div class ="iw-container" id='+stepId+'>'+
                    '<h3 class="popover-title" id="tourInfoWindow">'+titleString+'</h3>'+
                    '<div class="popover-content scrollFix">'+contentString+'</div>'+
                    '<nav class="popover-navigation">'+
                        '<div class="btn-group" role="group">'+
                            '<button onclick="step2prev()" class="btn btn-default" data-role="prev"><< הקודם'+'</button>'+
                            '<button onclick="step2next()" class="btn btn-default" data-role="next">הבא >>'+'</button>'+
                        '</div>'+
                    '</nav>'+
                '</div>'+
        '</div>';
}
// style for tourInfoWindow
function tourStyle(infowindow){
    google.maps.event.addListener(infowindow, 'domready', function() {
        $('#tourInfoWindow').parent().parent().parent().parent().attr('class', 'gm-style-iwtour');
        iwOuter = $('.gm-style-iwtour');
        console.log(iwOuter.attr('class'));
        iwBackground = iwOuter.prev();
        iwBackground.children(':nth-child(2)').css({'display' : 'none'});
        iwBackground.children(':nth-child(4)').css({'display' : 'none'});
        iwBackground.children(':nth-child(3)').find('div').children().css({'box-shadow': '0.5px 0.5px 0.5px 1px #bbbbbb;', 'z-index' : '1'});
        iwCloseBtn = iwOuter.next();
        iwCloseBtn.css({
            opacity: '0.3', // by default the close button has an opacity of 0.7
            left: '55px', top: '20px', // button repositioning
        });
        iwCloseBtn.mouseover(function(){
            $(this).css({opacity: '0.5'});
        });
        iwCloseBtn.mouseout(function(){
            $(this).css({opacity: '0.3'});
        });
    });
}
function restInfoWindow(iwOuter,iwBackground,iwCloseBtn){
    iwOuter.attr("class","gm-style-iw");
    iwBackground.children(':nth-child(2)').css({'display' : 'inline'});
    iwBackground.children(':nth-child(4)').css({'display' : 'inline'});
    iwCloseBtn.css({
        opacity: '0.7', // by default the close button has an opacity of 0.7
        left: '10px', top: '10px', // button repositioning
    });
    iwCloseBtn.mouseover(function(){
        $(this).css({opacity: '0.8'});
    });
    iwCloseBtn.mouseout(function(){
        $(this).css({opacity: '0.7'});
    });
}

