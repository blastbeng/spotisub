var socket = null;
$(document).ready(function() {
    socket = io();
});
    
function searchPlaylistsResults(missing, page, limit){
    searchValue = document.getElementById('text-search').value
    if( searchValue !== undefined && searchValue !== "" ){
        this.location = "/playlists/" + missing + "/" + page + "/" + limit + "/spotify_song.title/1/" + searchValue + "/";
    }
}

function keypressPlaylistsResults(event, missing, page, limit){
    if(event.keyCode === 13){
        event.preventDefault();
        searchPlaylistsResults(missing, page, limit);
    }
}

function gotoArtist(hiddenId){
    uuid = document.getElementById(hiddenId).value
    if( uuid !== undefined && uuid !== "" ){
        this.location = "/artist/" + uuid.trim() + "/";
    }
}

function hideToolbarElement(element_id) {
    var element = document.getElementById(element_id);
    if ( !element.classList.contains("nodisplay") ) {
        element.classList.add("nodisplay");
    }
}

function showSort(){
    var element = document.getElementById("toolbar-root-sort");
    if ( element.classList.contains("nodisplay") ) {
        element.classList.remove("nodisplay");
    } else {
        element.classList.add("nodisplay");
    }
}

function callUrlAndReload(url){
    let xhr = new XMLHttpRequest();

    xhr.open("GET", url, true);

    xhr.onreadystatechange = function () {
        if (this.readyState == 4 && this.status == 200) {
            location.reload();
        }
    }
    xhr.send();
}

function callUrl(url){
    let xhr = new XMLHttpRequest();

    xhr.open("GET", url, true);
    xhr.send();
}



window.addEventListener('click', function(e){
  if (e.target.id !== 'show-toolbar-popup' && e.target.id !== 'rescan-button') {
    var element1 = document.getElementById("toolbar-root-sort");
    if (element1 != null && element1 !== 'undefined' && !element1.contains(e.target) && !element1.classList.contains("nodisplay") ) {
        element1.classList.add("nodisplay");
    } 
    var element2 = document.getElementById("toolbar-root-view");
    if (element2 != null && element2 !== 'undefined' && !element2.contains(e.target) && !element2.classList.contains("nodisplay") ) {
        element2.classList.add("nodisplay");
    } 
    var element3 = document.getElementById("toolbar-root-filter");
    if (element3 != null && element3 !== 'undefined' && !element3.contains(e.target) && !element3.classList.contains("nodisplay") ) {
        element3.classList.add("nodisplay");
    } 
    var element4 = document.getElementById("toolbar-root-rescan");
    if (element4 != null && element4 !== 'undefined' && !element4.contains(e.target) && !element4.classList.contains("nodisplay") ) {
        element4.classList.add("nodisplay");
    } 
        
    }
});

function showRescanAlert(){
    var element = document.getElementById("toolbar-root-rescan");
    if ( element.classList.contains("nodisplay") ) {
        element.classList.remove("nodisplay");
    } else {
        element.classList.add("nodisplay");
    }
    hideToolbarElement("toolbar-root-sort")
}

function closeRescanAlert(){
    var element = document.getElementById("toolbar-root-rescan");
    if ( !element.classList.contains("nodisplay") ) {
        element.classList.add("nodisplay");
    }
    hideToolbarElement("toolbar-root-sort")
}