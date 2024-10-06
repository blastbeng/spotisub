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

            let old_page_value = parseInt(page.value);
            let new_page_value = parseInt((parseInt(row_len)+1) / limit) + 1;

            if (old_page_value != new_page_value){

                page.value = new_page_value;

                let url = overview_url + new_page_value + "/" + limit + "/" + order + "/" + asc + "/"
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
                        } else if($(window).scrollTop() == $(document).height() - $(window).height()) {
                            updateData(false);
                        }
                    } 
                }
                xhr.send();
            }
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
    hide_empty = document.getElementById("hide-empty-overview-check");
    select = document.getElementById("filter-type-overview-select");
    filter_type = select.value.toUpperCase();
    filter = input.value.toUpperCase();
    table = document.getElementById("overview_data");
    tr = table.getElementsByTagName("tr");
  
    // Loop through all table rows, and hide those who don't match the search query
    var hidden = false;
    for (i = 0; i < tr.length; i++) {
        var hide_text = false;
        var hide_progress = false;
        for (j = 0; j < tr[i].children.length; j++) {
            var td = tr[i].children[j]
            if (td.id == "table-href") {
                txtValue = td.textContent || td.innerText;
                if (txtValue.toUpperCase().indexOf(filter) > -1) {
                    hide_text = false;
                } else {
                    hide_text = true;
                }
            }
            if (td.id == "table-type") {
                txtValue = td.textContent || td.innerText;
                if (txtValue.toUpperCase().indexOf(filter_type) > -1) {
                    hide_type = false;
                } else {
                    hide_type = true;
                }
            }
            if (td.id == "table-progress") {
                if (td.children != null && td.children != 'undefined' && td.children.item.length > 0){
                    if (td.children[0] != null && td.children[0] !== 'undefined' && td.children[0].children != null && td.children[0].children !== 'undefined' && td.children[0].children.length > 0){
                        var progress_bar = td.children[0].children[1]
                        txtValue = td.textContent || td.innerText;
                        if (progress_bar.value == 0) {
                            if (hide_empty.checked) {
                                hide_progress = true;
                            } else if (!hide_empty.checked){
                                hide_progress = false;
                            }
                        }
                    }
                }
            }
        }
        if (hide_progress || hide_text || hide_type) {
            tr[i].style.display = "none";
            hidden = true;
        } else if(!hide_progress && !hide_text && !hide_type) {
            tr[i].style.display = "";
        }
    }
    if (hidden) {
        updateData(hidden);
    }
}

function resetFilters(){
    input = document.getElementById("filter-overview-text");
    input.value = "";
    hide_empty = document.getElementById("hide-empty-overview-check");
    hide_empty.checked = true;
    hide_empty = document.getElementById("filter-type-overview-select");
    hide_empty.value = "";
    filterOverview();
}

function pollOverviewJob(url){
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