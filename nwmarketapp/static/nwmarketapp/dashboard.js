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
const loadPriceChanges = (serverId) => {
    serverId = 2
    nwmpRequest(`/mw/price_changes/${serverId}`)
    .then(data => {
        let sections = ['price_drops', 'price_increases']
        for (let x = 0; x < sections.length; x++){

            for (let i = 0; i < data[sections[x]].length; i++){
                 let obj = data[sections[x]][i]

                  let row = document.createElement("tr");

                  let nameCell = document.createElement("td");
                  let priceCell = document.createElement("td");
                  let changeCell = document.createElement("td");
                  let avgCell = document.createElement("td");


                  let item_url = '/' + obj.item_id + '/' + serverId
                  nameCell.innerHTML = `<a href='${item_url}'>` + obj.item_name + "</a>";
                  priceCell.innerHTML = obj.price;
                  changeCell.innerHTML = obj.price_change + '%';
                  avgCell.innerHTML = obj.vs_avg + '%';

                  // Append the cells to the row
                  row.appendChild(nameCell);
                  row.appendChild(priceCell);
                  row.appendChild(changeCell);
                  row.appendChild(avgCell);
                  let tableId = sections[x] + '-table'

                  document.getElementById(tableId).appendChild(row);

            }
        }




    }).catch((data) => {

        console.log(data);
        createNotification(data['status'], "danger")
    })
}

// dropdown click event listener
window.addEventListener('load', function() {
    init();
    setupDropdown("server-select")
    setupDropdown("settings")
    loadPriceChanges(2)
    // setupModal("item-selection-modal-trigger", "item-selection-modal");




});

