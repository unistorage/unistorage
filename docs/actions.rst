Actions
=======

Операция -- некоторое действие над файлом: изменение размера картинки, конвертация документа в другой формат и так далее.
В системе каждая операция представляет собой модуль, удовлетворяющий следующим условиям:

- Имеет аттрибуты:

  - `name` -- имя операции (``resize``, ``convert``, etc)
  - `applicable_for` -- :term:`семейство типов`, к которым применима операция
  - `result_type_family` -- семейство типов, к которому принадлежит результат операции


- Имеет функции:

  - .. py:function:: validate_and_get_args(args)

        Валидирует словарь, полученный из пользовательского запроса и либо возвращает "очищенный"
        список аргументов (т.н. `cleaned args`), либо бросает :class:`action.utils.ValidationError`.

        :param args: словарь (чаще всего -- ``request.args.to_dict()``)
        :type args: dict

  - .. py:function:: perform(source_file, *cleaned_args)

        :param source_file: исходный файл
        :type source_file: file-like object


Для удобства модули операций сгруппированы в пакеты по полю `applicable_for`.

API
---

.. automodule:: actions
    :members:

.. automodule:: actions.handlers
    :members:

.. automodule:: actions.templates
    :members:
