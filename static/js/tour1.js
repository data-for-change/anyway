/**
 * Created by root on 30/04/15.
 */
/**
 * Created by root on 30/04/15.
 */
var tour = new Tour({
    //storage: window.localStorage,
    //basePath: path,
    template: "<div class='popover tour'> \
    <div class='arrow'></div> \
    <h3 class='popover-title'></h3> \
    <div class='popover-content'></div> \
    <nav class='popover-navigation'> \
        <div class='btn-group'> \
            <button class='btn btn-default' data-role='Prev'>"+הקודם+"</button> \
            <button class='btn btn-default' data-role='next'>"+next+"</button> \
        </div> \
        <button class='btn btn-default' data-role='end'>"+endtour+"</button> \
    </nav> \
    </div>",
  steps: [
  {
    element:  $('#step1Component'),
    title: "Title of my step",
    content: '<p>ברוכים הבאים ל - anyway. האתר מציג נתוני תאונות לפי מיקום.</p>'
  },
  {
    element:  $('#step2Component'),
    title: "Title of my step2",
    content: '<p>ברוכים הבאים ל - anyway. האתר מציג נתוני תאונות לפי מיקום.</p>'
  }
]});
// Initialize the tour
tour.init();
// Start the tour
tour.start();
