let selectedItems = [];
const initTypeahead = (data) => {
    $.typeahead({
        input: '.item-search',
        display: "name",

        source: {data: data},
        callback: {
            onInit: function (node) {
                console.log('Typeahead Initiated on ' + node.selector);
            },
            onClickAfter: function(node, a, item, event){
                selectItem(item.id, item.name);

            },
            onSubmit: function (node, form, item, event) {
                selectItem(item.id, item.name);
            },

        }
    })
}

$('.typeahead').bind('typeahead:render', function(ev, suggestion) {
  console.log('Selection: ' + suggestion);
});



const selectItem = (item_id, item_name) => {

    selectedItems.push({'itemId': item_id, 'itemName':item_name})
    populateSelectedItems()
    document.getElementById('item-search').value=''

};

const removeItem = (item_id) => {
    for (let i = 0; i < selectedItems.length; i++) {
        let element = selectedItems[i]
        if(element.itemId == parseInt(item_id)){
            selectedItems.splice(i, 1);
        }
    };

    populateSelectedItems()

};