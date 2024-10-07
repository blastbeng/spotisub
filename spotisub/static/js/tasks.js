$(document).ready(function() {
    socket.on('tasks_response', function(msg, cb) {
        msg.forEach(function(msg) { 
            var element = document.getElementById("spinner_"+msg.id);
            if (msg.running == 0 && element.classList.contains("fa-sync") ) {
                element.classList.add("fa-spinner");
                element.classList.remove("fa-sync");
            } else if (msg.running == 1 && element.classList.contains("fa-spinner") ) {
                element.classList.add("fa-sync");
                element.classList.remove("fa-spinner");
            }
        });
    });
});
