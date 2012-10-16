$(function () {
    var options = {
        xaxis: {
            mode: 'time',
            timeformat: '%d.%m',
            tickSize: [1, 'day']
        },
        yaxes: [{
            min: 0,
            tickFormatter: function (v) { return v.toFixed(2) + ' МБ'; }
        }, {
            position: 'right'
        }],
        bars: {
            show: true,
            barWidth: 20 * 60 * 60 * 1000,
            align: 'center'
        }
    };

    var data = [{
        data: filesSizeData,
        label: 'Объём файлов',
    }, {
        data: filesCountData,
        label: 'Количество файлов',
        yaxis: 2,
        bars: {
            barWidth: 10 * 60 * 60 * 1000,
        }
    }];

    $.plot($('#plot'), data, options);

    $('select[name=type_id]').chosen({
        allow_single_deselect: true,
        placeholder_text_single: 'Не указан'
    });
});
