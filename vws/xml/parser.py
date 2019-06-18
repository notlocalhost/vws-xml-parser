import xml.sax as sax
from multiprocessing import Process, Pipe

from xml.sax import ContentHandler, ErrorHandler


class NoneElement:
    """
    Класс не существующего элемента.
    """

    def __call__(self, separator: str = None) -> None or str or list:
        """
        Получение текстового содержания, всегда None.
        :return: None
        :param separator: Разделитель
        """
        return None

    def __getattribute__(self, name):
        """
        Обращение к дочернему элементу, возвращает пустой элемент.
        :param name: Имя дочернего элемента
        :return: self
        """
        return self

    def __getitem__(self, name):
        """
        Обращение к атрибуту элемента, возвращает None.
        :param name: Имя атрибута
        :return: None
        """
        return None

    def __iter__(self):
        """
        Элемент итерируемый, но пустой.
        :return: self
        """
        return self

    def __next__(self):
        """
        Прерывание цикла.
        """
        raise StopIteration()

    def __bool__(self):
        """
        Проверка на существование элемента, всегда False.
        :return: False
        """
        return False

    def __contains__(self, item):
        """
        Проверка вхождения, всегда False.
        :param item: Дочерний элемент
        :return: False
        """
        return False

    def __eq__(self, other):
        """
        Сравление элемента с чем-либо, всегда False.
        :param other: Другой объект
        :return: False
        """
        return False


class Element:
    """
    Класс XML-элемента, именно объекты этого класса будут создаваться при парсинге XML-файла.
    """

    NONE = NoneElement()

    def __init__(self, parser, name: str, parent=None):
        """
        Инициализация элемента.
        :param parser: Ссылка на парсер
        :param name: Имя элемента
        :param parent: Родительский элемент
        """
        self.__parser = parser
        self.__name = name
        self.__attrs = {}
        self.__text = None
        self.__childs = {}
        self.__parent = parent
        self.__iterate = False
        self.__each = None
        self.__n_a_m_e = name.replace(':', '_').replace('-', '_')

    def __call__(self, separator: str = None) -> None or str or list:
        """
        Возвращает тектстовое содержимое элемента. Если элемент не содержит текста - возвращает None. Если содержит
        текст - возвращает строку или массив строк, в случае, если текстовое содержимое разбито другими элементами.
        Если указан разделитель, то вместо массива будет возвращена одна строка с содержимым массива разделенных данной
        строкой.
        :param separator: Разделитель
        :return: None or str or list
        """
        if self.__text is None:
            return None
        if not(separator is None) and isinstance(self.__text, list):
            return separator.join(self.__text)
        return self.__text

    def __getattribute__(self, name):
        """
        Обращение к дочернему элементу. В случае, если элемент содержит двоеточие или тире, эти символы будут заменены
        символ подчеркивания чтобы можно было обратится к ним, либо использовать функцию Element.child. Если дочернего
        элемента с таким именем нет - возвращает пустой элемент (Element.NONE).
        :param name: Имя элемента
        :return: Element or NoneElement
        """
        if name[0] == '_':
            return object.__getattribute__(self, name)
        for child in self.__childs.values():
            if name == child.__n_a_m_e:
                return child
        return Element.NONE

    def __getitem__(self, name):
        """
        Получение значения атрибута элемента. Если атрибут отсутствует возвращает None.
        :param name: Имя атрибута
        :return: str or None
        """
        return self.__attrs.get(name)

    def __iter__(self):
        """
        Итерируемый элемент, организаци цикла по данным элементам.
        :return: Self
        """
        self.__iterate = self.__parser.breakpoint == self
        return self

    def __next__(self):
        """
        Переход к следующему такомуже элементу, если следующий элемент не такой как этот, цикп прерывается.
        :return: self
        """
        if self.__parser.finished:
            return False
        if self.__iterate:
            self.__iterate = False
            return self
        if self.__parser.breakpoint != self:
            raise StopIteration()
        self.__parser.next()
        return self

    def __bool__(self):
        """
        Проверка на существование элемента.
        :return: True
        """
        return True

    def __contains__(self, element):
        """
        Проверка входждения елемента. Возвращает правду в случае если этот элемент является заданным или дочерним от
        заданного.
        :param element: Проверяемый элемент
        :return: bool
        """
        e = self
        while e != element:
            e = e.__parent
            if e is None:
                return False
        return True

    def child(self, name_or_path):
        """
        Возвращает дочерний элемент.
        :param name_or_path: Имя элемента или путь от текущего элемента
        :return: Element or NoneElement
        """
        if isinstance(self, NoneElement):
            return NoneElement
        if isinstance(name_or_path, str):
            return self.__childs.get(name_or_path, Element.NONE)
        else:
            current = self
            for name in name_or_path:
                current = current.__childs.get(name)
                if current is None:
                    return Element.NONE
            return current

    def clear(self):
        """
        Очистка данных элемента и удаление дочерних элементов.
        """
        self.__attrs.clear()
        self.__childs.clear()
        self.__text = None

    def name(self):
        """
        Возвращает имя элемента.
        :return: None or str
        """
        if isinstance(self, NoneElement):
            return None
        return self.__name

    def path(self):
        """
        Возвращаеи путь элемента.
        :return: None or str
        """
        if isinstance(self, NoneElement):
            return None
        path = f'/{self.__name}'
        parent = self.__parent
        while not(parent is None):
            path = f'/{parent.__name}{path}'
            parent = parent.__parent
        return path

    def parent(self):
        """
        Возвращает родительски элемент.
        :return: Element
        """
        if isinstance(self, NoneElement):
            return None
        return self.__parent

    def setAttributes(self, attrs: {}):
        """
        Установка атрибутов элемента. Используется парсером.
        :param attrs: Словарь атрибутов
        """
        if isinstance(self, NoneElement):
            return
        self.__attrs = attrs

    def setChilds(self, childs: {}):
        """
        Установка дочерних элементов. Используется парсером.
        :param childs: Словарь дочерних элементов
        """
        if isinstance(self, NoneElement):
            return
        self.__childs = childs

    def setText(self, text):
        """
        Установка текстового содержания элемента. Используется парсером.
        :param text: None or str or list of str
        """
        if isinstance(self, NoneElement):
            return
        self.__text = text

    def each(self, *args):
        """
        Функция для долучения и установки переменной each. Используется для цикла "пока".
        """
        if not args:
            return self.__each
        else:
            self.__each = args[0]


class OnError(ErrorHandler):
    """
    Обработчик искоючений.
    """

    def __init__(self, handler):
        self.handler = handler
        self.excepted = False

    def sendError(self, level, exception):
        if self.excepted:
            return
        self.excepted = True
        self.handler.io.send([Handler.ERROR, level, type(exception), str(exception)])

    def error(self, exception):
        self.sendError('ERROR', exception)

    def fatalError(self, exception):
        self.sendError('FATAL', exception)

    def warning(self, exception):
        self.sendError('WARNING', exception)


class Finish(Exception):
    """
    Исключение для завершения обработчиком парсинга документа.
    """
    pass


class Handler(ContentHandler):
    """
    Обработчик контента XML-документа.
    """

    PARSE = 1   # Начать/продолжить парсинг
    FINISH = 2  # Команда на завершение парсинга
    DATA = 3    # Передача данных парсеру
    ERROR = 4   # Передача информации об ошибке

    def __init__(self, io):
        """
        Инициализация обработчика.
        :param io: Пайп для общения с парсером.
        """
        super().__init__()
        self.io = io
        self.path = []
        self.stack = []
        self.data = None
        self.element = None
        self.min = None

    @staticmethod
    def create(source, pipe):
        """
        Создание обработчика.
        :param source: Источник данныйх
        :param pipe: Пайп для общения между обработчиком и парсером
        """
        handler = Handler(pipe)
        handler.service()
        try:
            sax.parse(source, handler, OnError(handler))
        except Finish:
            pass
        except Exception as e:
            handler.io.send([Handler.ERROR, 'ERROR', type(e), str(e)])

    @staticmethod
    def clearAttributes(element):
        """
        Чистка атрибутов элемента и атрибутов дочерних элементов.
        :param element: list
        """
        element[1] = None
        for n in element[3]:
            Handler.clearAttributes(n)

    def characters(self, content: str):
        """
        Вызывается при получении текстового содержания элемента. Игнорируются пустые строки, если текст поплняется,
        создается массив из строк.
        :param content: Текст
        :return:
        """
        content = content.strip()
        if content != '':
            if self.element[2] is None:
                self.element[2] = content
            elif isinstance(self.element[2], str):
                self.element[2] = [self.element[2], content]
            else:
                self.element[2].append(content)

    def startElement(self, name, attrs):
        """
        Вызываетс при встрече нового элемента документа.
        :param name: Имя элемента
        :param attrs: Его атрибуты
        """
        self.path.append(name)
        attrs = {name: value for name, value in attrs.items()}
        element = [name, attrs, None, []]
        if self.element is None:
            self.data = element
            self.min = element
        else:
            exists = False
            for child in self.element[3]:
                if child[0] == name:
                    i = self.stack.index(self.min)
                    path = [e[0] for e in self.stack[:i + 1]]
                    self.io.send([Handler.DATA, self.min, path[1:], self.path[1:]])
                    self.service()
                    Handler.clearAttributes(self.min)
                    self.min = element
                    self.element[3] = [element]
                    for i, e in enumerate(self.element[3]):
                        if e[0] == name:
                            self.element[3][i] = element
                            break
                    exists = True
                    break
            if not exists:
                self.element[3].append(element)
        self.element = element
        self.stack.append(element)

    def endElement(self, name):
        """
        Вызывается при закрытии элемента документа.
        :param name:
        """
        self.path.pop()
        element = self.stack.pop()
        self.element = self.stack[-1] if self.stack else None
        if element == self.min:
            self.min = self.element
        if not self.path:
            self.io.send([Handler.DATA, self.data, None, None])

    def service(self):
        """
        Обработка команд от парсера.
        """
        while True:
            o = self.io.recv()
            if o == Handler.PARSE:
                return
            if o == Handler.FINISH:
                raise Finish()


class While:
    """
    Класс для реализации цикла, пока парсинг идет по элементу или по его дочерних элементах.
    """

    def __init__(self, parser, points):
        self.parser = parser
        self.points = points

    def __contains__(self, element):
        if self.parser.finished:
            return False
        if not element:
            return False
        each = Element.each(element)
        if each is None:
            Element.each(element, 1 if element in self.points[0] else 2)
            return True
        if each == 1:
            if element in self.points[0]:
                self.parser.next()
                return True
            if element in self.points[1]:
                Element.each(element, None)
                Element.setChilds(element, {})
                return False
        elif each == 2:
            Element.each(element, None)
            return False


class Parser:
    """
    Класс отвечающий за навигацию при парсинге XML-документа.
    """

    def __init__(self, source):
        """
        Конструктор класса.
        :param source: Источник XML-документа
        """
        self.__io, io = Pipe()
        self.__handler = Process(target=Handler.create, args=(source, io))
        self.__handler.start()
        self.__root: Element or None = None
        self.__points = [None, None]
        self.__each = None
        self.__finished = False

    def __contains__(self, element):
        """
        Реализация цикла, пока парсинг идет по элементу или по его дочерних элементах.
        """
        if self.__each is None:
            self.__each = While(self, self.__points)
        return element in self.__each

    @property
    def breakpoint(self) -> Element or NoneElement:
        """
        Возвращает элемент на котором произошла точка останова парсинга. Возвратит пустой элемент, если пропарсен
        полностью весь документ.
        :return: Элемент тоочки
        """
        return self.__points[0]

    def finish(self):
        """
        Комманда для завершения парсинга.
        """
        if self.__handler.is_alive():
            self.__finished = True
            self.__io.send(Handler.FINISH)
            self.__handler.join()

    @property
    def finished(self) -> bool:
        """
        Проверка, завершен ли парсинг.
        :return: bool
        """
        return self.__finished

    @property
    def root(self) -> Element:
        """
        Возвращает корневой элемент документа. Вызов метода обязателен.
        :return: Корневой элемент
        """
        self.next()
        return self.__root

    def next(self):
        """
        Команда для продолжения парсинга до следующей точки останова.
        """
        if self.__finished:
            return
        self.__io.send(Handler.PARSE)
        self.__service()

    def __update(self, data, parent: Element = None) -> Element:
        """
        Обновление дерева элементов в зависимости от данных переданных обработчиком документа.
        :param data: Объекс с данными
        :param parent: Родительский элемент
        :return: Созданный элемент
        """
        if parent is None:
            if self.__root is None:
                element = Element(self, data[0])
                self.__root = element
            else:
                element = self.__root
        else:
            element = Element.child(parent, data[0])
            if not element:
                element = Element(self, data[0], parent)
        if not(data[1] is None):
            Element.setAttributes(element, data[1])
        Element.setText(element, data[2])
        Element.setChilds(element, {child[0]: self.__update(child, element) for child in data[3]})
        return element

    def __service(self):
        """
        Обработчик сообщений от обработчика документа.
        """
        while True:
            o = self.__io.recv()

            # От обработчика пришли данные о структуре документа (с возможным завершением)
            if o[0] == Handler.DATA:
                if self.__root is None:
                    self.__update(o[1])
                else:
                    element: Element = self.__root if o[2] is None else Element.child(self.__root, o[2])
                    self.__update(o[1], Element.parent(element))
                self.__points[1] = self.__points[0]
                self.__points[0] = Element.NONE if o[3] is None else Element.child(self.__root, o[3])
                if self.__points[0] is None:
                    self.__handler.join()
                return

            # От обработчика пришла ошибка
            if o[0] == Handler.ERROR:
                self.__handler.join()
                raise Exception(o[1:])

