function pollPlaylistJob(url){
    let xhr = new XMLHttpRequest();

    xhr.open("GET", url, true);

    xhr.onreadystatechange = function () {
        var element = document.getElementById("rescan-button");
        if (this.readyState == 4) {
            if (this.status == 200) {
                if ( !element.classList.contains("svg-fa-spin") ) {
                    element.classList.add("svg-fa-spin");
                }
            } else if ( element.classList.contains("svg-fa-spin") ) {
                element.classList.remove("svg-fa-spin");
            }
        }
    }
    xhr.send();
}

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