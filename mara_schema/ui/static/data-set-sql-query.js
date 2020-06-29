var DataSetSqlQuery = function (baseUrl) {

    function localStorageKey(param) {
        return 'mara-schem-sql-query-param-' + param;
    }

    $('.param-checkbox').each(function (n, checkbox) {
        var storedValue = localStorage.getItem(localStorageKey(checkbox.value));
        if (storedValue == 'false') {
            checkbox.checked = false;
        } else if (storedValue == 'true') {
            checkbox.checked = true;
        } else {
            checkbox.checked = checkbox.value != 'star schema';
        }
    });

    function updateUI() {
        var selectedParams = [];
        $('.param-checkbox').each(function (n, checkbox) {
            if (checkbox.checked) {
                selectedParams.push(checkbox.value);
            }
            localStorage.setItem(localStorageKey(checkbox.value), checkbox.checked);
        });

        var url = baseUrl;
        if (selectedParams.length > 0) {
            url += '/' + selectedParams.join('/')
        }
        loadContentAsynchronously('sql-container', url);
    }

    $('.param-checkbox').change(updateUI);

    updateUI();
};
