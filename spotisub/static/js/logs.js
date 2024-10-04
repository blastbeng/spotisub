function pollLogsJob(url){
    let xhr = new XMLHttpRequest();

    xhr.open("GET", url, true);

    xhr.onreadystatechange = function () {
        var output = document.getElementById('output-log');
        if (this.readyState == 4 && this.status == 200) {
            output.textContent = xhr.responseText;
        }
    }
    xhr.send();
}