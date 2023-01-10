max_tracked_num = 6

const fetchAutocompleteData = () => {
    fetch(
        "/api/typeahead/"
    ).then(
        (response) => response.json()
    ).then(
        (data) => initTypeahead(data)
    )
}

const saveTrackedItems = () => {

    const form = document.getElementById("tracked-items-form");
    const csrftoken = form.querySelector("[name=csrfmiddlewaretoken]").value;

    const selectedItemIds = selectedItems.map(item => item.itemId);

    const body = JSON.stringify({
        'server_id': serverId,
        'item_ids': selectedItemIds
    })

    nwmpRequest("/mw/tracked_items_save/", "POST", {
            credentials: 'same-origin',
            body: body,
            headers: {
                "X-CSRFToken": csrftoken,
                'Content-Type': 'application/json'
            },
      }).then((data) => {
            loadTrackedItems(serverId)
            if(data["status"] == "failed") {
                const content = data["errors"].join("<br><br>")
                createNotification(content, "danger");
            } else {
                createNotification("Items updated successfully.", "success");

            }
      }).catch((err) => {
          console.log('fail', data)
          createNotification("Items update failed.", "danger");
      })

}


window.onpopstate = function(e){
    init();
};

const init = () => {
     const lastServerId = localStorage.getItem("lastServerId");
     document.getElementById("item-tracking").classList.add("hidden");

     fetchAutocompleteData();


     //get server_id from URL
     const loc = window.location;
     let serverFromURL
     if(!loc.pathname) {
         serverFromURL =  null;
     } else {
         const parts = loc.pathname.split("/");
         serverFromURL = parts[3]

         if (!serverFromURL) {
             serverFromURL = null;
         }
     }
     serverId = serverFromURL || lastServerId || 2;
     changeServer(serverId);
     let server_health = '<span class="' + servers[serverId]['health'] + '"></span>&nbsp;'
     document.getElementById("server-name").innerHTML = server_health +  servers[serverId]['name'];
     document.title = 'New World Market Prices - Dashboard - ' + servers[serverId]['name'];

}

window.onpopstate = function(e){
    init();
};

const loadTrackedItems = (serverId) => {
    document.getElementById("item-selection-link").classList.add("hidden");
    document.getElementById("item-tracking").classList.add("hidden");
    document.getElementById("loading-message").classList.remove("hidden");
     nwmpRequest(`/mw/dashboard_items/${serverId}/`)
    .then(data => {

        document.getElementById("welcome-banner").classList.add("hidden");
        document.getElementById("item-tracking").classList.remove("hidden");

        const elem = document.getElementById("tracked-items");
        elem.innerHTML = data["item_data"];
        for (let i = 0; i < data["mini_graph_data"].length; i++){
            let obj =  data["mini_graph_data"][i]

            if(obj.graph_data == null){
                   document.getElementById('chart-' + obj.item_id).innerHTML = 'No prices found'
            }else {
                create_mini_graph(eval(obj.graph_data), 'chart-' + obj.item_id)
            }

        }
        selectedItems = []
        for (let i = 0; i < data["mini_graph_data"].length; i++){
            let obj =  data["mini_graph_data"][i]
            selectedItems.push({'itemId': obj.item_id, 'itemName': obj.item_name})
        }
        max_tracked_num = data['max_tracked_num']
        populateSelectedItems()



    }).catch((data) => {

         max_tracked_num = data['max_tracked_num']
         populateSelectedItems()

         if(data['status'] == 'Not logged in'){
             //not logged in
            document.getElementById("welcome-banner").classList.remove("hidden");
            document.getElementById("loading-message").classList.add("hidden");
            document.getElementById("item-tracking").classList.add("hidden");
            document.getElementById("not-loggedin-message").classList.remove("hidden");


         }else {
             // no tracked items found for this server
             document.getElementById("welcome-banner").classList.remove("hidden");
             document.getElementById("loading-message").classList.add("hidden");
             document.getElementById("item-selection-link").classList.remove("hidden");
             document.getElementById("item-tracking").classList.add("hidden");
         }
    })

}

function changeServer(server_id){
    localStorage.setItem('lastServerId', server_id);
    let server_health = '<span class="' + servers[server_id]['health'] + '"></span>&nbsp;'
    document.getElementById("server-name").innerHTML = server_health + servers[server_id]['name'];
    document.getElementById("server-timestamp").innerHTML =  'Updated ' + servers[server_id]['last_scanned']
    let linkItem = document.getElementById('dashboard-link')
    if (linkItem) {
       linkItem.href = '/mw/dashboard/' + server_id
    }

    serverId = server_id;
    loadTrackedItems(serverId)
    // populateSelectedItems()

    window.history.pushState({
            serverId: serverId,
        }, "New World Market Prices", `/mw/dashboard/${serverId}`)
    loadPriceChanges(serverId)
    loadRareItems(serverId)
    loadTopSold(serverId)
    document.title = 'New World Market Prices - Dashboard - ' + servers[serverId]['name'];
}

const populateSelectedItems = () => {


    selectedItems.splice(max_tracked_num, selectedItems.length)

    const parent = document.getElementsByClassName('tracked-item-selection')
    for (let i = 0; i < parent.length; i++) {

        if(selectedItems.length > i){

            let item = selectedItems[i]
            let itemVal = `<span class="is-size-6">${item['itemName']}</span><button class="delete is-medium" id="delete-${item['itemId']}"></button>`
            parent[i].innerHTML = itemVal

        }else{
            if (i > (max_tracked_num-1)){
                parent[i].innerHTML = ' <img class="lock-icon" src="/static/nwmarketapp/lock_icon.png"><span style=\"color: rgba(255, 255, 255, 0.2);\">[Locked]</span>'
            }else {
                parent[i].innerHTML = '<span style=\"color: rgba(255, 255, 255, 0.2);\">[Empty]</span>'
            }
        }
    }
    const deleteBtns = document.getElementsByClassName('delete')
    for (let i = 0; i < deleteBtns.length; i++) {

        deleteBtns[i].onclick = () => {
            let btnId = deleteBtns[i].id
            removeItem(btnId.slice(7))
        }
    }



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
    let sections = ['price_drops', 'price_increases']
    for (let x = 0; x < sections.length; x++) {
        let phId = sections[x] + '-ph'
        let tableId = sections[x] + '-table'
        document.getElementById(phId).style.display = 'block'
        document.getElementById(tableId).innerHTML = '';


    }
    nwmpRequest(`/mw/price_changes/${serverId}`)
        .then(data => {

            for (let x = 0; x < sections.length; x++) {

                for (let i = 0; i < data[sections[x]].length; i++) {
                    let obj = data[sections[x]][i]

                    let row = document.createElement("tr");

                    let nameCell = document.createElement("td");
                    let priceCell = document.createElement("td");
                    let changeCell = document.createElement("td");
                    let avgCell = document.createElement("td");


                    let item_id = obj.item_id
                    nameCell.innerHTML = `<a onclick="loadGraphModal(${serverId}, ${item_id});return false;">` + obj.item_name + "</a>";
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
                let phId = sections[x] + '-ph'
                document.getElementById(phId).style.display = 'none'
            }


        }).catch((data) => {

        console.log(data);
        // createNotification(data['status'], "danger")
        if (data['status'] == 'No recent scans from user') {
            //rare items lock
            let tableId = 'rare_items-table'
            document.getElementById(tableId).innerHTML = '';
            let phId = 'rare_items-ph'
            document.getElementById(phId).style.display = 'none'
            //price changes lock
            for (let x = 0; x < sections.length; x++) {
                let phId = sections[x] + '-ph'
                let tableId = sections[x] + '-table'
                document.getElementById(phId).style.display = 'none'
                document.getElementById(tableId).innerHTML = '';
                document.getElementsByClassName('locked-item')
                let lockItems = document.getElementsByClassName('locked-item')
                for (let i = 0; i < lockItems.length; i++) {
                    lockItems[i].classList.remove("hidden");
                }
            }
            sections = ['top_sold_items_allservers', 'top_sold_items_currentserver']
            //sold items lock
            for (let x = 0; x < sections.length; x++) {
                let phId = sections[x] + '-ph'
                let tableId = sections[x] + '-table'
                document.getElementById(phId).style.display = 'none'
                document.getElementById(tableId).innerHTML = '';
                document.getElementsByClassName('locked-item')
                let lockItems = document.getElementsByClassName('locked-item')
                for (let i = 0; i < lockItems.length; i++) {
                    lockItems[i].classList.remove("hidden");
                }
            }

        }
    })
}
const loadRareItems = (serverId) => {

    let tableId = 'rare_items-table'
    document.getElementById(tableId).innerHTML = '';
    let phId = 'rare_items-ph'
    document.getElementById(phId).style.display='block'
    nwmpRequest(`/mw/rare_items/${serverId}`)
    .then(data => {

        for (let i = 0; i < data['rare_items'].length; i++){
             let obj = data['rare_items'][i]

              let row = document.createElement("tr");

              let nameCell = document.createElement("td");
              let priceCell = document.createElement("td");
              let lastseenCell = document.createElement("td");


              let item_id = obj.item_id
              nameCell.innerHTML = `<a onclick="loadGraphModal(${serverId}, ${item_id});return false;">` + obj.item_name + "</a>";
              priceCell.innerHTML = obj.price;
              lastseenCell.innerHTML = obj.last_seen + ' days ago';

              // Append the cells to the row
              row.appendChild(nameCell);
              row.appendChild(priceCell);
              row.appendChild(lastseenCell);

              let tableId = 'rare_items-table'

              document.getElementById(tableId).appendChild(row);

        }
        let phId = 'rare_items-ph'
        document.getElementById(phId).style.display='none'





    }).catch((data) => {

        console.log(data);
        // createNotification(data['status'], "danger")
    })
}
const loadTopSold = (serverId) => {
    // set up tab functionality
    document.querySelectorAll('.tabs').forEach((tab)=>{
    tab.querySelectorAll('li').forEach((li)=>{
      li.onclick = () => {
          tab.querySelector('li.is-active').classList.remove('is-active')
          li.classList.add('is-active')
          tab.nextElementSibling.querySelector('.tab-pane.is-active').classList.remove('is-active')
          tab.nextElementSibling.querySelector('.tab-pane#'+li.firstElementChild.getAttribute('id'))
            .classList.add("is-active")
      }
    })
  })
  // get data
    let sections = ['top_sold_items_allservers', 'top_sold_items_currentserver']
    for (let x = 0; x < sections.length; x++) {
        let phId = sections[x] + '-ph'
        let tableId = sections[x] + '-table'
        document.getElementById(phId).style.display='block'
        document.getElementById(tableId).innerHTML = '';

    }


   nwmpRequest(`/mw/top_sold_items/${serverId}`)
    .then(data => {

        for (let x = 0; x < sections.length; x++){

            for (let i = 0; i < data[sections[x]].length; i++){
                 let obj = data[sections[x]][i]

                  let row = document.createElement("tr");

                  let nameCell = document.createElement("td");
                  let priceCell = document.createElement("td");
                  let qtyCell = document.createElement("td");
                  let totalCell = document.createElement("td");


                  let item_id = obj.ItemId
                  nameCell.innerHTML = `<a onclick="loadGraphModal(${serverId}, ${item_id});return false;">` + obj.ItemName + "</a>";
                  priceCell.innerHTML = obj.AvgPrice;
                  qtyCell.innerHTML = obj.AvgQty;
                  totalCell.innerHTML = obj.Total;

                  // Append the cells to the row
                  row.appendChild(nameCell);
                  row.appendChild(priceCell);
                  row.appendChild(qtyCell);
                  row.appendChild(totalCell);
                  let tableId = sections[x] + '-table'

                  document.getElementById(tableId).appendChild(row);

            }
            let phId = sections[x] + '-ph'
            document.getElementById(phId).style.display='none'
        }




    }).catch((data) => {

        console.log(data);
         // createNotification(data['status'], "danger");

    })

}

const loadGraphModal = (serverId, itemId) => {
     nwmpRequest(`/api/price-data/${serverId}/${itemId}`)
    .then(data => {
       create_linegraph(data["graph_data"],'dashboard-graph-modal-chart');
       const DataModal = document.getElementById('dashboard-graph-modal');
       const modalTitle = document.getElementById('graph-modal-title');
       let item_url = '/' + data['item_id'] + '/' + serverId
       modalTitle.innerHTML = `<a href='${item_url}'>` + data['item_name'] + '</a>'
       // modalTitle.innerHTML = data['item_name']
       DataModal.classList.add("is-active");


        DataModal.querySelectorAll(".close-modal").forEach((elem) => {

            elem.onclick = () => {
                DataModal.classList.remove("is-active");
            }

        });



    }).catch((data) => {
        console.log('GraphOverlay fail',data);
        createNotification(data['status'], "danger");

    })

}


window.addEventListener('load', function() {
    init();
    setupDropdown("server-select")
    setupDropdown("settings")
    setupModal("item-selection-modal-trigger", "item-selection-modal");
    setupModal("item-selection-modal-trigger2", "item-selection-modal");





});


