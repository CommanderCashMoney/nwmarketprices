window.dataLayer = window.dataLayer || [];
function gtag(){
    dataLayer.push(arguments);
}
gtag('js', new Date());
gtag('config', 'G-WW3EJQVND0');

const getParamsFromUrl = () => {
    // convert this to something more elegant as needed
    const loc = window.location;
    if(!loc.pathname) {
        return;
    }
    const parts = loc.pathname.split("/");
    let item_id = parts.pop() || parts.pop();
    if(!item_id) {
        return null;
    } else if (item_id == "#") {
        item_id = parts.pop();
    }

    return {
        "item_id": item_id,
        "server_id": parts.pop()
    }
}

const nwdbConfig = {
    scale: 0.80,
    delay: 5
};

function link_submit(cn) {
    $.ajax({
        type: 'GET',
        url: `/api/${cn}/${server_id}`,
        success: function (response) {
            update_prices(response);
            createLinegraph(response);
            const name = response.item_name;
            $(".js-typeahead-names").val(name)

            window.scrollTo(0,0)
            let win_title = 'New World Market Prices' + cn
            let new_url = `/${cn}/${server_id}`;
            window.history.pushState('data', win_title, new_url);
            gtag('event', 'link-search', {'term': name});
            $.getScript("https://www.googletagmanager.com/gtag/js?id=G-WW3EJQVND0",function(){});
            document.getElementById("item-info").classList.remove("hidden");
            document.getElementById("welcome-info").classList.add("hidden");

        },

        error: function (response) {
            console.log(response)
        }
    })
}

document.addEventListener("DOMContentLoaded", () => {
    const params = getParamsFromUrl();
    if(params.item_id) {
        link_submit(params.item_id);
    }
});

function change_server(server_id){
    // todo: fully ajax
    const urlParams = getParamsFromUrl();
    if(!urlParams) {
        window.location.assign(`/1223/${server_id}`);
    } else {
        window.location.assign(`/${urlParams.item_id}/${server_id}`);
    }
    server_id = server_id;
}
