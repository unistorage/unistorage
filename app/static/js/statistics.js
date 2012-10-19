$(function () {
    $('select[name=type_id]').chosen({
        allow_single_deselect: true,
        placeholder_text_single: 'Не указан'
    });
});


function drawVisualization(plot, data) {
    google.setOnLoadCallback(function() {
        new google.visualization.ColumnChart(plot).draw(data, {
            hAxis: {title: 'Дата'},
            vAxes: [{'format': '# МБ'}, {'format': '#'}],
            series:{
                0: {targetAxisIndex:0},
                1: {targetAxisIndex:1}
            }
        });
    });
}