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
