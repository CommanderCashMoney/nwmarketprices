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

function changeServer(server_id, initialLoad=false){
    localStorage.setItem('lastServerId', server_id);
    let server_health = '<span class="' + servers[server_id]['health'] + '"></span>&nbsp;'
    document.getElementById("server-name").innerHTML = server_health + servers[server_id]['name'];
    document.querySelectorAll('.export-data-modal-url').forEach((download_link)=>{
        download_link.href = `/api/latest-prices/${server_id}/`;

    });
    document.getElementById('dashboard-link').href= '/mw/dashboard/' + server_id


    serverId = server_id;
    fetch(`/api/server-price-data/${serverId}/`)
    .then(res => {
        return res.json();
    })
    .then(data => {
        if(!initialLoad) {
            window.history.pushState({
                serverId: serverId,
                itemId: itemId
            }, "New World Market Prices", `/${itemId}/${serverId}`)
            loadItem(itemId, false)
        }
        const { most_listed, fetch_time, ...popularItemData } = data;
        top10data = most_listed;
        drawBar();
        for (const [key, value] of Object.entries(popularItemData)) {
            document.getElementById(key).innerHTML = value;
        }
    })
    document.title = 'New World Market Prices - ' + servers[serverId]['name'];
}

const loadItem = (item_id, initialLoad = false) => {
    itemId = item_id;
    if(item_id == null) {
        window.history.pushState({
            serverId: serverId,
            itemId: itemId
        }, "New World Market Prices", `/${serverId}`)
        return;
    }
    nwmpRequest(`/api/price-data/${serverId}/${itemId}/`)
    .then(data => {
        if(!initialLoad) {
            window.history.pushState({
                serverId: serverId,
                itemId: itemId
            }, "New World Market Prices", `/${itemId}/${serverId}`)
        }
        document.getElementById("item-search").value = data["item_name"];
        document.getElementById("price-data").classList.remove("hidden");
        document.getElementById("welcome-banner").classList.add("hidden");
        const elem = document.getElementById("lowest-price-data");
        elem.innerHTML = data["lowest_price"];
        create_linegraph(data["graph_data"],'line-graph-container');
        setupModal("lowest-10-modal-trigger", "lowest-10-modal");
    }).catch((data) => {

        console.log(data);
        createNotification(data['status'], "danger")
    })
    $('html, body').animate({ scrollTop: 0 }, 'fast');
};

const init = () => {
    const lastServerId = localStorage.getItem("lastServerId");
    document.getElementById("price-data").classList.add("hidden");
    document.getElementById("welcome-banner").classList.add("hidden");

    fetchAutocompleteData();

    const params = getParamsFromUrl();
    // first, use the server id in the url. if there's none, use the last server id the person was on. otherwise 2.
    serverId = params && params.server_id || lastServerId || 2;
    changeServer(serverId, true);
    if(params && params.item_id) {
        loadItem(params.item_id, true);
    } else {
        document.getElementById("welcome-banner").classList.remove("hidden");
    }
    let server_health = '<span class="' + servers[serverId]['health'] + '"></span>&nbsp;'
    document.getElementById("server-name").innerHTML = server_health +  servers[serverId]['name'];
    document.title = 'New World Market Prices - ' + servers[serverId]['name'];
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
    setupDropdown("server-select");
    setupDropdown("settings");
    setupModal("export-data-modal-trigger", "export-data-modal");
    setupTabs();
});
