function pollLogsJob(url){
    let xhr = new XMLHttpRequest();

    xhr.open("GET", url, true);

    xhr.onreadystatechange = function () {
        var ul = document.getElementById('output-log');
        if (this.readyState >= 3 && this.status == 200) {
            var li = document.createElement("li");
            li.appendChild(document.createTextNode(xhr.responseText));
            ul.appendChild(li);
        }
    }
    xhr.send();
}