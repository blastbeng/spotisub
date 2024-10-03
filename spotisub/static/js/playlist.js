function pollPlaylistJob(url){
    let xhr = new XMLHttpRequest();

    xhr.open("GET", url, true);

    xhr.onreadystatechange = function () {
        var element = document.getElementById("rescan-button");
        if (this.readyState == 4 && this.status == 200) {
            if ( !element.classList.contains("svg-fa-spin") ) {
                element.classList.add("svg-fa-spin");
            }
        } else if ( element.classList.contains("svg-fa-spin") ) {
            element.classList.remove("svg-fa-spin");
        }
    }
    xhr.send();
}