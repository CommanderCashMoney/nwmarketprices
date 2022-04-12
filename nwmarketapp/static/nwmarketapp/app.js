let serverId = null;
let itemId = null;

const initTypeahead = () => {
    $.typeahead({
        input: '.item-search',
        order: "asc",
        display: "name",


        source: {
             data: ["aaaa"]

        },
        callback: {
            onInit: function (node) {
                console.log('Typeahead Initiated on ' + node.selector);
            },
            onClickAfter: function(node, a, item, event){

                var cn_id = item.id
                var form_data = {cn_id}

                 $.ajax({
                    type: 'GET',
                    url: "",
                    data: form_data,
                    success: function (response) {
                        update_prices(response);
                        create_linegraph(response)
                        let name = $(".js-typeahead-names").eq(0).val();
                         let win_title = 'New World Market Prices' + cn_id
                        let new_url = '';
                        window.history.pushState('data', win_title, new_url);
                        gtag('event', 'search-input', {'term': name});
                        $.getScript("https://www.googletagmanager.com/gtag/js?id=G-WW3EJQVND0",function(){});
                    },

                    error: function (response) {
                        console.log(response)
                    }
                })

            },
            onSubmit: function (node, form, item, event) {
                event.preventDefault();
                var cn_id = item.id
                var form_data = {cn_id}

                $.ajax({
                    type: 'GET',
                    url: "",
                    data: form_data,
                    success: function (response) {
                        update_prices(response);
                        create_linegraph(response)
                        let name = $(".js-typeahead-names").eq(0).val();

                        gtag('event', 'search-input', {'term': name});
                        $.getScript("https://www.googletagmanager.com/gtag/js?id=G-WW3EJQVND0",function(){});
                    },

                    error: function (response) {
                        console.log(response)
                    }
                })
            }

        }
    })
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
        document.getElementById("price-data").classList.remove("hidden");
        document.getElementById("welcome-banner").classList.add("hidden");
        const elem = document.getElementById("lowest-price-data");
        elem.innerHTML = data["lowest_price"];
        create_linegraph(data["graph_data"]);
    })
};

const init = () => {
    document.getElementById("price-data").classList.add("hidden");
    document.getElementById("welcome-banner").classList.add("hidden");

    initTypeahead();

    const params = getParamsFromUrl();
    serverId = params && params.server_id || 1;
    changeServer(serverId, true);
    if(params && params.item_id) {
        loadItem(params.item_id, true);
    } else {
        document.getElementById("welcome-banner").classList.remove("hidden");
    }
    document.getElementById("server-name").innerText = servers[serverId];
}

window.addEventListener('load', function() {
    init();
});

window.onpopstate = function(e){
    init();
};
