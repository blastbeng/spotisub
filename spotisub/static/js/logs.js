$(document).ready(function() {
    socket.on('log_response', function(msg, cb) {
        if (msg.status == 1) {
            var ul = document.getElementById('output-log');
            var li = document.createElement("li");
            li.appendChild(document.createTextNode(msg.data));
            ul.appendChild(li);
        } 
    });
});