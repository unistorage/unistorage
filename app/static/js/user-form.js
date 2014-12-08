(function() {
    
    var removeButton = $('<a></a>', {
        class: 'btn btn-danger  remove',
        html: '<i class="icon-remove icon-white"></i>'
    });

    function addDomainField(index) {
      var name = 'domains-' + index;
      var input = $('<input>', {
          id: name,
          name: name,
          type: 'text'
      });

      var li = $('<li></li>', {
          class: 'control-group'
      });
      li.append(input).append(removeButton.clone());
      $('#domains').find('ul').append(li);
    } 

    function getLastDomainIndex(index) {
        var id = $('#domains').find('li:last>input');
        return id.length ? parseInt(id.attr('id').split('-')[1]) : 0;
    } 

    $(function() {
        $('#domains a#add-domain').click(function() {
            var index = getLastDomainIndex();
            addDomainField(index + 1);
        });

        $('#domains ul li').each(function(idx, li) {
            $(li).append(removeButton.clone());
        });

        $('#domains ul').on('click', 'a.remove', function() {
            $(this).parent().remove();
        });

        $('select[name=has_access_to]').chosen({
            placeholder_text_multiple: 'Выберите пользователей'    
        });

        $('#s3').change(function() {
          if (!$('#s3')[0].checked) {
            $('#aws_credentials').hide()
          } else {
            $('#aws_credentials').show()
          }
        }).change();
    });

})();
