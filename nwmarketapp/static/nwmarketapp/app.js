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

const getParamsFromUrl = () => {
    // convert this to something more elegant as needed
    const loc = window.location;
    if(!loc.pathname) {
        return null;
    }
    const parts = loc.pathname.split("/");
    let server_id = parts.pop() || parts.pop();
    if(!server_id) {
        return null;
    } else if (server_id == "#") {
        server_id = parts.pop();
    }

    return {
        "item_id": parts.pop(),
        "server_id": server_id
    }
}

function changeServer(server_id, initialLoad=false){
    localStorage.setItem('lastServerId', server_id);
    document.getElementById("server-name").innerText = servers[server_id];
    serverId = server_id;
    fetch(`/server-price-data/${serverId}/`)
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
        const { most_listed, ...popularItemData } = data;
        top10data = most_listed;
        drawBar();
        for (const [key, value] of Object.entries(popularItemData)) {
            document.getElementById(key).innerHTML = value;
        }
    })
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
    fetch(`/price-data/${serverId}/${itemId}/`)
    .then(res => {
        return res.json();
    })
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
        create_linegraph(data["graph_data"]);
        setupModal("lowest-10-modal-trigger", "lowest-10-modal");
    })
};

const init = () => {
    const lastServerId = localStorage.getItem("lastServerId");
    document.getElementById("price-data").classList.add("hidden");
    document.getElementById("welcome-banner").classList.add("hidden");

    fetchAutocompleteData();

    const params = getParamsFromUrl();
    // first, use the server id in the url. if there's none, use the last server id the person was on. otherwise 1.
    serverId = params && params.server_id || lastServerId || 1;
    changeServer(serverId, true);
    if(params && params.item_id) {
        loadItem(params.item_id, true);
    } else {
        document.getElementById("welcome-banner").classList.remove("hidden");
    }
    document.getElementById("server-name").innerText = servers[serverId];
}

window.onpopstate = function(e){
    init();
};

// dropdown click event listener
window.addEventListener('load', function() {
    init();
    const serverSelect = document.getElementById("server-select");
    const dropdownElems = serverSelect.getElementsByClassName("navbar-dropdown")[0];
    serverSelect.onclick = () => {
        dropdownElems.classList.toggle("hidden");
        serverSelect.classList.toggle("is-active");
    }

    const settings = document.getElementById("settings");
    const settingsElems = settings.getElementsByClassName("navbar-dropdown")[0];
    settings.onclick = () => {
        settings.classList.toggle("is-active");
        settingsElems.classList.toggle("hidden");
    }

    window.addEventListener("click", (event) => {
        const elem = event.target;
        const isChildOfSettings = elem === settings || settings.contains(elem);
        if(!isChildOfSettings) {
            settings.classList.remove("is-active");
            settingsElems.classList.add("hidden");
        }

        const isChildOfServerSelect = elem === serverSelect || serverSelect.contains(elem);
        if(!isChildOfServerSelect) {
            serverSelect.classList.remove("is-active");
            dropdownElems.classList.add("hidden");
        }
    });

    setupModal("export-data-modal-trigger", "export-data-modal");
});

const setupModal = (triggerId, modalId) => {
    document.getElementById(triggerId).onclick = () => {
        const exportDataModal = document.getElementById(modalId);
        exportDataModal.classList.add("is-active");
        exportDataModal.querySelectorAll(".close-modal").forEach((elem) => {
            elem.onclick = () => {
                exportDataModal.classList.remove("is-active");
            }
        });
    }
}
