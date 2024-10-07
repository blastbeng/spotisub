$(document).ready(function() {
    socket.on('playlist_response', function(msg, cb) {
        var playlist_info_uuid = document.getElementById("playlist_info_uuid").value;
        var element = document.getElementById("rescan-button");
        if (msg.status == 1) {
            var found = false;
            for(let i = 0; i < msg.uuids.length; i++) {
                if (msg.status == 1 && playlist_info_uuid == msg.uuids[i]) {
                    found = true;
                    break
                }
            }
            if (found && !element.classList.contains("svg-fa-spin") ) {
                element.classList.add("svg-fa-spin");
            } else if ( !found && !element.classList.contains("svg-fa-spin") ) {
                element.classList.remove("svg-fa-spin");
            }
        } else if ( element.classList.contains("svg-fa-spin") ) {
            element.classList.remove("svg-fa-spin");
        }
    });
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