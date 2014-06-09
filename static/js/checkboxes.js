var prefix = "/static/img/menu icons/";
var imgNames = [
  ["deadly-unchecked.png", "severe-unchecked.png", "medium-unchecked.png"],
  ["deadly-checked.png",   "severe-checked.png",   "medium-checked.png"],
  ["severe-hover.png",     "deadly-hover.png",     "medium-hover.png"]
];

function getImg(o, checked) {
  var dataType = o.getAttribute('data-type');
  return prefix + imgNames[checked][dataType-1];
}

function replaceCheckboxes() {
  //for (o in document.getElementsByTagName('input')) {
  var inputs = document.getElementsByTagName('input')
  for (var i=0; i<inputs.length; i++) {
    o = inputs[i];
    if (o.getAttribute('type') == 'checkbox') {
      var img = document.createElement('img');
      img.src = getImg(o, o.checked ? 1 : 0);
      img.id = 'checkboxImage'+o.id;
      img.setAttribute('onclick', 'checkboxClick("'+o.id+'")');
      img.setAttribute('onmouseover', 'checkboxMouseOver("'+o.id+'")');
      img.setAttribute('onmouseout', 'checkboxMouseOut("'+o.id+'")');
      o.parentNode.insertBefore(img, o);
      o.style.display='none';
    }
  }
}

function toggleChecked(o) {
  o.checked = o.checked ? '' : 'checked'; // empty string is equivalent to false
}

function updateImg(id, o) {
  document.getElementById('checkboxImage'+id).src = getImg(o, o.checked ? 1 : 0);
}

function checkboxClick(id) {
  o = document.getElementById(id);
  toggleChecked(o);
  updateImg(id, o);
}

function checkboxMouseOver(id) {
  o = document.getElementById(id);
  document.getElementById('checkboxImage'+id).src = getImg(o, 2);
}

function checkboxMouseOut(id) {
  updateImg(id, o);
}
