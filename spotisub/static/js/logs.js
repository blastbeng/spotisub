$(document).ready(function() {
    window.addEventListener('resize', function(event){
        var msgdiv = document.getElementById('output-log-div');
        msgdiv.scrollIntoView(false);
        var header_baseh = $("#header-base").height();
        var height_def = $(window).height() - header_baseh;
        msgdiv.style.height = height_def + "px";
        msgdiv.scrollTop = msgdiv.scrollHeight;
    });

    var msgdiv = document.getElementById('output-log-div');
    msgdiv.scrollIntoView(false);
    var header_baseh = $("#header-base").height();
    var height_def = $(window).height() - header_baseh;
    msgdiv.style.height = height_def + "px";
    msgdiv.scrollTop = msgdiv.scrollHeight;
    socket.on('log_response', function(msg, cb) {
        if (msg.status == 1) {
            var ul = document.getElementById('output-log');
            var li = document.createElement("li");
            li.appendChild(document.createTextNode(msg.data));
            ul.appendChild(li);
            var msgdiv = document.getElementById('output-log-div');
            msgdiv.scrollTop = msgdiv.scrollHeight;
        } 
    });
});