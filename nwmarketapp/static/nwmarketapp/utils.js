const nwmpRequest = (url, method = "GET", init = null) => {
    init = init || {};
    return fetch(url, {
        ...init,
        method: method
    }).then(async response => {
        const isJson = response.headers.get('content-type')?.includes('application/json');
        const data = isJson ? await response.json() : null;
        if (response.ok) {
            return data;
        } else {
            return Promise.reject(data);
        }
    })
}

let notificationTimeout = null;
const createNotification = (message, level) => {

    if(notificationTimeout) {
        clearTimeout(notificationTimeout);
        notificationTimeout = null;
    }
    // level should be info, success, warning, danger
    const notifications = document.getElementById("notifications");
    notifications.innerHTML = `<div class="notification is-${level} container">
        <button class="delete"></button>
        ${message}
    </div>`;
    notificationTimeout = setTimeout(() => {notifications.innerHTML = "";}, 2500);
    (document.querySelectorAll('.notification .delete') || []).forEach(($delete) => {
        const $notification = $delete.parentNode;

        $delete.addEventListener('click', () => {
            $notification.parentNode.removeChild($notification);
            clearTimeout(notificationTimeout);
            notificationTimeout = null;
        });
    });
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

const setupModal = (triggerId, modalId) => {
    document.getElementById(triggerId).onclick = () => {
        const DataModal = document.getElementById(modalId);
        DataModal.classList.add("is-active");

        if(typeof(selectedItems) !== 'undefined' && selectedItems.length > 0 ){
            populateSelectedItems()
        }
        DataModal.querySelectorAll(".close-modal").forEach((elem) => {

            if(elem.id == 'save_items'){
                elem.onclick = () => {
                    saveTrackedItems()
                    DataModal.classList.remove("is-active");
                }
            }else {
                elem.onclick = () => {
                    DataModal.classList.remove("is-active");
                }
            }
        });
    }
}
