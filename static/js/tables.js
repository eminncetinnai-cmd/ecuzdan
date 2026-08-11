/**
 * E-CÜZDAN v15.0 - Tables JavaScript
 * DataTables initialization and helper functions
 */

// Default DataTable Options
export const DEFAULT_DATATABLE_OPTIONS = {
    language: {
        url: '//cdn.datatables.net/plug-ins/1.13.4/i18n/tr.json'
    },
    pageLength: 10,
    lengthMenu: [10, 25, 50, 100],
    order: [[0, 'desc']],
    responsive: true,
    columnDefs: [
        { orderable: false, targets: -1 } // Last column not sortable
    ],
    dom: '<"flex justify-between items-center mb-4"lf>rt<"flex justify-between items-center mt-4"ip>'
};

// Initialize DataTable
export function initDataTable(tableId, options = {}) {
    const table = $(`#${tableId}`);
    if (table.length) {
        return table.DataTable({
            ...DEFAULT_DATATABLE_OPTIONS,
            ...options
        });
    }
    return null;
}

// Initialize Multiple DataTables
export function initDataTables(tableIds, options = {}) {
    const tables = {};
    tableIds.forEach(id => {
        tables[id] = initDataTable(id, options[id] || options);
    });
    return tables;
}

// Destroy DataTable
export function destroyDataTable(tableId) {
    const table = $(`#${tableId}`);
    if (table.length && table.DataTable().length) {
        table.DataTable().destroy();
    }
}

// Reload DataTable
export function reloadDataTable(tableId) {
    const table = $(`#${tableId}`);
    if (table.length && table.DataTable().length) {
        table.DataTable().ajax.reload();
    }
}

// Add Row to DataTable
export function addRowToDataTable(tableId, data) {
    const table = $(`#${tableId}`);
    if (table.length && table.DataTable().length) {
        table.DataTable().row.add(data).draw();
    }
}

// Update Row in DataTable
export function updateRowInDataTable(tableId, rowIndex, data) {
    const table = $(`#${tableId}`);
    if (table.length && table.DataTable().length) {
        table.DataTable().row(rowIndex).data(data).draw();
    }
}

// Delete Row from DataTable
export function deleteRowFromDataTable(tableId, rowIndex) {
    const table = $(`#${tableId}`);
    if (table.length && table.DataTable().length) {
        table.DataTable().row(rowIndex).remove().draw();
    }
}

// Search DataTable
export function searchDataTable(tableId, searchTerm) {
    const table = $(`#${tableId}`);
    if (table.length && table.DataTable().length) {
        table.DataTable().search(searchTerm).draw();
    }
}

// Filter DataTable by Column
export function filterDataTableByColumn(tableId, columnIndex, value) {
    const table = $(`#${tableId}`);
    if (table.length && table.DataTable().length) {
        table.DataTable().column(columnIndex).search(value).draw();
    }
}

// Get Selected Rows
export function getSelectedRows(tableId) {
    const table = $(`#${tableId}`);
    if (table.length && table.DataTable().length) {
        return table.DataTable().rows('.selected').data().toArray();
    }
    return [];
}

// Select Row
export function selectRow(tableId, rowIndex) {
    const table = $(`#${tableId}`);
    if (table.length && table.DataTable().length) {
        table.DataTable().row(rowIndex).select();
    }
}

// Deselect All Rows
export function deselectAllRows(tableId) {
    const table = $(`#${tableId}`);
    if (table.length && table.DataTable().length) {
        table.DataTable().rows().deselect();
    }
}

// Export for global access
window.ECuzdanTables = {
    DEFAULT_DATATABLE_OPTIONS,
    initDataTable,
    initDataTables,
    destroyDataTable,
    reloadDataTable,
    addRowToDataTable,
    updateRowInDataTable,
    deleteRowFromDataTable,
    searchDataTable,
    filterDataTableByColumn,
    getSelectedRows,
    selectRow,
    deselectAllRows
};
