$(document).ready(function() {
    // Function to detect log level from log message
    function getLogLevel(logMessage) {
        // Check for log level keywords at the start or after timestamp
        if (logMessage.includes(' ERROR ')) {
            return 'error';
        } else if (logMessage.includes(' WARNING ') || logMessage.includes(' WARN ')) {
            return 'warning';
        } else if (logMessage.includes(' INFO ')) {
            return 'info';
        } else if (logMessage.includes(' DEBUG ')) {
            return 'debug';
        }
        return 'default';
    }
    
    // Function to get CSS class for log level
    function getLogClass(logLevel) {
        switch(logLevel) {
            case 'error':
                return 'log-error';
            case 'warning':
                return 'log-warning';
            case 'info':
                return 'log-info';
            case 'debug':
                return 'log-debug';
            default:
                return 'log-default';
        }
    }
    
    // Function to create and add log entry
    function addLogEntry(logMessage) {
        var ul = document.getElementById('output-log');
        var li = document.createElement("li");
        var logLevel = getLogLevel(logMessage);
        var logClass = getLogClass(logLevel);
        
        li.className = logClass;
        li.appendChild(document.createTextNode(logMessage));
        ul.appendChild(li);
        
        var msgdiv = document.getElementById('output-log-div');
        msgdiv.scrollTop = msgdiv.scrollHeight;
    }
    
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
    
    // Apply log classes to existing log entries on page load
    var logList = document.getElementById('output-log');
    if (logList) {
        var listItems = logList.getElementsByTagName('li');
        for (var i = 0; i < listItems.length; i++) {
            var logMessage = listItems[i].textContent;
            var logLevel = getLogLevel(logMessage);
            var logClass = getLogClass(logLevel);
            listItems[i].className = logClass;
        }
    }
    
    socket.on('log_response', function(msg, cb) {
        if (msg.status == 1) {
            addLogEntry(msg.data);
        } 
    });
});