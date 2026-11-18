# /schemas/internal_knowledge/domain/code_relation_type.py
"""代码仓库专属关系"""
from enum import Enum

from schemas.base import DocumentedEnum

class CodeRelationType(DocumentedEnum):
    """代码仓库专属关系

    设计规范:
        1. 统一采用主动语态定义有向边 (Source -> Relation -> Target)，如 SubClass -> INHERITS -> BaseClass。
        2. 优先提取高频核心关系 (DEFINES, CALLS, IMPORTS, INHERITS, IMPLEMENTS, OVERRIDES)，数据流关系按需开启。
    """

    # 结构与包含
    CONTAINS = ("contains", "结构与包含", "目录包含文件，或文件包含类/函数")
    DEFINES = ("defines", "结构与包含", "作用域定义了变量、函数或类")
    DECLARES = ("declares", "结构与包含", "接口或头文件声明了方法/变量")
    BELONGS_TO = ("belongs_to", "结构与包含", "成员归属于类、模块或包")

    # 调用与执行流
    CALLS = ("calls", "调用与执行流", "函数/方法调用另一个函数/方法")
    INSTANTIATES = ("instantiates", "调用与执行流", "实例化类 (new / Class())")
    THROWS = ("throws", "调用与执行流", "抛出异常")
    CATCHES = ("catches", "调用与执行流", "捕获异常")
    DECORATES = ("decorates", "调用与执行流", "装饰器或注解修饰函数/类")

    # 依赖与引用
    IMPORTS = ("imports", "依赖与引用", "导入模块或符号")
    REFERENCES = ("references", "依赖与引用", "引用常量、全局变量或属性")
    DEPENDS_ON = ("depends_on", "依赖与引用", "包、服务或组件级宏观依赖")

    # 面向对象与多态
    INHERITS = ("inherits", "面向对象与多态", "继承父类 (extends)")
    IMPLEMENTS = ("implements", "面向对象与多态", "实现接口或抽象类 (implements)")
    OVERRIDES = ("overrides", "面向对象与多态", "重写父类方法")
    MIXES_IN = ("mixes_in", "面向对象与多态", "混入特征 (Mixin / Trait)")

    # 类型与数据流
    RETURNS = ("returns", "类型与数据流", "返回某种类型")
    ACCEPTS = ("accepts", "类型与数据流", "接收某种类型的参数")
    READS = ("reads", "类型与数据流", "读取变量或字段的值")
    WRITES = ("writes", "类型与数据流", "修改或赋值变量/字段")
    TYPE_OF = ("type_of", "类型与数据流", "变量或字段的数据类型")

    # 测试与工程元数据
    TESTS = ("tests", "测试与工程元数据", "测试用例验证目标代码")
    DOCUMENTS = ("documents", "测试与工程元数据", "文档或注释说明代码模块")
    CONFIGURES = ("configures", "测试与工程元数据", "配置文件作用于特定模块")
