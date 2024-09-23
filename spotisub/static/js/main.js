function searchPlaylistsResults(missing, page, limit){
    searchValue = document.getElementById('text-search').value
    if( searchValue !== undefined && searchValue !== "" ){
        this.location = "/playlists/" + missing + "/" + page + "/" + limit + "/" + searchValue + "/";
    }
}