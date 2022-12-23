let serverId = null;
let itemId = null;

const fetchAutocompleteData = () => {
    fetch(
        "/api/typeahead/"
    ).then(
        (response) => response.json()
    ).then(
        (data) => initTypeahead(data)
    )
}

const selectItem = (item_id, initialLoad = false) => {
   itemId = item_id;
   console.log(itemId)


};


const init = () => {
     fetchAutocompleteData();
     const params = getParamsFromUrl();

}

window.onpopstate = function(e){
    init();
};

const setupDropdown = (triggerId) => {
    const select = document.getElementById(triggerId);
    if(!select) {
        return;
    }
    const dropdownElems = select.getElementsByClassName("navbar-dropdown")[0];
    select.onclick = () => {
        dropdownElems.classList.toggle("hidden");
        select.classList.toggle("is-active");
    }

    window.addEventListener("click", (event) => {
        const elem = event.target;
        const isChildOfSelect = elem === select || select.contains(elem);
        if(!isChildOfSelect) {
            select.classList.remove("is-active");
            dropdownElems.classList.add("hidden");
        }
    });
}

// dropdown click event listener
window.addEventListener('load', function() {
    init();
    setupDropdown("server-select")
    setupDropdown("settings")
    // setupModal("item-selection-modal-trigger", "item-selection-modal");




});

