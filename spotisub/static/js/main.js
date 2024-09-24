function searchPlaylistsResults(missing, page, limit){
    searchValue = document.getElementById('text-search').value
    if( searchValue !== undefined && searchValue !== "" ){
        this.location = "/playlists/" + missing + "/" + page + "/" + limit + "/" + searchValue + "/";
    }
}

function gotoArtist(hiddenId){
    uuid = document.getElementById(hiddenId).value
    if( uuid !== undefined && uuid !== "" ){
        this.location = "/artist/" + uuid.trim() + "/";
    }
}