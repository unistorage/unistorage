$(function () {
    google.setOnLoadCallback(drawVisualization);

    function drawVisualization() {
        new google.visualization.ColumnChart($('#plot').get(0)).draw(statisticsData,
            {
                hAxis: {title: 'Дата'},
                vAxes: [{'format': '# МБ'},{'format': '#'}],
                series:{
                    0: {targetAxisIndex:0},
                    1: {targetAxisIndex:1}
                }
            }
        );
    }

    $('select[name=type_id]').chosen({
        allow_single_deselect: true,
        placeholder_text_single: 'Не указан'
    });
});
