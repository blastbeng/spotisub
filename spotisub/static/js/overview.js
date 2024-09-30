$(window).scroll(function() {
    if($(window).scrollTop() == $(document).height() - $(window).height()) {

        updateData(false);
        
    }
});  

function updateData(fromFilter){
        var limit = document.getElementById("limit").value;
        var order = document.getElementById("order").value;
        var asc = document.getElementById("asc").value;
        var page = document.getElementById("page");
        var result_size = document.getElementById("result_size").value;
        var overview_url = document.getElementById("overview_url").value;

        let row_len = document.getElementById("overview_data").rows.length - 1;

        if (row_len < result_size) {

            let xhr = new XMLHttpRequest();

            page.value = parseInt(parseInt(row_len) / limit) + 1;

            let url = overview_url + page.value + "/" + limit + "/" + order + "/" + asc + "/"
            xhr.open("GET", url, true);

            xhr.onreadystatechange = function () {
                if (this.readyState == 4 && this.status == 200) {
                    var table_resp = document.createElement( 'tbody' );
                    table_resp.innerHTML = this.responseText;
                    var update = false;
                    for (var i = 0, row; row = table_resp.rows[i]; i++) {
                        var tr = $('#' + row["id"]);
                        if (tr.length == 0) {
                            //table_data.append(row);
                            var row_idx = ((parseInt(limit) * (parseInt(page.value) - 1))) + i;
                            $(row.outerHTML).insertAfter($("#overview_data > tr").eq(row_idx-1));
                            update = true;
                        }
                    }
                    if (update && fromFilter) {
                        filterOverview();
                    }
                } 
            }
            xhr.send();
        } else {
            loading_elm = document.getElementById("loading-more");
            loading_elm.style.display = "none";
        }

}



function showSort(){
    var element = document.getElementById("toolbar-root-sort");
    if ( element.classList.contains("nodisplay") ) {
        element.classList.remove("nodisplay");
    } else {
        element.classList.add("nodisplay");
    }
    hideToolbarElement("toolbar-root-view")
    hideToolbarElement("toolbar-root-filter")
}

function showView(){
    var element = document.getElementById("toolbar-root-view");
    if ( element.classList.contains("nodisplay") ) {
        element.classList.remove("nodisplay");
    } else {
        element.classList.add("nodisplay");
    }
    hideToolbarElement("toolbar-root-sort")
    hideToolbarElement("toolbar-root-filter")
}

function showFilter(){
    var element = document.getElementById("toolbar-root-filter");
    if ( element.classList.contains("nodisplay") ) {
        element.classList.remove("nodisplay");
    } else {
        element.classList.add("nodisplay");
    }
    hideToolbarElement("toolbar-root-sort")
    hideToolbarElement("toolbar-root-view")
}

function displayTable(){
    var element = document.getElementById("data");
    if ( element.classList.contains("table-card") ) {
        element.classList.remove("table-card");
    }
    if ( !element.classList.contains("table-striped") ) {
        element.classList.add("table-striped");
    } 
    hideToolbarElement("toolbar-root-view")
} 

function displayPoster(){
    var element = document.getElementById("data");
    if ( element.classList.contains("table-striped") ) {
        element.classList.remove("table-striped");
    }
    if ( !element.classList.contains("table-card") ) {
        element.classList.add("table-card");
    } 
    hideToolbarElement("toolbar-root-view")
}

function filterOverview() {
    // Declare variables
    var input, filter, table, tr, td, i, txtValue;
    input = document.getElementById("filter-overview-text");
    filter = input.value.toUpperCase();
    table = document.getElementById("overview_data");
    tr = table.getElementsByTagName("tr");
  
    // Loop through all table rows, and hide those who don't match the search query
    var hidden = false;
    for (i = 0; i < tr.length; i++) {
      td = tr[i].getElementsByTagName("td")[1];
      if (td) {
        txtValue = td.textContent || td.innerText;
        if (txtValue.toUpperCase().indexOf(filter) > -1) {
          tr[i].style.display = "";
        } else {
          tr[i].style.display = "none";
          hidden = true;
        }
      }
    }
    if (hidden) {
        updateData(hidden);
    }
}